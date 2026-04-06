"""Team invitation helpers."""

from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

INVITE_TTL_HOURS = 72


def create_invitation_token() -> str:
    return secrets.token_urlsafe(32)


def default_invite_expiry():
    return timezone.now() + timedelta(hours=INVITE_TTL_HOURS)
