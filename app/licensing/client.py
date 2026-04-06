import logging
from typing import Any, Dict, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LicenseServerError(Exception):
    def __init__(self, message, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


def license_gateway_base_url() -> str:
    """Return operator gateway base (…/api/license-registry/v1) without trailing slash.

    Only ``LICENSE_GATEWAY_BASE_URL`` enables activate/heartbeat; do not infer from
    ``LICENSE_SERVER_URL`` so legacy validate URLs keep working unchanged.
    """
    return (getattr(settings, "LICENSE_GATEWAY_BASE_URL", None) or "").strip().rstrip("/")


def license_validate_url() -> str:
    base = license_gateway_base_url()
    if base:
        return f"{base}/validate/"
    return (getattr(settings, "LICENSE_SERVER_URL", None) or "").strip()


def post_license_validation(
    license_server_url: str,
    payload: Dict[str, Any] | None = None,
    token: str = "",
    auth_bearer: str = "",
    timeout_seconds: int = 8,
) -> Tuple[bool, Dict]:
    if not license_server_url:
        raise LicenseServerError("LICENSE_SERVER_URL is not configured")

    if bool(getattr(settings, "USE_MOCK_REGISTRY", False)):
        from .mock_registry import mock_post_license_validation

        return mock_post_license_validation(license_server_url, payload, auth_bearer)

    headers = {"Content-Type": "application/json"}
    if auth_bearer:
        headers["Authorization"] = f"Bearer {auth_bearer}"
    elif token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(
            license_server_url,
            json=payload if payload is not None else {},
            headers=headers,
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LicenseServerError(f"License server request failed: {exc}") from exc

    if response.status_code == 429:
        ra = response.headers.get("Retry-After") or response.headers.get("retry-after") or "60"
        try:
            retry_after = max(1, int(ra))
        except (TypeError, ValueError):
            retry_after = 60
        raise LicenseServerError(
            "License server rate limited",
            status_code=429,
            retry_after=retry_after,
        )

    if response.status_code >= 500:
        raise LicenseServerError(f"License server returned {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise LicenseServerError("License server returned non-JSON response") from exc

    is_valid = bool(
        data.get("valid")
        or data.get("is_valid")
        or str(data.get("status", "")).lower() in {"active", "valid"}
    )
    return is_valid, data


def post_gateway_activate(base_url: str, body: dict, timeout_seconds: int = 25) -> dict:
    if bool(getattr(settings, "USE_MOCK_REGISTRY", False)):
        from .mock_registry import mock_post_gateway_activate

        return mock_post_gateway_activate(base_url, body)

    url = f"{base_url.rstrip('/')}/activate/"
    try:
        response = requests.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LicenseServerError(f"License activation request failed: {exc}") from exc

    if response.status_code == 429:
        ra = response.headers.get("Retry-After") or response.headers.get("retry-after") or "60"
        try:
            retry_after = max(1, int(ra))
        except (TypeError, ValueError):
            retry_after = 60
        raise LicenseServerError(
            "License gateway rate limited",
            status_code=429,
            retry_after=retry_after,
        )

    if response.status_code >= 500:
        raise LicenseServerError(f"License gateway returned {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise LicenseServerError("License gateway returned non-JSON response") from exc

    if response.status_code >= 400:
        msg = data.get("message") or data.get("detail") or response.text
        raise LicenseServerError(msg or f"Activation failed ({response.status_code})")

    return data


def post_gateway_heartbeat(base_url: str, bearer: str, body: dict | None = None, timeout_seconds: int = 15) -> dict:
    url = f"{base_url.rstrip('/')}/heartbeat/"
    try:
        response = requests.post(
            url,
            json=body or {},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer}",
            },
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LicenseServerError(f"License heartbeat request failed: {exc}") from exc

    if response.status_code >= 500:
        raise LicenseServerError(f"License gateway returned {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise LicenseServerError("License gateway returned non-JSON response") from exc

    if response.status_code >= 400:
        msg = data.get("message") or data.get("detail") or response.text
        raise LicenseServerError(msg or f"License heartbeat failed ({response.status_code})")

    return data


def post_gateway_ticket_ingest(
    base_url: str,
    bearer: str,
    body: dict | None = None,
    timeout_seconds: int = 15,
) -> dict:
    """POST self-hosted ticket payload to operator /tickets/ingest/."""
    url = f"{base_url.rstrip('/')}/tickets/ingest/"
    try:
        response = requests.post(
            url,
            json=body or {},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer}",
            },
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LicenseServerError(f"Ticket ingest request failed: {exc}") from exc

    if response.status_code >= 500:
        raise LicenseServerError(f"License gateway returned {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise LicenseServerError("License gateway returned non-JSON response") from exc

    if response.status_code >= 400:
        msg = data.get("message") or data.get("detail") or response.text
        raise LicenseServerError(msg or f"Ticket ingest failed ({response.status_code})")

    return data
