"""List/revoke JWT refresh sessions using token_blacklist OutstandingToken."""

from __future__ import annotations

import base64
import json
import logging
from collections import defaultdict
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

User = get_user_model()


def _decode_jwt_payload_unverified(token: str) -> dict[str, Any]:
    """Return payload dict from JWT without verification (display only)."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        raw = base64.urlsafe_b64decode(payload_b64.encode('ascii'))
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return {}


def _is_blacklisted_outstanding(outstanding_id: int) -> bool:
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

    return BlacklistedToken.objects.filter(token_id=outstanding_id).exists()


def list_refresh_sessions_for_user(user: User, current_access_token: str | None) -> list[dict[str, Any]]:
    """
    Build session rows from OutstandingToken rows for this user.
    current_access_token: optional Bearer access JWT to mark `current` by matching `sid` claim.
    """
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    current_sid = None
    if current_access_token:
        payload = _decode_jwt_payload_unverified(current_access_token.replace('Bearer ', '').strip())
        current_sid = payload.get('sid')

    out: list[dict[str, Any]] = []
    now = timezone.now()
    qs = OutstandingToken.objects.filter(user=user, expires_at__gt=now).order_by('-created_at')

    outstanding_ids = list(qs.values_list('id', flat=True))
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

    blacklisted_ids = set(
        BlacklistedToken.objects.filter(token_id__in=outstanding_ids).values_list('token_id', flat=True)
    )

    for ot in qs:
        if ot.id in blacklisted_ids:
            continue
        payload = _decode_jwt_payload_unverified(ot.token)
        sid = payload.get('sid')
        jti = payload.get('jti')
        out.append(
            {
                'id': str(ot.id),
                'jti': jti,
                'sid': sid,
                'device': (payload.get('client_ua') or 'Unknown')[:200],
                'ip_address': (payload.get('client_ip') or '—')[:64],
                'last_activity': ot.created_at.isoformat() if ot.created_at else None,
                'expires_at': ot.expires_at.isoformat() if ot.expires_at else None,
                'current': bool(current_sid and sid and current_sid == sid),
            }
        )
    return out


def active_session_stats_by_tenant() -> dict[str, dict[str, int]]:
    """
    Return tenant-level active session stats using non-blacklisted, unexpired refresh tokens.

    Shape:
    {
      "<tenant_id>": {"active_session_count": 12, "active_user_count": 5},
      ...
    }
    """
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    now = timezone.now()
    qs = OutstandingToken.objects.filter(
        expires_at__gt=now,
        user__tenant__isnull=False,
    ).values_list('id', 'user_id', 'user__tenant_id')

    token_rows = list(qs)
    if not token_rows:
        return {}

    token_ids = [row[0] for row in token_rows]
    blacklisted_ids = set(
        BlacklistedToken.objects.filter(token_id__in=token_ids).values_list('token_id', flat=True)
    )

    session_count_by_tenant: dict[str, int] = defaultdict(int)
    users_by_tenant: dict[str, set[int]] = defaultdict(set)

    for token_id, user_id, tenant_id in token_rows:
        if token_id in blacklisted_ids or tenant_id is None:
            continue
        tenant_key = str(tenant_id)
        session_count_by_tenant[tenant_key] += 1
        users_by_tenant[tenant_key].add(int(user_id))

    return {
        tenant_key: {
            'active_session_count': int(session_count_by_tenant.get(tenant_key, 0)),
            'active_user_count': int(len(users_by_tenant.get(tenant_key, set()))),
        }
        for tenant_key in set(session_count_by_tenant.keys()) | set(users_by_tenant.keys())
    }


def blacklist_outstanding_id(user: User, outstanding_id: int) -> bool:
    """Blacklist the refresh token tied to an OutstandingToken row."""
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    try:
        ot = OutstandingToken.objects.get(id=outstanding_id, user=user)
    except OutstandingToken.DoesNotExist:
        return False
    try:
        refresh = RefreshToken(ot.token)
        refresh.blacklist()
        return True
    except TokenError as e:
        logger.warning('blacklist session failed: %s', e)
        return False
    except Exception as e:
        logger.exception('blacklist session error: %s', e)
        return False


def blacklist_all_refresh_for_user(user: User) -> int:
    """Blacklist all outstanding refresh tokens for user. Returns count."""
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    n = 0
    for ot in OutstandingToken.objects.filter(user=user):
        if _is_blacklisted_outstanding(ot.id):
            continue
        try:
            refresh = RefreshToken(ot.token)
            refresh.blacklist()
            n += 1
        except Exception:
            continue
    return n
