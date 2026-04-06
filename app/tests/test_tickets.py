"""
Comprehensive test suite for the ticket system.

Covers: tenant isolation, lifecycle transitions, permissions,
merge/escalation, SLA, email threading, sidebar, and exports.
"""
import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from saas_platform.models import Tenant
from tickets.models import (
    Ticket, TicketCannedResponse, TicketMessage, TicketQueue,
    TicketRoleProfile, TicketRoutingRule, TicketSlaPolicy,
    TicketSlaSnapshot, TicketTag,
)
from tickets.services import (
    TicketTransitionError, assign_ticket, close_ticket, create_ticket,
    escalate_ticket, merge_tickets, pend_ticket, reopen_ticket,
    resolve_ticket, start_progress,
)
from tickets.email import generate_reply_token, parse_reply_token

from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tenant_a(db):
    return Tenant.objects.create(name='Tenant A', slug='tenant-a')


@pytest.fixture
def tenant_b(db):
    return Tenant.objects.create(name='Tenant B', slug='tenant-b')


@pytest.fixture
def requester_a(db, tenant_a):
    u = User.objects.create_user(
        username='req_a', email='req_a@a.com', password='pass',
        role='Employee', tenant=tenant_a,
    )
    return u


@pytest.fixture
def requester_b(db, tenant_b):
    u = User.objects.create_user(
        username='req_b', email='req_b@b.com', password='pass',
        role='Employee', tenant=tenant_b,
    )
    return u


@pytest.fixture
def agent_a(db, tenant_a):
    u = User.objects.create_user(
        username='agent_a', email='agent_a@a.com', password='pass',
        role='Employee', tenant=tenant_a,
    )
    TicketRoleProfile.objects.create(tenant=tenant_a, user=u, role='agent')
    return u


@pytest.fixture
def dev_user(db):
    return User.objects.create_user(
        username='dev', email='dev@test.com', password='pass',
        role='Developer', is_superuser=True, is_staff=True,
    )


@pytest.fixture
def ticket_a(tenant_a, requester_a):
    return create_ticket(
        tenant=tenant_a, requester=requester_a,
        subject='Issue A', body='Details of issue A',
    )


@pytest.fixture
def sla_policy_a(tenant_a):
    return TicketSlaPolicy.objects.create(
        tenant=tenant_a, name='Standard', priority='medium',
        first_response_minutes=60, resolution_minutes=480,
    )


# ---------------------------------------------------------------------------
# Tenant Isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTenantIsolation:
    def test_requester_cannot_see_other_tenant_tickets(self, requester_a, requester_b, tenant_a, tenant_b):
        t1 = create_ticket(tenant=tenant_a, requester=requester_a, subject='A1', body='body')
        t2 = create_ticket(tenant=tenant_b, requester=requester_b, subject='B1', body='body')
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.get('/api/tickets/')
        assert r.status_code == 200
        ids = [t['id'] for t in r.data]
        assert str(t1.id) in ids
        assert str(t2.id) not in ids

    def test_requester_cannot_access_other_tenant_ticket_detail(self, requester_a, requester_b, tenant_a, tenant_b):
        t2 = create_ticket(tenant=tenant_b, requester=requester_b, subject='B2', body='body')
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.get(f'/api/tickets/{t2.id}/')
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLifecycle:
    def test_full_happy_path(self, ticket_a, agent_a, dev_user):
        t = ticket_a
        assert t.status == 'open'

        t = assign_ticket(t, agent_a, dev_user)
        assert t.status == 'assigned'

        t = start_progress(t, agent_a)
        assert t.status == 'in_progress'
        assert t.first_responded_at is not None

        t = pend_ticket(t, agent_a, reason='waiting for customer')
        assert t.status == 'pending'

        t = resolve_ticket(t, agent_a, reason='fixed')
        assert t.status == 'resolved'
        assert t.resolved_at is not None

        t = close_ticket(t, dev_user)
        assert t.status == 'closed'
        assert t.closed_at is not None

    def test_invalid_transition_raises(self, ticket_a, dev_user):
        t = ticket_a
        with pytest.raises(TicketTransitionError):
            resolve_ticket(t, dev_user)

    def test_reopen_from_resolved(self, ticket_a, agent_a, dev_user):
        t = assign_ticket(ticket_a, agent_a, dev_user)
        t = start_progress(t, agent_a)
        t = resolve_ticket(t, agent_a)
        t = reopen_ticket(t, dev_user, reason='not actually fixed')
        assert t.status == 'open'
        assert t.resolved_at is None

    def test_escalation_bumps_priority(self, ticket_a, dev_user):
        assert ticket_a.priority == 'medium'
        t = escalate_ticket(ticket_a, dev_user, reason='urgent')
        assert t.priority == 'high'
        t = escalate_ticket(t, dev_user)
        assert t.priority == 'critical'
        t = escalate_ticket(t, dev_user)
        assert t.priority == 'critical'


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMerge:
    def test_merge_tickets(self, tenant_a, requester_a, dev_user):
        t1 = create_ticket(tenant=tenant_a, requester=requester_a, subject='Dup 1', body='A')
        t2 = create_ticket(tenant=tenant_a, requester=requester_a, subject='Dup 2', body='B')
        target = merge_tickets(t1, t2, dev_user)
        t1.refresh_from_db()
        assert t1.status == 'closed'
        assert t1.merged_into_id == t2.id
        assert target.id == t2.id

    def test_cannot_merge_across_tenants(self, tenant_a, tenant_b, requester_a, requester_b, dev_user):
        t1 = create_ticket(tenant=tenant_a, requester=requester_a, subject='A', body='A')
        t2 = create_ticket(tenant=tenant_b, requester=requester_b, subject='B', body='B')
        with pytest.raises(TicketTransitionError):
            merge_tickets(t1, t2, dev_user)


# ---------------------------------------------------------------------------
# SLA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSla:
    def test_sla_snapshots_created_on_ticket_create(self, tenant_a, requester_a, sla_policy_a):
        t = create_ticket(
            tenant=tenant_a, requester=requester_a,
            subject='SLA test', body='testing SLA', priority='medium',
        )
        snaps = TicketSlaSnapshot.objects.filter(ticket=t)
        assert snaps.count() == 2
        fr = snaps.get(metric='first_response')
        assert fr.status == 'on_track'
        res = snaps.get(metric='resolution')
        assert res.status == 'on_track'

    def test_first_response_marked_achieved(self, tenant_a, requester_a, agent_a, sla_policy_a, dev_user):
        t = create_ticket(
            tenant=tenant_a, requester=requester_a,
            subject='SLA test 2', body='testing', priority='medium',
        )
        t = assign_ticket(t, agent_a, dev_user)
        t = start_progress(t, agent_a)
        snap = TicketSlaSnapshot.objects.get(ticket=t, metric='first_response')
        assert snap.status == 'achieved'


# ---------------------------------------------------------------------------
# Email threading
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestEmailThreading:
    def test_reply_token_roundtrip(self):
        ticket_id = 'aabbccdd-1122-3344-5566-778899aabbcc'
        token = generate_reply_token(ticket_id)
        assert parse_reply_token(token) == ticket_id

    def test_invalid_token_returns_none(self):
        assert parse_reply_token('garbage') is None
        assert parse_reply_token('tkt-0000000000000000-fake') is None


# ---------------------------------------------------------------------------
# Requester API
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRequesterAPI:
    def test_create_ticket(self, requester_a):
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.post('/api/tickets/', {
            'subject': 'Help me',
            'body': 'I need help',
            'priority': 'high',
        })
        assert r.status_code == 201
        assert r.data['subject'] == 'Help me'
        assert r.data['priority'] == 'high'

    def test_create_ticket_priority_normal_alias_to_medium(self, requester_a):
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.post('/api/tickets/', {
            'subject': 'Alias priority',
            'body': 'Body',
            'priority': 'normal',
        })
        assert r.status_code == 201
        assert r.data['priority'] == 'medium'

    def test_list_tickets(self, requester_a, ticket_a):
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.get('/api/tickets/')
        assert r.status_code == 200
        assert len(r.data) >= 1

    def test_reply_to_ticket(self, requester_a, ticket_a):
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.post(f'/api/tickets/{ticket_a.id}/reply/', {
            'body': 'Follow-up info',
        })
        assert r.status_code == 201
        assert TicketMessage.objects.filter(ticket=ticket_a).count() == 2

    def test_unauthenticated_blocked(self):
        client = APIClient()
        r = client.get('/api/tickets/')
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Platform API
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPlatformAPI:
    def test_queue_list(self, dev_user, ticket_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.get('/api/platform/tickets/queue/')
        assert r.status_code == 200
        assert len(r.data) >= 1

    def test_assign_ticket(self, dev_user, ticket_a, agent_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.post(f'/api/platform/tickets/queue/{ticket_a.id}/assign/', {
            'assignee_id': str(agent_a.id),
        })
        assert r.status_code == 200
        assert r.data['assignee'] == agent_a.id

    def test_transition_ticket(self, dev_user, ticket_a, agent_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        client.post(f'/api/platform/tickets/queue/{ticket_a.id}/assign/', {
            'assignee_id': str(agent_a.id),
        })
        r = client.post(f'/api/platform/tickets/queue/{ticket_a.id}/transition/', {
            'action': 'start_progress',
        })
        assert r.status_code == 200
        assert r.data['status'] == 'in_progress'

    def test_non_developer_blocked(self, requester_a, ticket_a):
        client = APIClient()
        client.force_authenticate(user=requester_a)
        r = client.get('/api/platform/tickets/queue/')
        assert r.status_code == 403

    def test_create_ticket_on_behalf(self, dev_user, tenant_a, requester_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.post('/api/platform/tickets/queue/', {
            'tenant_id': str(tenant_a.id),
            'requester_id': requester_a.id,
            'subject': 'Admin-created ticket',
            'body': 'Created by super-admin on behalf of user',
            'priority': 'high',
        })
        assert r.status_code == 201
        assert r.data['subject'] == 'Admin-created ticket'
        assert r.data['priority'] == 'high'
        assert r.data['requester'] == requester_a.id

    def test_list_tenants(self, dev_user, tenant_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.get('/api/platform/tickets/queue/tenants/')
        assert r.status_code == 200
        slugs = [t['slug'] for t in r.data]
        assert tenant_a.slug in slugs

    def test_search_users(self, dev_user, requester_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.get('/api/platform/tickets/queue/users/', {'search': requester_a.email[:5]})
        assert r.status_code == 200
        emails = [u['email'] for u in r.data]
        assert requester_a.email in emails

    def test_reply_to_ticket(self, dev_user, ticket_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.post(f'/api/platform/tickets/queue/{ticket_a.id}/reply/', {
            'body': 'Platform agent response',
        })
        assert r.status_code == 201
        assert 'id' in r.data

    def test_internal_note(self, dev_user, ticket_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.post(f'/api/platform/tickets/queue/{ticket_a.id}/reply/', {
            'body': 'This is private',
            'is_internal': True,
        })
        assert r.status_code == 201
        detail = client.get(f'/api/platform/tickets/queue/{ticket_a.id}/').data
        internals = [m for m in detail['messages'] if m['is_internal']]
        assert len(internals) >= 1


# ---------------------------------------------------------------------------
# Sidebar visibility
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSidebarVisibility:
    def test_developer_sees_tickets_in_sidebar(self, dev_user):
        from accounts.sidebar_config import filter_sidebar_items
        items = filter_sidebar_items(dev_user)
        ids = [i['id'] for i in items]
        assert 'tickets' in ids

    def test_employee_sees_tickets_in_sidebar(self, requester_a):
        from accounts.sidebar_config import filter_sidebar_items
        items = filter_sidebar_items(requester_a)
        ids = [i['id'] for i in items]
        assert 'tickets' in ids

    def test_visitor_sees_tickets_in_sidebar(self, tenant_a):
        visitor = User.objects.create_user(
            username='vis', email='vis@a.com', password='pass',
            role='Visitor', tenant=tenant_a,
        )
        from accounts.sidebar_config import filter_sidebar_items
        items = filter_sidebar_items(visitor)
        ids = [i['id'] for i in items]
        assert 'tickets' in ids


# ---------------------------------------------------------------------------
# Analytics & export
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAnalyticsAndExport:
    def test_analytics_endpoint(self, dev_user, ticket_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.get('/api/platform/tickets/analytics/')
        assert r.status_code == 200
        assert 'total' in r.data
        assert 'by_status' in r.data

    def test_csv_export(self, dev_user, ticket_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.get('/api/platform/tickets/export.csv')
        assert r.status_code == 200
        assert 'text/csv' in r['Content-Type']

    def test_agent_performance(self, dev_user, ticket_a):
        client = APIClient()
        client.force_authenticate(user=dev_user)
        r = client.get('/api/platform/tickets/agent-performance/')
        assert r.status_code == 200
        assert 'agents' in r.data


# ---------------------------------------------------------------------------
# Tenant assignment (self-hosted / no SaaS flag)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantEnsureForTickets:
    @override_settings(PLATFORM_SAAS_ENABLED=False, DEPLOYMENT_MODE='self_hosted')
    def test_ensure_user_tenant_then_create_ticket(self):
        from saas_platform.tenant_assignment import ensure_user_tenant

        u = User.objects.create_user(
            username='solo_ticket',
            email='solo_ticket@example.com',
            password='pass',
            role='Employee',
        )
        assert u.tenant_id is None
        ensure_user_tenant(u)
        u.refresh_from_db()
        assert u.tenant_id is not None
        assert u.tenant.slug != 'default'
        assert u.tenant.organization_name_key.startswith('__user__')

        client = APIClient()
        client.force_authenticate(user=u)
        r = client.post(
            '/api/tickets/',
            {'subject': 'Help', 'body': 'Body', 'priority': 'medium'},
        )
        assert r.status_code == 201

    @override_settings(PLATFORM_SAAS_ENABLED=False, DEPLOYMENT_MODE='self_hosted')
    def test_ensure_user_tenant_shared_organization(self):
        from saas_platform.tenant_assignment import ensure_user_tenant

        u1 = User.objects.create_user(
            username='org_a1',
            email='org_a1@example.com',
            password='pass',
            role='Employee',
            organization_name='Acme Corp',
        )
        u2 = User.objects.create_user(
            username='org_a2',
            email='org_a2@example.com',
            password='pass',
            role='Employee',
            organization_name='Acme Corp',
        )
        ensure_user_tenant(u1)
        ensure_user_tenant(u2)
        u1.refresh_from_db()
        u2.refresh_from_db()
        assert u1.tenant_id == u2.tenant_id
        assert u1.tenant.organization_name_key == 'Acme Corp'

    @override_settings(PLATFORM_SAAS_ENABLED=False, DEPLOYMENT_MODE='self_hosted')
    def test_rehome_from_legacy_default_to_personal(self):
        from saas_platform.tenant_assignment import rehome_from_legacy_default

        default_t, _ = Tenant.objects.get_or_create(
            slug='default',
            defaults={'name': 'Default', 'organization_name_key': ''},
        )
        u = User.objects.create_user(
            username='legacy_default',
            email='legacy_default@example.com',
            password='pass',
            role='Employee',
            tenant=default_t,
        )
        rehome_from_legacy_default(u)
        u.refresh_from_db()
        assert u.tenant_id != default_t.id
        assert u.tenant.organization_name_key.startswith('__user__')
