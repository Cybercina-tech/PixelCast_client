"""
System-wide email sending using Django mail backends without mutating global settings.

Resolution order:
1. SystemEmailSettings (DB) when delivery_mode is smtp and host is set, or console when requested.
2. Environment variables EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_USE_SSL, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD.
3. Console backend (development default).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Sequence

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

from core.models import SystemEmailSettings

logger = logging.getLogger(__name__)


def _env_str(name: str, default: str = '') -> str:
    return (os.environ.get(name) or '').strip() or default


def _env_bool(name: str, default: bool) -> bool:
    v = _env_str(name, '')
    if not v:
        return default
    return v.lower() in ('1', 'true', 'yes', 'on')


def _env_int(name: str, default: int) -> int:
    v = _env_str(name, '')
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _smtp_params_from_env() -> dict[str, Any]:
    host = _env_str('EMAIL_HOST', '')
    if not host:
        return {}
    return {
        'host': host,
        'port': _env_int('EMAIL_PORT', 587),
        'username': _env_str('EMAIL_HOST_USER', ''),
        'password': _env_str('EMAIL_HOST_PASSWORD', ''),
        'use_tls': _env_bool('EMAIL_USE_TLS', True),
        'use_ssl': _env_bool('EMAIL_USE_SSL', False),
    }


def get_system_email_connection():
    """
    Return a backend instance for system/transactional email (explicit parameters; no global settings mutation).
    """
    solo = SystemEmailSettings.get_solo()

    if solo.delivery_mode == SystemEmailSettings.DELIVERY_CONSOLE:
        return get_connection(
            backend='django.core.mail.backends.console.EmailBackend',
            fail_silently=False,
        )

    if solo.delivery_mode == SystemEmailSettings.DELIVERY_SMTP and (solo.smtp_host or '').strip():
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=solo.smtp_host.strip(),
            port=solo.smtp_port,
            username=(solo.smtp_username or '').strip() or None,
            password=solo.get_smtp_password() or None,
            use_tls=solo.use_tls,
            use_ssl=solo.use_ssl,
            fail_silently=False,
        )

    env_params = _smtp_params_from_env()
    if env_params.get('host'):
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=env_params['host'],
            port=env_params['port'],
            username=env_params['username'] or None,
            password=env_params['password'] or None,
            use_tls=env_params['use_tls'],
            use_ssl=env_params['use_ssl'],
            fail_silently=False,
        )

    # Default: console (matches typical dev settings when nothing is configured)
    logger.debug('No SMTP configuration; using console email backend')
    return get_connection(
        backend='django.core.mail.backends.console.EmailBackend',
        fail_silently=False,
    )


def resolve_default_from_email() -> str:
    solo = SystemEmailSettings.get_solo()
    v = (solo.default_from_email or '').strip()
    if v:
        return v
    return getattr(settings, 'DEFAULT_FROM_EMAIL', '') or 'no-reply@pixelcastsignage.com'


def send_system_email(
    subject: str,
    message: str,
    recipient_list: Sequence[str],
    *,
    from_email: str | None = None,
    fail_silently: bool = False,
    html_message: str | None = None,
) -> int:
    """
    Send a transactional email using the system connection.

    Returns the number of messages sent (Django contract).
    """
    conn = get_system_email_connection()
    from_addr = (from_email or '').strip() or resolve_default_from_email()
    recipients = [r for r in recipient_list if r]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_addr,
        to=recipients,
        connection=conn,
    )
    if html_message:
        msg.attach_alternative(html_message, 'text/html')
    return msg.send(fail_silently=fail_silently)
