from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _timeout() -> float:
    return float(getattr(settings, "MOTHER_HTTP_TIMEOUT_SECONDS", 10))


def _base_url() -> str:
    u = (getattr(settings, "MOTHER_URL", None) or "").strip().rstrip("/")
    return u


def register_instance(
    *,
    purchase_code: str,
    domain: str,
    version: str = "",
) -> dict[str, Any]:
    base = _base_url()
    if not base:
        raise ValueError("MOTHER_URL is not configured")
    url = urljoin(base + "/", "api/gateway/register-instance/")
    payload = {
        "purchase_code": purchase_code.strip(),
        "domain": domain.strip(),
        "version": (version or "").strip() or "unknown",
    }
    r = requests.post(url, json=payload, timeout=_timeout())
    r.raise_for_status()
    return r.json()


def send_heartbeat(instance_key: str, *, version: str = "") -> None:
    base = _base_url()
    if not base:
        raise ValueError("MOTHER_URL is not configured")
    url = urljoin(base + "/", "api/gateway/heartbeat/")
    body = {"version": (version or "").strip()[:20], "status": "ok"}
    r = requests.post(
        url,
        headers={"X-Instance-Key": instance_key},
        json=body,
        timeout=_timeout(),
    )
    r.raise_for_status()


def send_usage_report(instance_key: str, payload: dict[str, Any]) -> None:
    base = _base_url()
    if not base:
        raise ValueError("MOTHER_URL is not configured")
    url = urljoin(base + "/", "api/gateway/usage-report/")
    r = requests.post(
        url,
        headers={"X-Instance-Key": instance_key},
        json=payload,
        timeout=_timeout(),
    )
    r.raise_for_status()


def check_feature_allowed(instance_key: str, feature: str) -> bool | None:
    """
    Ask mother whether this instance may use a feature (e.g. saas_mode).

    Returns:
        True / False when the server responds with JSON {"allowed": bool}
        None on network/HTTP errors or malformed response (caller should deny).
    """
    base = _base_url()
    if not base:
        logger.warning("mother_client: MOTHER_URL not set; feature check denied")
        return None
    url = urljoin(base + "/", "api/gateway/feature-check/")
    try:
        r = requests.post(
            url,
            headers={"X-Instance-Key": instance_key},
            json={"feature": (feature or "").strip()},
            timeout=_timeout(),
        )
        if r.status_code == 403:
            return False
        if r.status_code >= 400:
            logger.warning(
                "mother_client: feature-check HTTP %s: %s",
                r.status_code,
                (r.text or "")[:200],
            )
            return None
        data = r.json()
        if isinstance(data, dict) and "allowed" in data:
            return bool(data.get("allowed"))
    except requests.RequestException as exc:
        logger.warning("mother_client: feature-check request failed: %s", exc)
        return None
    except ValueError:
        logger.warning("mother_client: feature-check invalid JSON")
        return None
    return None


def post_ticket(instance_key: str, payload: dict[str, Any]) -> requests.Response:
    base = _base_url()
    if not base:
        raise ValueError("MOTHER_URL is not configured")
    url = urljoin(base + "/", "api/gateway/ticket/")
    return requests.post(
        url,
        headers={"X-Instance-Key": instance_key},
        json=payload,
        timeout=_timeout(),
    )
