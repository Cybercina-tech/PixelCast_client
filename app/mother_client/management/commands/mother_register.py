from __future__ import annotations

import logging
import os
from urllib.parse import urljoin, urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone as dj_tz

from mother_client.client import _base_url, _timeout
from mother_client.crypto import encrypt_api_key
from mother_client.models import MotherClientState

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Register this Pixelcast instance with the mother platform (one-time)."

    def handle(self, *args, **options):
        state = MotherClientState.get_solo()
        if state.has_credentials():
            logger.info("mother_register: credentials already stored, skipping")
            return

        if not getattr(settings, "MOTHER_SYNC_ENABLED", False):
            logger.info("mother_register: MOTHER_SYNC_ENABLED is false, skipping")
            return

        base = _base_url()
        if not base:
            logger.warning("mother_register: MOTHER_URL is not set")
            return

        code = (getattr(settings, "PURCHASE_CODE", None) or "").strip()
        if not code:
            logger.warning("mother_register: PURCHASE_CODE is not set")
            return

        parsed = urlparse((getattr(settings, "BASE_URL", None) or "").strip())
        domain = (parsed.netloc or parsed.path or "").strip()
        if not domain:
            logger.warning("mother_register: could not derive domain from BASE_URL")
            return

        version = (getattr(settings, "SCREENGRAM_APP_VERSION", None) or "").strip()
        url = urljoin(base + "/", "api/gateway/register-instance/")
        payload = {
            "purchase_code": code,
            "domain": domain,
            "version": version or "unknown",
        }

        try:
            r = requests.post(url, json=payload, timeout=_timeout())
        except (requests.Timeout, requests.ConnectionError) as exc:
            logger.warning("mother_register: network error: %s", exc)
            return

        if r.status_code == 201:
            data = r.json()
            raw_key = (data.get("api_key") or "").strip()
            inst_raw = data.get("instance_id")
            if not raw_key or not inst_raw:
                logger.error("mother_register: unexpected response body")
                return
            from uuid import UUID

            try:
                iid = UUID(str(inst_raw))
            except ValueError:
                logger.error("mother_register: invalid instance_id in response")
                return
            try:
                enc = encrypt_api_key(raw_key)
            except Exception:
                logger.exception("mother_register: failed to encrypt API key")
                return
            state.instance_id = iid
            state.api_key_encrypted = enc
            state.registered_at = dj_tz.now()
            state.save()
            self.stdout.write(self.style.SUCCESS("Registered with mother platform."))
            if os.environ.get("PURCHASE_CODE", "").strip():
                logger.warning(
                    "mother_register: PURCHASE_CODE is still set in the environment. "
                    "Remove it from env/secrets when possible; credentials are stored encrypted in the database."
                )
            return

        if r.status_code == 409:
            logger.warning(
                "mother_register: purchase already registered on mother (409). "
                "Use the existing instance API key from the operator console and store it locally, "
                "or contact support; automatic registration cannot retrieve the key."
            )
            return

        logger.warning("mother_register: failed with HTTP %s: %s", r.status_code, r.text[:500])
