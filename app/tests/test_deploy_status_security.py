"""Tests for deployment status endpoint access control."""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_deployment_status_forbidden_when_secret_unset():
    client = APIClient()
    r = client.get('/api/core/deploy/status/')
    assert r.status_code == 403


@pytest.mark.django_db
@override_settings(DEPLOYMENT_STATUS_SECRET='unit-test-deploy-secret')
def test_deployment_status_requires_matching_header():
    client = APIClient()
    assert client.get('/api/core/deploy/status/').status_code == 403
    assert (
        client.get(
            '/api/core/deploy/status/',
            HTTP_X_DEPLOYMENT_STATUS_SECRET='wrong',
        ).status_code
        == 403
    )
    r = client.get(
        '/api/core/deploy/status/',
        HTTP_X_DEPLOYMENT_STATUS_SECRET='unit-test-deploy-secret',
    )
    assert r.status_code == 200
