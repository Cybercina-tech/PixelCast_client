"""
Ticket-specific permission helpers and DRF permission classes.

Maps platform product roles to ticket capabilities without mutating
the global User.role or accounts ROLE_PERMISSIONS.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from .models import TicketRoleProfile

TICKET_ROLE_CAPABILITIES: dict[str, set[str]] = {
    'customer': {
        'ticket.create',
        'ticket.view_own',
        'ticket.reply_own',
        'ticket.upload_own',
        'ticket.csat_submit',
    },
    'agent': {
        'ticket.create',
        'ticket.view_own',
        'ticket.view_queue',
        'ticket.reply_own',
        'ticket.reply_assigned',
        'ticket.internal_note',
        'ticket.assign_self',
        'ticket.transition',
        'ticket.upload_own',
        'ticket.upload_assigned',
        'ticket.use_canned',
        'ticket.csat_submit',
    },
    'supervisor': {
        'ticket.create',
        'ticket.view_own',
        'ticket.view_queue',
        'ticket.view_all',
        'ticket.reply_own',
        'ticket.reply_assigned',
        'ticket.reply_any',
        'ticket.internal_note',
        'ticket.assign_self',
        'ticket.assign_others',
        'ticket.transition',
        'ticket.escalate',
        'ticket.merge',
        'ticket.upload_own',
        'ticket.upload_assigned',
        'ticket.use_canned',
        'ticket.manage_canned',
        'ticket.view_analytics',
        'ticket.csat_submit',
    },
    'admin': {
        'ticket.create',
        'ticket.view_own',
        'ticket.view_queue',
        'ticket.view_all',
        'ticket.reply_own',
        'ticket.reply_assigned',
        'ticket.reply_any',
        'ticket.internal_note',
        'ticket.assign_self',
        'ticket.assign_others',
        'ticket.transition',
        'ticket.escalate',
        'ticket.merge',
        'ticket.upload_own',
        'ticket.upload_assigned',
        'ticket.use_canned',
        'ticket.manage_canned',
        'ticket.manage_queues',
        'ticket.manage_sla',
        'ticket.manage_routing',
        'ticket.manage_tags',
        'ticket.manage_roles',
        'ticket.view_analytics',
        'ticket.export',
        'ticket.csat_submit',
    },
}


def get_ticket_role(user, tenant) -> str | None:
    """Resolve the effective ticket-domain role for *user* within *tenant*."""
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser or getattr(user, 'role', '') == 'Developer':
        return 'admin'

    profile = (
        TicketRoleProfile.objects
        .filter(tenant=tenant, user=user, is_active=True)
        .values_list('role', flat=True)
        .first()
    )
    if profile:
        return profile

    return 'customer'


def has_ticket_capability(user, tenant, capability: str) -> bool:
    role = get_ticket_role(user, tenant)
    if not role:
        return False
    return capability in TICKET_ROLE_CAPABILITIES.get(role, set())


def get_user_tenant(user):
    """Return the tenant linked to the user, or None."""
    return getattr(user, 'tenant', None)


# ---------------------------------------------------------------
# DRF permission classes
# ---------------------------------------------------------------

class IsTicketParticipant(BasePermission):
    """Allow access if user is requester or assignee of the ticket."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or getattr(user, 'role', '') == 'Developer':
            return True
        return obj.requester_id == user.id or obj.assignee_id == user.id


class CanViewTicket(BasePermission):
    """View permission based on ticket role capabilities."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        tenant = obj.tenant
        if has_ticket_capability(user, tenant, 'ticket.view_all'):
            return True
        if has_ticket_capability(user, tenant, 'ticket.view_queue') and obj.assignee_id == user.id:
            return True
        if has_ticket_capability(user, tenant, 'ticket.view_own') and obj.requester_id == user.id:
            return True
        return False


class CanManageTicketSettings(BasePermission):
    """Allow management of SLA, queues, routing, tags."""

    def has_permission(self, request, view):
        user = request.user
        tenant = get_user_tenant(user)
        if not tenant:
            return user.is_superuser or getattr(user, 'role', '') == 'Developer'
        return has_ticket_capability(user, tenant, 'ticket.manage_sla')


class IsPlatformTicketAdmin(BasePermission):
    """Super-admin / Developer access to platform-wide ticket endpoints."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_developer())
