"""Self-hosted ticket mirror: registry ingest API and outbound bridge client."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

pytest_plugins = ['tests.test_tickets']
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from licensing.models import LicenseRegistryInstallation, LicenseRegistryPurchase, LicenseState
from licensing.registry_service import hash_activation_token
from tickets.models import Ticket, TicketMessage
from tickets.services import create_ticket


@pytest.fixture
def bridge_registry(db):
    fp = 'c' * 64
    purchase = LicenseRegistryPurchase.objects.create(code_fingerprint=fp)
    token = 'bridge-test-token-plain'
    inst = LicenseRegistryInstallation.objects.create(
        purchase=purchase,
        domain='bridge-host.example.com',
        token_hash=hash_activation_token(token),
        last_heartbeat_at=timezone.now(),
    )
    return token, inst


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True, LICENSE_REGISTRY_API_ENABLED=True)
def test_ingest_creates_ticket(bridge_registry):
    token, inst = bridge_registry
    client = APIClient()
    remote_id = uuid.uuid4()
    r = client.post(
        '/api/license-registry/v1/tickets/ingest/',
        {
            'remote_ticket_id': str(remote_id),
            'subject': 'Need help',
            'body': 'First message',
            'domain': inst.domain,
            'requester_name': 'Ada',
            'requester_email': 'ada@example.com',
        },
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert r.status_code == 201
    data = r.json()
    assert data['event'] == 'created'
    tk = Ticket.objects.get(pk=data['id'])
    assert tk.registry_installation_id == inst.pk
    assert tk.remote_ticket_id == remote_id
    assert 'Ada' in (tk.bridge_requester_name or '')
    assert TicketMessage.objects.filter(ticket=tk).count() == 1


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True, LICENSE_REGISTRY_API_ENABLED=True)
def test_ingest_appends_same_remote_id(bridge_registry):
    token, inst = bridge_registry
    client = APIClient()
    remote_id = uuid.uuid4()
    client.post(
        '/api/license-registry/v1/tickets/ingest/',
        {
            'remote_ticket_id': str(remote_id),
            'subject': 'Subject',
            'body': 'One',
            'domain': inst.domain,
        },
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    r2 = client.post(
        '/api/license-registry/v1/tickets/ingest/',
        {
            'remote_ticket_id': str(remote_id),
            'body': 'Two',
            'domain': inst.domain,
        },
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert r2.status_code == 200
    assert r2.json()['event'] == 'appended'
    tk = Ticket.objects.get(remote_ticket_id=remote_id, registry_installation=inst)
    assert TicketMessage.objects.filter(ticket=tk).count() == 2


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True, LICENSE_REGISTRY_API_ENABLED=True)
def test_ingest_invalid_token(bridge_registry):
    _token, inst = bridge_registry
    client = APIClient()
    r = client.post(
        '/api/license-registry/v1/tickets/ingest/',
        {
            'remote_ticket_id': str(uuid.uuid4()),
            'subject': 'X',
            'body': 'Y',
            'domain': inst.domain,
        },
        format='json',
        HTTP_AUTHORIZATION='Bearer totally-wrong-token',
    )
    assert r.status_code == 401


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True, LICENSE_REGISTRY_API_ENABLED=True)
def test_ingest_missing_remote_id(bridge_registry):
    token, inst = bridge_registry
    client = APIClient()
    r = client.post(
        '/api/license-registry/v1/tickets/ingest/',
        {'subject': 'X', 'body': 'Y', 'domain': inst.domain},
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert r.status_code == 400


@pytest.mark.django_db
@override_settings(
    DEPLOYMENT_MODE='self_hosted',
    TICKET_OPERATOR_BRIDGE_ENABLED=True,
    LICENSE_GATEWAY_BASE_URL='https://gw.example.com/api/license-registry/v1',
    SCREENGRAM_APP_VERSION='9.9.9',
)
def test_push_new_ticket_if_configured(tenant_a, requester_a):
    LicenseState.objects.all().delete()
    state = LicenseState.get_solo()
    state.activation_token = 'act-token'
    state.activated_domain = 'self.example.com'
    state.save()

    with patch('licensing.client.post_gateway_ticket_ingest') as mock_post:
        from tickets import operator_bridge

        ticket = create_ticket(
            tenant=tenant_a,
            requester=requester_a,
            subject='Local subj',
            body='Local body',
        )
        operator_bridge.push_new_ticket_if_configured(ticket.id)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == 'https://gw.example.com/api/license-registry/v1'
    assert args[1] == 'act-token'
    body = kwargs.get('body') or args[2]
    assert body['remote_ticket_id'] == str(ticket.id)
    assert body['subject'] == 'Local subj'
    assert body['body'] == 'Local body'
    assert body['domain'] == 'self.example.com'


def immediate_on_commit(func, using=None):
    func()


@pytest.mark.django_db
@override_settings(
    DEPLOYMENT_MODE='self_hosted',
    TICKET_OPERATOR_BRIDGE_ENABLED=True,
    LICENSE_GATEWAY_BASE_URL='https://gw.example.com/api/license-registry/v1',
)
@patch('django.db.transaction.on_commit', side_effect=immediate_on_commit)
@patch('licensing.client.post_gateway_ticket_ingest')
def test_create_ticket_triggers_bridge(mock_post, _mock_on_commit, tenant_a, requester_a):
    LicenseState.objects.all().delete()
    state = LicenseState.get_solo()
    state.activation_token = 'act-token'
    state.activated_domain = 'self.example.com'
    state.save()

    create_ticket(
        tenant=tenant_a,
        requester=requester_a,
        subject='S',
        body='B',
    )
    assert mock_post.called


@pytest.mark.django_db
@override_settings(
    DEPLOYMENT_MODE='self_hosted',
    TICKET_OPERATOR_BRIDGE_ENABLED=True,
    LICENSE_GATEWAY_BASE_URL='https://gw.example.com/api/license-registry/v1',
    NOTIFICATION_ENCRYPTION_KEY=Fernet.generate_key(),
)
def test_push_new_ticket_suppressed_skips_ingest(tenant_a, requester_a):
    LicenseState.objects.all().delete()
    state = LicenseState.get_solo()
    state.activation_token = 'act-token'
    state.activated_domain = 'self.example.com'
    state.save()

    with patch('licensing.client.post_gateway_ticket_ingest') as mock_post:
        from tickets import operator_bridge

        ticket = create_ticket(
            tenant=tenant_a,
            requester=requester_a,
            subject='Local subj',
            body='Local body',
        )
        ticket.suppress_operator_bridge_outbound = True
        ticket.save(update_fields=['suppress_operator_bridge_outbound'])
        operator_bridge.push_new_ticket_if_configured(ticket.id)

    mock_post.assert_not_called()


@pytest.mark.django_db
@override_settings(
    DEPLOYMENT_MODE='self_hosted',
    TICKET_OPERATOR_BRIDGE_ENABLED=True,
    MOTHER_TICKET_VIA_GATEWAY=True,
    MOTHER_URL='https://mother.example.com',
    NOTIFICATION_ENCRYPTION_KEY=Fernet.generate_key(),
    LICENSE_GATEWAY_BASE_URL='https://gw.example.com/api/license-registry/v1',
)
def test_mother_gateway_path_skips_license_ingest(tenant_a, requester_a):
    from mother_client.crypto import encrypt_api_key
    from mother_client.models import MotherClientState

    LicenseState.objects.all().delete()
    ls = LicenseState.get_solo()
    ls.activation_token = 'act-token'
    ls.activated_domain = 'self.example.com'
    ls.save()

    mc = MotherClientState.get_solo()
    mc.instance_id = uuid.uuid4()
    mc.api_key_encrypted = encrypt_api_key('instance-secret-key')
    mc.save()

    with patch('mother_client.operator_gateway.post_ticket') as mock_pt:
        mock_pt.return_value = MagicMock(ok=True, status_code=201, text='')
        with patch('licensing.client.post_gateway_ticket_ingest') as mock_ingest:
            from tickets import operator_bridge

            ticket = create_ticket(
                tenant=tenant_a,
                requester=requester_a,
                subject='Gateway subj',
                body='Gateway body',
            )
            operator_bridge.push_new_ticket_if_configured(ticket.id)

        mock_ingest.assert_not_called()
    mock_pt.assert_called_once()
