"""Ticket URL configuration — platform / super-admin surface."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .analytics_views import agent_performance, ticket_analytics, ticket_export_csv
from .views import (
    PlatformCannedResponseViewSet, PlatformQueueViewSet,
    PlatformRoleProfileViewSet, PlatformRoutingRuleViewSet,
    PlatformSlaPolicyViewSet, PlatformTagViewSet,
    PlatformTicketViewSet,
)

router = DefaultRouter()
router.register(r'queue', PlatformTicketViewSet, basename='platform-ticket')
router.register(r'queues', PlatformQueueViewSet, basename='platform-ticket-queue')
router.register(r'sla-policies', PlatformSlaPolicyViewSet, basename='platform-ticket-sla-policy')
router.register(r'routing-rules', PlatformRoutingRuleViewSet, basename='platform-ticket-routing-rule')
router.register(r'canned-responses', PlatformCannedResponseViewSet, basename='platform-ticket-canned')
router.register(r'tags', PlatformTagViewSet, basename='platform-ticket-tag')
router.register(r'roles', PlatformRoleProfileViewSet, basename='platform-ticket-role')

urlpatterns = [
    path('analytics/', ticket_analytics, name='platform-ticket-analytics'),
    path('export.csv', ticket_export_csv, name='platform-ticket-export-csv'),
    path('agent-performance/', agent_performance, name='platform-ticket-agent-performance'),
] + router.urls
