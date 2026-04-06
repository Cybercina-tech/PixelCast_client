from __future__ import annotations

import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone as dj_tz

from mother_client import client as mother_http
from mother_client.crypto import decrypt_api_key
from mother_client.models import MotherClientState
from mother_client.services import collect_usage_payload

logger = logging.getLogger(__name__)

_RETRY_KWARGS = {"max_retries": 3, "countdown": 60}


@shared_task(
    bind=True,
    autoretry_for=(requests.Timeout, requests.ConnectionError),
    retry_kwargs=_RETRY_KWARGS,
    name="mother_client.tasks.mother_send_heartbeat",
)
def mother_send_heartbeat(self) -> None:
    if not getattr(settings, "MOTHER_SYNC_ENABLED", False):
        return
    state = MotherClientState.get_solo()
    if not state.has_credentials():
        return
    try:
        key = decrypt_api_key(state.api_key_encrypted)
    except Exception:
        logger.exception("mother_send_heartbeat: cannot decrypt API key")
        return
    ver = (getattr(settings, "SCREENGRAM_APP_VERSION", None) or "").strip()
    mother_http.send_heartbeat(key, version=ver)
    state.last_heartbeat_ok_at = dj_tz.now()
    state.save(update_fields=["last_heartbeat_ok_at", "updated_at"])


@shared_task(
    bind=True,
    autoretry_for=(requests.Timeout, requests.ConnectionError),
    retry_kwargs=_RETRY_KWARGS,
    name="mother_client.tasks.mother_send_usage_report",
)
def mother_send_usage_report(self) -> None:
    if not getattr(settings, "MOTHER_SYNC_ENABLED", False):
        return
    state = MotherClientState.get_solo()
    if not state.has_credentials():
        return
    try:
        key = decrypt_api_key(state.api_key_encrypted)
    except Exception:
        logger.exception("mother_send_usage_report: cannot decrypt API key")
        return
    payload = collect_usage_payload()
    mother_http.send_usage_report(key, payload)
    state.last_usage_report_ok_at = dj_tz.now()
    state.save(update_fields=["last_usage_report_ok_at", "updated_at"])
