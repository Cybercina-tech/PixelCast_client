"""Ticket URL configuration — requester surface."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import RequesterTicketViewSet
from .inbound_views import inbound_email_webhook

router = DefaultRouter()
router.register(r'', RequesterTicketViewSet, basename='ticket')

urlpatterns = [
    path('inbound-email/', inbound_email_webhook, name='ticket-inbound-email'),
] + router.urls
