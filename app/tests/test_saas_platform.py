"""Tests for minimal Platform API (CodeCanyon client — tenants + license endpoints only)."""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from saas_platform.models import Tenant, TenantAuditLog


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name='Acme Corp', slug='acme')


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenants_list_as_developer(superadmin_user):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 200
    assert 'results' in r.data or isinstance(r.data, list)


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=False)
def test_platform_tenants_forbidden_when_disabled(superadmin_user):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 403


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenants_denied_for_manager(manager_user):
    client = APIClient()
    client.force_authenticate(user=manager_user)
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 403


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenant_create_as_developer(superadmin_user):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.post(
        '/api/platform/tenants/',
        {
            'name': 'Gamma Org',
            'slug': 'gamma-org',
            'subscription_status': 'trialing',
            'plan_name': 'Starter',
            'plan_interval': 'month',
            'device_limit': 25,
        },
        format='json',
    )
    assert r.status_code == 201
    assert r.data['name'] == 'Gamma Org'
    assert r.data['slug'] == 'gamma-org'
    assert Tenant.objects.filter(slug='gamma-org').exists()


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenant_update_as_developer(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.put(
        f'/api/platform/tenants/{tenant.id}/',
        {'name': 'Acme Updated', 'plan_name': 'Pro', 'subscription_status': 'active'},
        format='json',
    )
    assert r.status_code == 200
    assert r.data['name'] == 'Acme Updated'
    tenant.refresh_from_db()
    assert tenant.plan_name == 'Pro'


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenant_delete_as_developer(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.delete(f'/api/platform/tenants/{tenant.id}/')
    assert r.status_code == 200
    assert r.data['status'] == 'deleted'


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenant_create_denied_for_manager(manager_user):
    client = APIClient()
    client.force_authenticate(user=manager_user)
    r = client.post('/api/platform/tenants/', {'name': 'X', 'slug': 'x'}, format='json')
    assert r.status_code == 403


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_tenant_access_lock_and_unlock(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.post(f'/api/platform/tenants/{tenant.id}/access-lock/', {'reason': 'test'}, format='json')
    assert r.status_code == 200
    tenant.refresh_from_db()
    assert tenant.access_locked is True
    r2 = client.post(f'/api/platform/tenants/{tenant.id}/access-unlock/', {}, format='json')
    assert r2.status_code == 200
    tenant.refresh_from_db()
    assert tenant.access_locked is False


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_feature_flags_get(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get(f'/api/platform/tenants/{tenant.id}/feature-flags/')
    assert r.status_code == 200
    assert isinstance(r.data, dict)


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_feature_flags_put_merge(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.put(f'/api/platform/tenants/{tenant.id}/feature-flags/', {'beta_ui': True}, format='json')
    assert r.status_code == 200
    assert r.data.get('beta_ui') is True


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_manual_override_ok(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.post(
        f'/api/platform/tenants/{tenant.id}/manual-override/',
        {'device_limit': 10, 'notes': 'test'},
        format='json',
    )
    assert r.status_code == 200
    tenant.refresh_from_db()
    assert tenant.device_limit == 10


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_tenant_audit_log_endpoint(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    TenantAuditLog.objects.create(tenant=tenant, actor=superadmin_user, action='test', details={})
    r = client.get(f'/api/platform/tenants/{tenant.id}/audit-log/')
    assert r.status_code == 200
    assert isinstance(r.data, list)


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_tenant_license_get_creates_default(superadmin_user, tenant):
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    r = client.get(f'/api/platform/tenants/{tenant.id}/license/')
    assert r.status_code == 200


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_tenant_license_denied_for_manager(manager_user, tenant):
    client = APIClient()
    client.force_authenticate(user=manager_user)
    r = client.get(f'/api/platform/tenants/{tenant.id}/license/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_public_pricing_anonymous():
    client = APIClient()
    r = client.get('/api/public/pricing/')
    assert r.status_code == 200
    assert 'plans' in r.data
    assert 'default_free_screen_limit' in r.data


@pytest.mark.django_db
@override_settings(PLATFORM_SAAS_ENABLED=True)
def test_platform_unauthenticated():
    client = APIClient()
    r = client.get('/api/platform/tenants/')
    assert r.status_code == 401
