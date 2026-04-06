"""
Envato Market API — verify purchase codes (author sale by code).

Used only on the operator license gateway (SaaS deployment with personal token).
Docs: https://api.envato.com/v3/market/author/sale?code=...
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ENVATO_SALE_URL = "https://api.envato.com/v3/market/author/sale"


class EnvatoApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def fetch_sale_by_purchase_code(purchase_code: str, timeout_seconds: int = 12) -> dict[str, Any]:
    """
    Return Envato JSON for a valid sale, or raise EnvatoApiError.

    Typical successful shape includes: buyer, sold_at, item{id,name,...}, license, support_until.
    """
    token = (getattr(settings, "CODECANYON_TOKEN", None) or "").strip()
    if not token:
        raise EnvatoApiError("CODECANYON_TOKEN is not configured on the license gateway", status_code=None)

    code = (purchase_code or "").strip()
    if not code:
        raise EnvatoApiError("Purchase code is required", status_code=400)

    url = ENVATO_SALE_URL
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "ScreenGram-LicenseGateway/1.0",
    }
    try:
        response = requests.get(url, params={"code": code}, headers=headers, timeout=timeout_seconds)
    except requests.RequestException as exc:
        logger.warning("Envato request failed: %s", exc)
        raise EnvatoApiError(f"Envato request failed: {exc}", status_code=None) from exc

    if response.status_code == 404:
        raise EnvatoApiError("Purchase code not found or not sold by this author", status_code=404)
    if response.status_code == 403:
        raise EnvatoApiError("Envato token invalid or missing required permissions", status_code=403)
    if response.status_code == 429:
        raise EnvatoApiError("Envato rate limit exceeded", status_code=429)
    if response.status_code >= 400:
        raise EnvatoApiError(f"Envato error HTTP {response.status_code}", status_code=response.status_code)

    try:
        return response.json()
    except ValueError as exc:
        raise EnvatoApiError("Envato returned non-JSON", status_code=None) from exc


def parse_sale_item_id(sale: dict[str, Any]) -> int | None:
    item = sale.get("item") or {}
    if isinstance(item, dict):
        raw = item.get("id")
        try:
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None
    return None
