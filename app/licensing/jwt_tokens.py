"""
Signed HS256 JWT binding license state to a single host (domain).

The registry activation token stays opaque for upstream Bearer calls; this JWT is
stored separately and verified in LicenseEnforcementMiddleware so copying the DB to
another host cannot satisfy enforcement without re-validation.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _signing_key() -> str:
    explicit = (getattr(settings, "LICENSE_DOMAIN_JWT_SECRET", None) or "").strip()
    if explicit:
        return explicit
    return settings.SECRET_KEY


def normalize_domain(host: str) -> str:
    """Strip port; lowercase; no trailing dot."""
    h = (host or "").strip().lower()
    if ":" in h and not h.startswith("["):
        h = h.split(":", 1)[0]
    return h.rstrip(".")


def issue_domain_binding_jwt(domain: str, plan_type: str) -> str:
    ttl_hours = int(getattr(settings, "LICENSE_DOMAIN_JWT_TTL_HOURS", 24 * 365) or 24 * 365)
    now = timezone.now()
    payload = {
        "dom": normalize_domain(domain),
        "pt": (plan_type or "")[:64],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=max(1, ttl_hours))).timestamp()),
    }
    return jwt.encode(payload, _signing_key(), algorithm="HS256")


def verify_domain_binding_jwt(token: str, request_host: str) -> tuple[bool, str]:
    if not (token or "").strip():
        return False, "missing"
    try:
        payload = jwt.decode(
            (token or "").strip(),
            _signing_key(),
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return False, "expired"
    except jwt.InvalidTokenError:
        return False, "invalid"

    bound = normalize_domain(str(payload.get("dom") or ""))
    current = normalize_domain(request_host)
    if not bound or bound != current:
        return False, "domain_mismatch"
    return True, ""


def refresh_domain_binding_jwt(domain: str, plan_type: str) -> str:
    """Alias for issue (explicit name for callers after revalidation)."""
    return issue_domain_binding_jwt(domain, plan_type)
