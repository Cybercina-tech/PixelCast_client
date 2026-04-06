"""
Deterministic mock responses for USE_MOCK_REGISTRY (local/dev testing without Envato).
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .client import LicenseServerError


def _parse_retry_after(headers: dict | None) -> int:
    if not headers:
        return 60
    ra = headers.get("Retry-After") or headers.get("retry-after") or "60"
    try:
        return max(1, int(ra))
    except (TypeError, ValueError):
        return 60


def mock_post_license_validation(
    license_server_url: str,
    payload: Dict[str, Any] | None,
    auth_bearer: str,
) -> Tuple[bool, Dict[str, Any]]:
    purchase = ((payload or {}).get("purchase_code") or "").strip().lower()
    bearer = (auth_bearer or "").strip()

    if "mock-429" in purchase or bearer.endswith("-mock429"):
        raise LicenseServerError(
            "Mock: rate limited",
            status_code=429,
            retry_after=42,
        )
    if "mock-404" in purchase:
        return False, {"valid": False, "status": "invalid", "message": "Mock: purchase not found"}
    if "mock-invalid" in purchase:
        return False, {"valid": False, "status": "invalid", "message": "Mock: invalid license"}

    if bearer:
        return True, {
            "valid": True,
            "status": "active",
            "plan_type": "saas",
            "features": {"max_screens": 99, "crypto_widgets": True, "video_support": True},
            "domain": (payload or {}).get("domain") or "",
        }

    return True, {
        "valid": True,
        "status": "active",
        "plan_type": "basic",
        "features": {"max_screens": 5, "crypto_widgets": False, "video_support": False},
        "domain": (payload or {}).get("domain") or "",
    }


def mock_post_gateway_activate(base_url: str, body: dict) -> dict:
    code = ((body or {}).get("purchase_code") or "").strip().lower()
    if "mock-429" in code:
        raise LicenseServerError("Mock: activation rate limited", status_code=429, retry_after=30)
    if "mock-fail" in code:
        raise LicenseServerError("Mock: activation failed", status_code=400)

    return {
        "activation_token": f"mock-bearer-{code[:8] or 'default'}",
        "valid": True,
        "status": "active",
        "plan_type": "saas",
        "features": {"max_screens": 10, "crypto_widgets": True, "video_support": False},
        "message": "Mock activation OK",
    }
