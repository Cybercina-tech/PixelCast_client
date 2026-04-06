"""
Celery tasks for ticket SLA monitoring, assignment automation, and notifications.

Reuses the project's existing notification dispatcher for alerts
and Channels layer for real-time updates.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# SLA check (run every 2–5 min via celery-beat)
# -------------------------------------------------------------------

@shared_task(name='tickets.check_sla_deadlines')
def check_sla_deadlines():
    """
    Scan tickets approaching or past SLA deadlines.

    - Mark snapshots as 'warning' when within the warning threshold.
    - Mark snapshots as 'breached' when past deadline.
    - Dispatch notification events for each state change.
    """
    from .models import Ticket, TicketSlaSnapshot

    now = timezone.now()
    changed = 0

    on_track = TicketSlaSnapshot.objects.filter(
        status='on_track',
    ).select_related('ticket', 'ticket__sla_policy')

    for snap in on_track.iterator():
        policy = snap.ticket.sla_policy
        if not policy:
            continue
        threshold_pct = policy.warning_threshold_pct / 100.0
        total_seconds = (snap.target_at - snap.ticket.created_at).total_seconds()
        warning_at = snap.ticket.created_at + timedelta(seconds=total_seconds * threshold_pct)

        if now >= snap.target_at:
            snap.status = 'breached'
            snap.breached_at = now
            snap.save(update_fields=['status', 'breached_at', 'updated_at'])
            _dispatch_sla_event(snap.ticket, snap.metric, 'breached')
            changed += 1
        elif now >= warning_at:
            snap.status = 'warning'
            snap.save(update_fields=['status', 'updated_at'])
            _dispatch_sla_event(snap.ticket, snap.metric, 'warning')
            changed += 1

    warning_snaps = TicketSlaSnapshot.objects.filter(
        status='warning',
    ).select_related('ticket')

    for snap in warning_snaps.iterator():
        if now >= snap.target_at:
            snap.status = 'breached'
            snap.breached_at = now
            snap.save(update_fields=['status', 'breached_at', 'updated_at'])
            _dispatch_sla_event(snap.ticket, snap.metric, 'breached')
            changed += 1

    logger.info('SLA check complete: %d snapshots updated', changed)
    return changed


def _dispatch_sla_event(ticket, metric, level):
    """Fire a notification event through the existing dispatcher."""
    try:
        from notifications.dispatcher import NotificationDispatcher
        event_key = f'ticket.sla_{level}'
        NotificationDispatcher.dispatch(
            event_key=event_key,
            payload={
                'ticket_id': str(ticket.id),
                'ticket_number': ticket.number,
                'subject': ticket.subject,
                'metric': metric,
                'tenant_id': str(ticket.tenant_id),
            },
            force=False,
        )
    except Exception as e:
        logger.warning('SLA notification dispatch failed: %s', e)

    _push_ws_update(ticket, f'sla_{level}', {'metric': metric})


# -------------------------------------------------------------------
# Real-time WebSocket push
# -------------------------------------------------------------------

def _push_ws_update(ticket, event_type, extra=None):
    """Push a ticket event over the Channels layer."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        layer = get_channel_layer()
        if not layer:
            return
        group = f'ticket_{ticket.tenant_id}'
        payload = {
            'type': 'ticket.event',
            'data': {
                'event': event_type,
                'ticket_id': str(ticket.id),
                'ticket_number': ticket.number,
                **(extra or {}),
            },
        }
        async_to_sync(layer.group_send)(group, payload)
    except Exception as e:
        logger.debug('WS push failed (non-critical): %s', e)


# -------------------------------------------------------------------
# Ticket lifecycle notifications
# -------------------------------------------------------------------

@shared_task(name='tickets.notify_ticket_created')
def notify_ticket_created(ticket_id: str):
    from .models import Ticket
    try:
        ticket = Ticket.objects.select_related('tenant', 'requester').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return
    _dispatch_event('ticket.created', ticket, {
        'requester_email': ticket.requester.email if ticket.requester else '',
    })
    _push_ws_update(ticket, 'created')


@shared_task(name='tickets.notify_ticket_assigned')
def notify_ticket_assigned(ticket_id: str, assignee_id: str):
    from .models import Ticket
    try:
        ticket = Ticket.objects.select_related('tenant', 'assignee').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return
    _dispatch_event('ticket.assigned', ticket, {
        'assignee_email': ticket.assignee.email if ticket.assignee else '',
        'assignee_id': assignee_id,
    })
    _push_ws_update(ticket, 'assigned', {'assignee_id': assignee_id})


@shared_task(name='tickets.notify_ticket_reply')
def notify_ticket_reply(ticket_id: str, message_id: str, is_internal: bool = False):
    from .models import Ticket
    try:
        ticket = Ticket.objects.select_related('tenant').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return
    event_key = 'ticket.reply_received'
    _dispatch_event(event_key, ticket, {
        'message_id': message_id,
        'is_internal': is_internal,
    })
    _push_ws_update(ticket, 'reply', {'message_id': message_id})


@shared_task(name='tickets.notify_csat_submitted')
def notify_csat_submitted(ticket_id: str, score: int):
    from .models import Ticket
    try:
        ticket = Ticket.objects.select_related('tenant').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return
    _dispatch_event('ticket.csat_submitted', ticket, {'score': score})


def _dispatch_event(event_key: str, ticket, extra: dict):
    try:
        from notifications.dispatcher import NotificationDispatcher
        NotificationDispatcher.dispatch(
            event_key=event_key,
            payload={
                'ticket_id': str(ticket.id),
                'ticket_number': ticket.number,
                'subject': ticket.subject,
                'tenant_id': str(ticket.tenant_id),
                **extra,
            },
            force=False,
        )
    except Exception as e:
        logger.warning('Ticket notification dispatch failed for %s: %s', event_key, e)
