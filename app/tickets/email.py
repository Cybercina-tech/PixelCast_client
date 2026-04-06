"""
Ticket email integration.

- Outbound: uses SystemEmailSettings / send_system_email for replies.
- Inbound: webhook-based parsing with reply-to token resolution.
- Thread tokens: HMAC-signed ticket-id tokens in Reply-To addresses.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import re
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

TOKEN_PREFIX = 'tkt'
REPLY_TO_DOMAIN_SETTING = 'TICKET_REPLY_TO_DOMAIN'


def _signing_key() -> bytes:
    return settings.SECRET_KEY[:32].encode()


def generate_reply_token(ticket_id: str) -> str:
    """Create an HMAC token that maps to a ticket for email reply threading."""
    raw = f'{TOKEN_PREFIX}:{ticket_id}'
    sig = hmac.new(_signing_key(), raw.encode(), hashlib.sha256).hexdigest()[:16]
    return f'{TOKEN_PREFIX}-{sig}-{ticket_id}'


def parse_reply_token(token: str) -> Optional[str]:
    """Validate and extract the ticket_id from a reply token. Returns None if invalid."""
    pattern = re.compile(rf'^{TOKEN_PREFIX}-([a-f0-9]{{16}})-(.+)$')
    m = pattern.match(token)
    if not m:
        return None
    sig, ticket_id = m.group(1), m.group(2)
    expected_raw = f'{TOKEN_PREFIX}:{ticket_id}'
    expected_sig = hmac.new(_signing_key(), expected_raw.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return ticket_id


def build_reply_to_address(ticket_id: str) -> str:
    """Build a reply-to email address that routes inbound mail to this ticket."""
    domain = getattr(settings, REPLY_TO_DOMAIN_SETTING, None)
    if not domain:
        domain = 'tickets.localhost'
    token = generate_reply_token(ticket_id)
    return f'{token}@{domain}'


def send_ticket_email(
    *,
    to_emails: list[str],
    subject: str,
    body_text: str,
    body_html: str = '',
    reply_to: str = '',
):
    """
    Send a transactional email for a ticket event using the system email stack.

    Falls back gracefully if email is not configured.
    """
    try:
        from core.email_service import send_system_email
        send_system_email(
            subject=subject,
            message=body_text,
            html_message=body_html or None,
            recipient_list=to_emails,
            reply_to=[reply_to] if reply_to else None,
        )
    except Exception as e:
        logger.warning('Ticket email send failed: %s', e)


def send_reply_notification(ticket, message):
    """Notify the requester (or assignee) that a new reply was posted."""
    if not ticket.requester or not ticket.requester.email:
        return
    if message.author_id == ticket.requester_id:
        if ticket.assignee and ticket.assignee.email:
            to = [ticket.assignee.email]
        else:
            return
    else:
        to = [ticket.requester.email]

    reply_to = build_reply_to_address(str(ticket.id))
    subject = f'Re: [{ticket.number}] {ticket.subject}'
    body = f'{message.author.full_name or message.author.username} replied:\n\n{message.body}'
    send_ticket_email(
        to_emails=to,
        subject=subject,
        body_text=body,
        reply_to=reply_to,
    )


def process_inbound_email(*, sender: str, recipient: str, subject: str, body: str) -> bool:
    """
    Process an inbound email (from webhook) and append it to the matching ticket thread.

    Returns True if the email was matched and appended, False otherwise.
    """
    token = recipient.split('@')[0] if '@' in recipient else recipient
    ticket_id = parse_reply_token(token)
    if not ticket_id:
        logger.info('Inbound email did not match a ticket token: %s', recipient)
        return False

    from .models import Ticket
    try:
        ticket = Ticket.objects.get(pk=ticket_id, is_deleted=False)
    except Ticket.DoesNotExist:
        logger.warning('Inbound email matched token but ticket not found: %s', ticket_id)
        return False

    from django.contrib.auth import get_user_model
    User = get_user_model()
    author = User.objects.filter(email__iexact=sender.strip()).first()

    from .services import add_reply
    add_reply(
        ticket,
        author=author,
        body=body.strip(),
        source='email',
    )
    logger.info('Inbound email appended to ticket %s from %s', ticket.number, sender)
    return True
