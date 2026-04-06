"""
Ticket domain service layer.

All state transitions, assignment, SLA computation, and merge logic
go through this module so validation happens in one place.
"""
from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from licensing.models import LicenseRegistryInstallation

from django.db import models, transaction
from django.utils import timezone

from .models import (
    Ticket, TicketAuditEvent, TicketMessage, TicketRelation,
    TicketRoutingRule, TicketSlaPolicy, TicketSlaSnapshot,
)

logger = logging.getLogger(__name__)

VALID_TRANSITIONS: dict[str, set[str]] = {
    'open': {'assigned', 'in_progress', 'closed'},
    'assigned': {'in_progress', 'pending', 'resolved', 'closed'},
    'in_progress': {'pending', 'resolved', 'closed'},
    'pending': {'in_progress', 'resolved', 'closed'},
    'resolved': {'closed'},
    'closed': set(),
}


class TicketTransitionError(Exception):
    pass


def _audit(ticket, actor, action, changes=None):
    TicketAuditEvent.objects.create(
        ticket=ticket,
        actor=actor,
        action=action,
        changes=changes or {},
    )


def _transition(ticket: Ticket, new_status: str, actor, *, reason: str = ''):
    allowed = VALID_TRANSITIONS.get(ticket.status, set())
    if new_status not in allowed:
        raise TicketTransitionError(
            f'Cannot move from {ticket.status} to {new_status}'
        )
    old = ticket.status
    ticket.status = new_status
    now = timezone.now()
    if new_status == 'resolved':
        ticket.resolved_at = now
    elif new_status == 'closed':
        ticket.closed_at = now
    ticket.save(update_fields=['status', 'resolved_at', 'closed_at', 'updated_at'])
    _audit(ticket, actor, f'status_change', {'from': old, 'to': new_status, 'reason': reason})


# ---------------------------------------------------------------
# Public API
# ---------------------------------------------------------------

@transaction.atomic
def create_ticket(
    *,
    tenant,
    requester,
    subject: str,
    body: str,
    priority: str = 'medium',
    source: str = 'web',
    category: str = '',
    language: str = 'en',
    client_version: str = '',
    deployment_context: str = '',
    attachments=None,
) -> Ticket:
    ticket = Ticket(
        tenant=tenant,
        subject=subject,
        priority=priority,
        source=source,
        requester=requester,
        category=category,
        language=language,
        client_version=(client_version or '')[:64],
        deployment_context=(deployment_context or '')[:32],
    )
    ticket.save()

    TicketMessage.objects.create(
        ticket=ticket,
        author=requester,
        body=body,
        is_internal=False,
        source=source,
    )
    ticket.last_message_at = timezone.now()
    ticket.save(update_fields=['last_message_at'])

    _apply_sla(ticket)
    _auto_route(ticket)
    _audit(ticket, requester, 'created')

    _schedule_operator_bridge_new_ticket(ticket.id)
    return ticket


@transaction.atomic
def assign_ticket(ticket: Ticket, assignee, actor) -> Ticket:
    old_assignee = ticket.assignee_id
    ticket.assignee = assignee
    if ticket.status == 'open':
        ticket.status = 'assigned'
    ticket.save(update_fields=['assignee', 'status', 'updated_at'])
    _audit(ticket, actor, 'assigned', {
        'from_assignee': str(old_assignee) if old_assignee else None,
        'to_assignee': str(assignee.id),
    })
    return ticket


@transaction.atomic
def start_progress(ticket: Ticket, actor) -> Ticket:
    _transition(ticket, 'in_progress', actor)
    if not ticket.first_responded_at:
        ticket.first_responded_at = timezone.now()
        ticket.save(update_fields=['first_responded_at'])
        _mark_sla_achieved(ticket, 'first_response')
    return ticket


@transaction.atomic
def pend_ticket(ticket: Ticket, actor, *, reason: str = '') -> Ticket:
    _transition(ticket, 'pending', actor, reason=reason)
    return ticket


@transaction.atomic
def resolve_ticket(ticket: Ticket, actor, *, reason: str = '') -> Ticket:
    _transition(ticket, 'resolved', actor, reason=reason)
    _mark_sla_achieved(ticket, 'resolution')
    return ticket


@transaction.atomic
def close_ticket(ticket: Ticket, actor, *, reason: str = '') -> Ticket:
    _transition(ticket, 'closed', actor, reason=reason)
    return ticket


@transaction.atomic
def reopen_ticket(ticket: Ticket, actor, *, reason: str = '') -> Ticket:
    if ticket.status not in ('resolved', 'closed'):
        raise TicketTransitionError('Can only reopen resolved or closed tickets')
    old = ticket.status
    ticket.status = 'open'
    ticket.resolved_at = None
    ticket.closed_at = None
    ticket.save(update_fields=['status', 'resolved_at', 'closed_at', 'updated_at'])
    _audit(ticket, actor, 'reopened', {'from': old, 'reason': reason})
    _apply_sla(ticket)
    return ticket


@transaction.atomic
def escalate_ticket(ticket: Ticket, actor, *, reason: str = '') -> Ticket:
    if ticket.priority == 'critical':
        new_priority = 'critical'
    else:
        order = ['low', 'medium', 'high', 'critical']
        idx = order.index(ticket.priority)
        new_priority = order[min(idx + 1, len(order) - 1)]
    old = ticket.priority
    ticket.priority = new_priority
    ticket.save(update_fields=['priority', 'updated_at'])
    _audit(ticket, actor, 'escalated', {'from_priority': old, 'to_priority': new_priority, 'reason': reason})
    _apply_sla(ticket)
    return ticket


@transaction.atomic
def merge_tickets(source: Ticket, target: Ticket, actor) -> Ticket:
    if source.tenant_id != target.tenant_id:
        raise TicketTransitionError('Cannot merge tickets across tenants')
    source.merged_into = target
    source.status = 'closed'
    source.closed_at = timezone.now()
    source.save(update_fields=['merged_into', 'status', 'closed_at', 'updated_at'])
    TicketRelation.objects.create(
        source=source, target=target, relation_type='merged_from', created_by=actor,
    )
    _audit(source, actor, 'merged', {'into_ticket': str(target.id)})
    _audit(target, actor, 'merge_received', {'from_ticket': str(source.id)})
    return target


def add_reply(
    ticket: Ticket, author, body: str, *, is_internal: bool = False,
    source: str = 'web', body_html: str = '',
) -> TicketMessage:
    msg = TicketMessage.objects.create(
        ticket=ticket,
        author=author,
        body=body,
        body_html=body_html,
        is_internal=is_internal,
        source=source,
    )
    ticket.last_message_at = msg.created_at
    ticket.save(update_fields=['last_message_at', 'updated_at'])
    if not is_internal and not ticket.first_responded_at and author != ticket.requester:
        ticket.first_responded_at = msg.created_at
        ticket.save(update_fields=['first_responded_at'])
        _mark_sla_achieved(ticket, 'first_response')
    _audit(ticket, author, 'internal_note' if is_internal else 'reply')
    _schedule_operator_bridge_customer_reply(ticket, author, is_internal, body)
    return msg


# ---------------------------------------------------------------
# SLA helpers
# ---------------------------------------------------------------

def _apply_sla(ticket: Ticket):
    policy = TicketSlaPolicy.objects.filter(
        tenant=ticket.tenant, priority=ticket.priority, is_active=True,
    ).first()
    if not policy:
        return
    ticket.sla_policy = policy
    now = timezone.now()
    ticket.first_response_due_at = now + timedelta(minutes=policy.first_response_minutes)
    ticket.resolution_due_at = now + timedelta(minutes=policy.resolution_minutes)
    ticket.save(update_fields=['sla_policy', 'first_response_due_at', 'resolution_due_at'])

    for metric, target_at in [
        ('first_response', ticket.first_response_due_at),
        ('resolution', ticket.resolution_due_at),
    ]:
        TicketSlaSnapshot.objects.update_or_create(
            ticket=ticket, metric=metric,
            defaults={'target_at': target_at, 'status': 'on_track'},
        )


def _mark_sla_achieved(ticket: Ticket, metric: str):
    snap = TicketSlaSnapshot.objects.filter(ticket=ticket, metric=metric).first()
    if snap and snap.status in ('on_track', 'warning'):
        snap.status = 'achieved'
        snap.achieved_at = timezone.now()
        snap.save(update_fields=['status', 'achieved_at', 'updated_at'])


# ---------------------------------------------------------------
# Auto-routing
# ---------------------------------------------------------------

def _auto_route(ticket: Ticket):
    rules = TicketRoutingRule.objects.filter(
        tenant=ticket.tenant, is_active=True,
    ).select_related('queue').order_by('priority_order')
    for rule in rules:
        if _rule_matches(rule, ticket):
            ticket.queue = rule.queue
            ticket.save(update_fields=['queue'])
            if rule.strategy == 'round_robin':
                _round_robin_assign(ticket, rule.queue)
            elif rule.strategy == 'least_busy':
                _least_busy_assign(ticket, rule.queue)
            return
    from .models import TicketQueue
    default_queue = TicketQueue.objects.filter(
        tenant=ticket.tenant, is_default=True, is_active=True,
    ).first()
    if default_queue:
        ticket.queue = default_queue
        ticket.save(update_fields=['queue'])


def _rule_matches(rule: TicketRoutingRule, ticket: Ticket) -> bool:
    conds = rule.conditions or {}
    if 'priority' in conds and ticket.priority not in (conds['priority'] if isinstance(conds['priority'], list) else [conds['priority']]):
        return False
    if 'category' in conds and ticket.category not in (conds['category'] if isinstance(conds['category'], list) else [conds['category']]):
        return False
    if 'language' in conds and ticket.language not in (conds['language'] if isinstance(conds['language'], list) else [conds['language']]):
        return False
    return True


def _round_robin_assign(ticket: Ticket, queue):
    from .models import TicketRoleProfile
    agents = list(
        TicketRoleProfile.objects.filter(
            tenant=ticket.tenant, role__in=['agent', 'supervisor'], is_active=True,
        ).values_list('user_id', flat=True)
    )
    if not agents:
        return
    last_assigned = (
        Ticket.objects.filter(tenant=ticket.tenant, queue=queue, assignee__isnull=False)
        .order_by('-updated_at')
        .values_list('assignee_id', flat=True)
        .first()
    )
    if last_assigned and last_assigned in agents:
        idx = (agents.index(last_assigned) + 1) % len(agents)
    else:
        idx = 0
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        assignee = User.objects.get(pk=agents[idx])
        ticket.assignee = assignee
        if ticket.status == 'open':
            ticket.status = 'assigned'
        ticket.save(update_fields=['assignee', 'status'])
    except User.DoesNotExist:
        pass


def _least_busy_assign(ticket: Ticket, queue):
    from django.contrib.auth import get_user_model
    from django.db.models import Count
    from .models import TicketRoleProfile
    User = get_user_model()
    agents = list(
        TicketRoleProfile.objects.filter(
            tenant=ticket.tenant, role__in=['agent', 'supervisor'], is_active=True,
        ).values_list('user_id', flat=True)
    )
    if not agents:
        return
    least = (
        User.objects.filter(pk__in=agents)
        .annotate(open_count=Count(
            'assigned_tickets',
            filter=models.Q(assigned_tickets__status__in=['open', 'assigned', 'in_progress']),
        ))
        .order_by('open_count')
        .first()
    )
    if least:
        ticket.assignee = least
        if ticket.status == 'open':
            ticket.status = 'assigned'
        ticket.save(update_fields=['assignee', 'status'])


def _schedule_operator_bridge_new_ticket(ticket_id: uuid.UUID) -> None:
    def _run():
        from . import operator_bridge

        operator_bridge.push_new_ticket_if_configured(ticket_id)

    transaction.on_commit(_run)


def _schedule_operator_bridge_customer_reply(ticket, author, is_internal: bool, body: str) -> None:
    if is_internal or not author or not getattr(ticket, 'requester_id', None):
        return
    if ticket.requester_id != author.id:
        return

    def _run():
        from . import operator_bridge

        operator_bridge.push_customer_reply_if_configured(ticket.id, body)

    transaction.on_commit(_run)


def ensure_registry_bridge_tenant(installation: LicenseRegistryInstallation):
    """One Tenant per registry installation for operator-side bridged tickets."""
    from django.utils.text import slugify

    from saas_platform.models import Tenant
    from saas_platform.pricing_models import PlatformBillingSettings

    key = f'__registry_install__{installation.pk}'
    existing = Tenant.objects.filter(organization_name_key=key).first()
    if existing:
        return existing

    solo = PlatformBillingSettings.get_solo()
    free_limit = solo.default_free_screen_limit
    dom = slugify((installation.domain or 'install').replace('.', '-'))[:40] or 'install'
    uid = str(installation.pk).replace('-', '')[:12]
    base = f'{dom}-{uid}'.lower()[:80]
    slug = base
    n = 0
    while Tenant.objects.filter(slug=slug).exists():
        n += 1
        slug = f'{base}-{n}'[:80]

    return Tenant.objects.create(
        name=(installation.domain or str(installation.pk))[:255],
        slug=slug,
        organization_name_key=key,
        device_limit=free_limit,
    )


@transaction.atomic
def ingest_remote_support_ticket(
    installation: LicenseRegistryInstallation,
    remote_ticket_id: uuid.UUID,
    body: str,
    *,
    subject: str = '',
    priority: str = 'medium',
    category: str = '',
    language: str = 'en',
    requester_name: str = '',
    requester_email: str = '',
    client_version: str = '',
) -> tuple[Ticket, str]:
    """
    Create or append a self-hosted ticket mirrored on the operator DB.

    Returns (ticket, event) where event is 'created', 'appended', or 'noop'.
    """
    valid_pri = {c[0] for c in Ticket.PRIORITY_CHOICES}
    pri = priority if priority in valid_pri else 'medium'

    body = (body or '').strip()
    tenant = ensure_registry_bridge_tenant(installation)
    existing = (
        Ticket.objects.select_for_update()
        .filter(
            registry_installation_id=installation.pk,
            remote_ticket_id=remote_ticket_id,
            is_deleted=False,
        )
        .first()
    )
    if existing:
        if not body:
            return existing, 'noop'
        msg = TicketMessage.objects.create(
            ticket=existing,
            author=None,
            body=body,
            is_internal=False,
            source='api',
        )
        existing.last_message_at = msg.created_at
        existing.save(update_fields=['last_message_at', 'updated_at'])
        _audit(existing, None, 'reply')
        return existing, 'appended'

    subject = (subject or '').strip()
    if not subject:
        raise ValueError('subject is required for a new remote ticket')
    if not body:
        raise ValueError('body is required')

    ticket = Ticket(
        tenant=tenant,
        subject=subject[:255],
        priority=pri,
        source='api',
        requester=None,
        category=(category or '')[:128],
        language=(language or 'en')[:8],
        client_version=(client_version or '')[:64],
        deployment_context='self_hosted',
        registry_installation=installation,
        remote_ticket_id=remote_ticket_id,
        bridge_requester_name=(requester_name or '')[:255],
        bridge_requester_email=(requester_email or '')[:254],
    )
    ticket.save()
    msg = TicketMessage.objects.create(
        ticket=ticket,
        author=None,
        body=body,
        is_internal=False,
        source='api',
    )
    ticket.last_message_at = msg.created_at
    ticket.save(update_fields=['last_message_at'])
    _apply_sla(ticket)
    _auto_route(ticket)
    _audit(ticket, None, 'created')
    return ticket, 'created'
