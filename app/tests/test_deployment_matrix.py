"""Deployment mode matrix and public deployment endpoint."""

import pytest
from django.test import Client, override_settings

from core.deployment import (
    deployment_public_payload,
    normalize_deployment_mode,
    resolve_effective_platform_saas,
)


@pytest.mark.django_db
def test_resolve_effective_platform_saas():
    assert resolve_effective_platform_saas('self_hosted', True) is False
    assert resolve_effective_platform_saas('self_hosted', False) is False
    assert resolve_effective_platform_saas('client', True) is False
    assert resolve_effective_platform_saas('client', False) is False
    assert resolve_effective_platform_saas('saas', False) is True
    assert resolve_effective_platform_saas('saas', True) is True
    assert resolve_effective_platform_saas('hybrid', True) is True
    assert resolve_effective_platform_saas('hybrid', False) is False


def test_normalize_deployment_mode_invalid():
    assert normalize_deployment_mode('bogus') == 'hybrid'


def test_normalize_deployment_mode_client():
    assert normalize_deployment_mode('client') == 'client'


def test_public_deployment_endpoint():
    client = Client()
    r = client.get('/api/public/deployment/')
    assert r.status_code == 200
    data = r.json()
    assert 'deployment_mode' in data
    assert 'platform_saas_enabled' in data
    assert 'stripe_publishable_key_configured' in data


def test_public_config_alias_matches_deployment():
    client = Client()
    a = client.get('/api/public/deployment/').json()
    b = client.get('/api/config/').json()
    assert a == b


@override_settings(DEPLOYMENT_MODE='saas', PLATFORM_SAAS_ENABLED=True)
def test_public_deployment_saas_mode():
    client = Client()
    r = client.get('/api/public/deployment/')
    assert r.json()['deployment_mode'] == 'saas'
    assert r.json()['platform_saas_enabled'] is True


def test_deployment_public_payload_shape():
    p = deployment_public_payload('hybrid', True, 'pk_test_123')
    assert p['deployment_mode'] == 'hybrid'
    assert p['platform_saas_enabled'] is True
    assert p['stripe_publishable_key_configured'] is True
    assert p['is_client'] is False
    assert p['show_platform_routes'] is True
    assert p['available_roles'] is None

    pc = deployment_public_payload('client', False, '')
    assert pc['is_client'] is True
    assert pc['show_platform_routes'] is False
    assert pc['available_roles'] == ['Visitor', 'Employee', 'Manager']
