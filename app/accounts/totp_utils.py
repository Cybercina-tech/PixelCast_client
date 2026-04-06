"""TOTP 2FA helpers (pyotp)."""

from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any

import pyotp

BACKUP_CODE_COUNT = 8


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_otpauth_uri(secret: str, email: str, issuer: str = 'PixelCast') -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    code = ''.join(code.split())
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception:
        return False


def generate_backup_codes_plain() -> list[str]:
    return [secrets.token_hex(4) for _ in range(BACKUP_CODE_COUNT)]


def hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode('utf-8')).hexdigest()


def hash_backup_codes_list(codes: list[str]) -> str:
    hashed = [hash_backup_code(c) for c in codes]
    return json.dumps(hashed)


def verify_backup_code(user_codes_json: str, code: str) -> tuple[bool, list[str]]:
    """
    If code matches a hashed entry, remove it and return updated list JSON.
    Returns (ok, new_json_or_original_if_fail).
    """
    if not user_codes_json or not code:
        return False, user_codes_json
    try:
        stored: list[str] = json.loads(user_codes_json)
    except json.JSONDecodeError:
        return False, user_codes_json
    h = hash_backup_code(code)
    if h not in stored:
        return False, user_codes_json
    stored = [x for x in stored if x != h]
    return True, json.dumps(stored)
