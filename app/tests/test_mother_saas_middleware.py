"""Mother SaaS enforcement for DEPLOYMENT_MODE=saas + /api/platform/."""

from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
@override_settings(DEPLOYMENT_MODE='saas', PLATFORM_SAAS_ENABLED=True)
@patch('mother_client.models.MotherClientState.get_solo')
@patch('mother_client.crypto.decrypt_api_key', return_value='instance-key-test')
@patch('mother_client.client.check_feature_allowed', return_value=True)
def test_platform_allowed_when_mother_grants_saas(_mock_check, _mock_decrypt, mock_solo, superadmin_user):
    m = MagicMock()
    m.has_credentials.return_value = True
    m.api_key_encrypted = 'enc'
    mock_solo.return_value = m

    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 200


@pytest.mark.django_db
@override_settings(DEPLOYMENT_MODE='saas', PLATFORM_SAAS_ENABLED=True)
@patch('mother_client.models.MotherClientState.get_solo')
@patch('mother_client.crypto.decrypt_api_key', return_value='instance-key-test')
@patch('mother_client.client.check_feature_allowed', return_value=None)
def test_platform_403_when_mother_unreachable(_mock_check, _mock_decrypt, mock_solo, superadmin_user):
    m = MagicMock()
    m.has_credentials.return_value = True
    m.api_key_encrypted = 'enc'
    mock_solo.return_value = m

    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 403


@pytest.mark.django_db
@override_settings(DEPLOYMENT_MODE='hybrid', PLATFORM_SAAS_ENABLED=True)
def test_middleware_skipped_when_not_saas_mode(superadmin_user):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 200
