"""Additional auth endpoints: 2FA, password reset, session revoke."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.cache import never_cache

from core.audit import AuditLogger
from core.email_service import send_system_email

from .jwt_sessions import blacklist_outstanding_id
from .models import User
from .security import sanitize_input
from .tokens import ScreenGramRefreshToken
from .totp_utils import (
    build_otpauth_uri,
    generate_backup_codes_plain,
    generate_totp_secret,
    hash_backup_codes_list,
    verify_backup_code,
    verify_totp,
)

logger = logging.getLogger(__name__)

TWOFA_SIGNER = TimestampSigner(salt='pixelcast.auth.2fa')
_PENDING_2FA_CACHE_PREFIX = '2fa_pending_secret:'
_PENDING_2FA_TTL = 600


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''


def issue_login_or_2fa_challenge(user, request):
    """Return DRF Response: either full login payload or 2FA challenge."""
    if getattr(user, 'is_2fa_enabled', False) and (user.totp_secret or '').strip():
        tf = TWOFA_SIGNER.sign(str(user.pk))
        return Response(
            {
                'status': '2fa_required',
                'two_factor_token': tf,
            },
            status=status.HTTP_200_OK,
        )
    return Response(build_login_success_response(user, request), status=status.HTTP_200_OK)


def build_login_success_response(user, request):
    try:
        from saas_platform.tenant_assignment import ensure_user_tenant

        ensure_user_tenant(user)
        user.refresh_from_db()
    except Exception as e:
        logger.warning('ensure_user_tenant in build_login_success_response failed: %s', e)
    ua = request.META.get('HTTP_USER_AGENT', '') or ''
    ip = _client_ip(request)
    refresh = ScreenGramRefreshToken.for_user(user, client_ua=ua, client_ip=ip)
    user.update_last_seen()
    return {
        'status': 'success',
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'role_display': user.get_role_display(),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_2fa_enabled': getattr(user, 'is_2fa_enabled', False),
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
    }


@api_view(['POST'])
@permission_classes([AllowAny])
@never_cache
def login_2fa_view(request):
    """POST /api/auth/login/2fa/ — complete login after password with TOTP or backup code."""
    tf = request.data.get('two_factor_token')
    code = (request.data.get('code') or '').strip()
    if not tf or not code:
        return Response({'error': 'two_factor_token and code are required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        uid = TWOFA_SIGNER.unsign(tf, max_age=600)
    except SignatureExpired:
        return Response({'error': '2FA session expired. Please log in again.'}, status=status.HTTP_400_BAD_REQUEST)
    except BadSignature:
        return Response({'error': 'Invalid 2FA token.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(pk=int(uid), is_active=True).first()
    if not user or not getattr(user, 'is_2fa_enabled', False):
        return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)

    ok = False
    if user.totp_secret and verify_totp(user.totp_secret, code):
        ok = True
    elif user.backup_codes_hash:
        matched, new_json = verify_backup_code(user.backup_codes_hash, code)
        if matched:
            ok = True
            user.backup_codes_hash = new_json
            user.save(update_fields=['backup_codes_hash'])

    if not ok:
        try:
            AuditLogger.log_authentication(action='login_2fa', user=user, success=False, error_message='bad code', request=request)
        except Exception as e:
            logger.error('audit 2fa fail: %s', e)
        return Response({'error': 'Invalid authentication code.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        AuditLogger.log_authentication(action='login_2fa', user=user, success=True, request=request)
    except Exception as e:
        logger.error('audit 2fa ok: %s', e)

    return Response(build_login_success_response(user, request), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@never_cache
def password_reset_request_view(request):
    """POST /api/auth/password-reset/request/ { email }"""
    email = sanitize_input((request.data.get('email') or '').strip().lower())
    generic = {
        'status': 'ok',
        'message': 'If an account exists for that email, password reset instructions have been sent.',
    }
    if not email:
        return Response(generic, status=status.HTTP_200_OK)

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if not user:
        return Response(generic, status=status.HTTP_200_OK)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base = getattr(settings, 'PUBLIC_WEB_APP_URL', 'http://localhost:5173').rstrip('/')
    link = f'{base}/reset-password?uid={uid}&token={token}'

    subject = 'PixelCast — Password reset'
    message = f'''Hello,

We received a request to reset your password. Open this link in your browser (valid for a limited time):

{link}

If you did not request this, you can ignore this email.

— PixelCast Signage
'''
    try:
        send_system_email(subject=subject, message=message, recipient_list=[user.email])
        try:
            AuditLogger.log_action(
                action_type='password_reset_requested',
                user=user,
                resource=user,
                description='Password reset email sent',
                request=request,
            )
        except Exception as e:
            logger.error('audit password reset: %s', e)
    except Exception as e:
        logger.exception('password reset email failed: %s', e)

    return Response(generic, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@never_cache
def password_reset_confirm_view(request):
    """POST /api/auth/password-reset/confirm/ { uid, token, new_password, new_password_confirm }"""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError

    uid = request.data.get('uid')
    token = request.data.get('token')
    pw = request.data.get('new_password') or ''
    pw2 = request.data.get('new_password_confirm') or ''
    if not uid or not token or not pw:
        return Response({'error': 'uid, token, and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if pw != pw2:
        return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        validate_password(pw)
    except DjangoValidationError as e:
        return Response({'error': list(e.messages)[0] if e.messages else 'Invalid password.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(pw)
    user.save(update_fields=['password'])
    try:
        AuditLogger.log_action(
            action_type='password_reset_completed',
            user=user,
            resource=user,
            description='Password reset via email link',
            request=request,
        )
    except Exception as e:
        logger.error('audit pwd reset confirm: %s', e)

    return Response({'status': 'success', 'message': 'Password has been reset. You can log in now.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@never_cache
def twofa_setup_start_view(request):
    """Begin TOTP enrollment; secret stored in cache until confirm."""
    user = request.user
    if getattr(user, 'is_2fa_enabled', False):
        return Response({'error': '2FA is already enabled.'}, status=status.HTTP_400_BAD_REQUEST)

    secret = generate_totp_secret()
    cache.set(f'{_PENDING_2FA_CACHE_PREFIX}{user.id}', secret, _PENDING_2FA_TTL)
    otpauth = build_otpauth_uri(secret, user.email)
    return Response(
        {
            'secret': secret,
            'otpauth_url': otpauth,
            'expires_in_seconds': _PENDING_2FA_TTL,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@never_cache
def twofa_setup_confirm_view(request):
    """Confirm TOTP and enable 2FA."""
    user = request.user
    code = (request.data.get('code') or '').strip()
    if not code:
        return Response({'error': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)

    secret = cache.get(f'{_PENDING_2FA_CACHE_PREFIX}{user.id}')
    if not secret:
        return Response({'error': 'No pending 2FA setup. Start again.'}, status=status.HTTP_400_BAD_REQUEST)

    if not verify_totp(secret, code):
        return Response({'error': 'Invalid code.'}, status=status.HTTP_400_BAD_REQUEST)

    plain_backup = generate_backup_codes_plain()
    user.totp_secret = secret
    user.is_2fa_enabled = True
    user.backup_codes_hash = hash_backup_codes_list(plain_backup)
    user.save(update_fields=['totp_secret', 'is_2fa_enabled', 'backup_codes_hash'])
    cache.delete(f'{_PENDING_2FA_CACHE_PREFIX}{user.id}')

    try:
        AuditLogger.log_action(
            action_type='2fa_enabled',
            user=user,
            resource=user,
            description='TOTP 2FA enabled',
            request=request,
        )
    except Exception as e:
        logger.error('audit 2fa enable: %s', e)

    return Response(
        {
            'status': 'success',
            'backup_codes': plain_backup,
            'message': 'Two-factor authentication is enabled. Store your backup codes safely.',
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@never_cache
def twofa_disable_view(request):
    """Disable 2FA (requires password + TOTP or backup code)."""
    user = request.user
    password = request.data.get('password') or ''
    code = (request.data.get('code') or '').strip()
    if not getattr(user, 'is_2fa_enabled', False):
        return Response({'error': '2FA is not enabled.'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(password):
        return Response({'error': 'Invalid password.'}, status=status.HTTP_400_BAD_REQUEST)

    ok = False
    if user.totp_secret and verify_totp(user.totp_secret, code):
        ok = True
    elif user.backup_codes_hash:
        matched, new_json = verify_backup_code(user.backup_codes_hash, code)
        if matched:
            ok = True
            user.backup_codes_hash = new_json

    if not ok:
        return Response({'error': 'Invalid authenticator or backup code.'}, status=status.HTTP_400_BAD_REQUEST)

    user.totp_secret = ''
    user.is_2fa_enabled = False
    user.backup_codes_hash = ''
    user.save(update_fields=['totp_secret', 'is_2fa_enabled', 'backup_codes_hash'])

    try:
        AuditLogger.log_action(
            action_type='2fa_disabled',
            user=user,
            resource=user,
            description='2FA disabled',
            request=request,
        )
    except Exception as e:
        logger.error('audit 2fa disable: %s', e)

    return Response({'status': 'success', 'message': 'Two-factor authentication has been disabled.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@never_cache
def revoke_session_view(request):
    """POST /api/auth/sessions/revoke/ { outstanding_id }"""
    try:
        oid = int(request.data.get('outstanding_id'))
    except (TypeError, ValueError):
        return Response({'error': 'outstanding_id required'}, status=status.HTTP_400_BAD_REQUEST)

    if blacklist_outstanding_id(request.user, oid):
        return Response({'status': 'success', 'message': 'Session revoked.'}, status=status.HTTP_200_OK)
    return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
