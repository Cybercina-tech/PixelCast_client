"""Encrypt API keys using the same Fernet material as notifications.EncryptedJSONField."""

from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


def _fernet() -> Fernet | None:
    raw = getattr(settings, "NOTIFICATION_ENCRYPTION_KEY", None)
    if not raw:
        logger.warning("mother_client: NOTIFICATION_ENCRYPTION_KEY is not set; cannot encrypt credentials")
        return None
    key = raw.encode("utf-8") if isinstance(raw, str) else raw
    try:
        return Fernet(key)
    except Exception as exc:
        logger.error("mother_client: invalid NOTIFICATION_ENCRYPTION_KEY: %s", exc)
        return None


def encrypt_api_key(plain: str) -> str:
    f = _fernet()
    if not f:
        raise RuntimeError("NOTIFICATION_ENCRYPTION_KEY is required to store mother gateway API key")
    return f.encrypt((plain or "").encode("utf-8")).decode("ascii")


def decrypt_api_key(stored: str) -> str:
    if not stored:
        return ""
    f = _fernet()
    if not f:
        raise RuntimeError("NOTIFICATION_ENCRYPTION_KEY is required to read mother gateway API key")
    try:
        return f.decrypt(stored.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        logger.error("mother_client: failed to decrypt API key: %s", exc)
        raise
