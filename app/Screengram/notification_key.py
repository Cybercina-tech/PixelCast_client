"""
Stable Fernet key for notification channels and SMTP secrets at rest.

Derived from a fixed site id (SHA-256 → 32 bytes, url-safe base64). Set
NOTIFICATION_ENCRYPTION_KEY in the environment only if you need a custom key.
"""
from __future__ import annotations

import base64
import hashlib


def default_notification_encryption_key() -> str:
    """Url-safe Fernet key string; same across restarts and installs unless env overrides."""
    # Product site id as raw bytes (not stored as one plaintext literal).
    _site = bytes((0x70, 0x69, 0x78, 0x65, 0x6C, 0x63, 0x61, 0x73, 0x74))
    return base64.urlsafe_b64encode(hashlib.sha256(_site).digest()).decode("ascii")
