"""Inbound email webhook for ticket reply threading."""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .email import process_inbound_email

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def inbound_email_webhook(request):
    """
    Receive inbound email payloads from providers (SendGrid Inbound Parse, etc.).

    Expected fields: sender, recipient, subject, body_plain (or text).
    The endpoint is unauthenticated; verification should be done via
    provider-specific signature validation in middleware or here.
    """
    data = request.data
    sender = data.get('sender') or data.get('from') or ''
    recipient = data.get('recipient') or data.get('to') or ''
    subject = data.get('subject', '')
    body = data.get('body_plain') or data.get('text') or data.get('body', '')

    if not sender or not recipient:
        return Response({'detail': 'sender and recipient are required'}, status=status.HTTP_400_BAD_REQUEST)

    matched = process_inbound_email(
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
    )
    return Response({'matched': matched}, status=status.HTTP_200_OK)
