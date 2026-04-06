"""Minimal platform API for CodeCanyon client — tenants + license tooling only."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from licensing.registry_admin_views import (
    self_hosted_license_detail,
    self_hosted_license_heartbeats,
    self_hosted_license_list,
    self_hosted_license_reactivate,
    self_hosted_license_suspicious,
    self_hosted_license_suspend,
)

from .license_views import tenant_license_enforcement_logs, tenant_license_view
from .views import TenantViewSet

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='platform-tenant')

urlpatterns = [
    path('tenants/<uuid:tenant_id>/license/', tenant_license_view, name='platform-tenant-license'),
    path(
        'tenants/<uuid:tenant_id>/license/enforcement-logs/',
        tenant_license_enforcement_logs,
        name='platform-tenant-license-logs',
    ),
    path('self-hosted-licenses/', self_hosted_license_list, name='platform-self-hosted-licenses'),
    path('self-hosted-licenses/<uuid:pk>/', self_hosted_license_detail, name='platform-self-hosted-license-detail'),
    path('self-hosted-licenses/<uuid:pk>/suspend/', self_hosted_license_suspend, name='platform-self-hosted-license-suspend'),
    path('self-hosted-licenses/<uuid:pk>/reactivate/', self_hosted_license_reactivate, name='platform-self-hosted-license-reactivate'),
    path('self-hosted-licenses/<uuid:pk>/suspicious/', self_hosted_license_suspicious, name='platform-self-hosted-license-suspicious'),
    path('self-hosted-licenses/<uuid:pk>/heartbeats/', self_hosted_license_heartbeats, name='platform-self-hosted-license-heartbeats'),
] + router.urls
