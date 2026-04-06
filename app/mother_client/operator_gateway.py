"""
Optional ticket forwarding via mother HTTP gateway (X-Instance-Key).

Used when MOTHER_TICKET_VIA_GATEWAY is true and local credentials exist.
"""

from __future__ import annotations

import logging

from django.conf import settings

from mother_client.client import post_ticket
from mother_client.crypto import decrypt_api_key
from mother_client.models import MotherClientState

logger = logging.getLogger(__name__)


def try_push_ticket_via_mother_gateway(*, ticket, body: str) -> bool:
    """
    POST ticket to mother /api/gateway/ticket/. Returns True if the request succeeded (2xx).
    """
    if not getattr(settings, "MOTHER_TICKET_VIA_GATEWAY", False):
        return False
    state = MotherClientState.get_solo()
    if not state.has_credentials():
        return False
    try:
        key = decrypt_api_key(state.api_key_encrypted)
    except Exception:
        logger.warning("Mother gateway ticket: cannot decrypt API key")
        return False

    req = ticket.requester
    email = ((req.email if req else "") or "").strip()[:254]
    text = (body or "").strip()
    if not text:
        return False

    payload = {
        "subject": (ticket.subject or "Support")[:255],
        "body": text,
        "priority": ticket.priority,
        "customer_email": email,
        "remote_ticket_id": str(ticket.id),
    }
    try:
        r = post_ticket(key, payload)
    except Exception as exc:
        logger.warning("Mother gateway ticket: request failed: %s", exc)
        return False
    if r.ok:
        return True
    logger.warning(
        "Mother gateway ticket: HTTP %s %s",
        r.status_code,
        (r.text or "")[:300],
    )
    return False
