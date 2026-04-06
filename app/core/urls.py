"""
URL configuration for core infrastructure endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    AuditLogViewSet,
    SystemBackupViewSet,
    NotificationViewSet,
    NotificationPreferenceViewSet,
    TVBrandViewSet,
)
from core.deploy_views import github_webhook, deployment_status
from core.system_email_views import SystemEmailSettingsView, SystemEmailTestView
from core.support_views import support_tickets

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'backups', SystemBackupViewSet, basename='backup')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preferences')
router.register(r'tv-brands', TVBrandViewSet, basename='tv-brand')

urlpatterns = [
    path('support/tickets/', support_tickets, name='support-tickets'),
    path('', include(router.urls)),
    path('system-email-settings/', SystemEmailSettingsView.as_view(), name='system-email-settings'),
    path('system-email-settings/test/', SystemEmailTestView.as_view(), name='system-email-test'),
    # Deployment webhook endpoints
    path('deploy/webhook/', github_webhook, name='github-webhook'),
    path('deploy/status/', deployment_status, name='deployment-status'),
]
