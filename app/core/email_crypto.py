"""
Fernet helpers for system SMTP password at rest (same key as notification channels).
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


def _fernet_key_bytes() -> bytes:
    key = getattr(settings, 'NOTIFICATION_ENCRYPTION_KEY', None) or ''
    if isinstance(key, str):
        key = key.encode('utf-8')
    if not key:
        raise ValueError(
            'NOTIFICATION_ENCRYPTION_KEY must be set to store SMTP passwords securely.'
        )
    return key


def get_fernet() -> 'Fernet':
    if Fernet is None:
        raise ImportError('cryptography is required for encrypted SMTP password storage')
    return Fernet(_fernet_key_bytes())


def encrypt_secret(plain: str) -> str:
    if plain is None or plain == '':
        return ''
    f = get_fernet()
    return f.encrypt(plain.encode('utf-8')).decode('ascii')


def decrypt_secret(token: str) -> str:
    if not token:
        return ''
    try:
        f = get_fernet()
        return f.decrypt(token.encode('ascii')).decode('utf-8')
    except Exception as e:
        logger.error('Failed to decrypt system email secret: %s', e)
        return ''
