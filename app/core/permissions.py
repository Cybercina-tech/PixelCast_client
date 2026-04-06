"""DRF permissions for core infrastructure (avoid importing saas_platform from core)."""

from django.conf import settings
from rest_framework.permissions import BasePermission

from core.deployment import is_client_deployment


class IsDeveloper(BasePermission):
    """Matches platform super-admin: Developer role or Django superuser."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_developer())


class IsDeveloperPlatformAccess(IsDeveloper):
    """
    Deny in DEPLOYMENT_MODE=client so operator-only endpoints stay closed even if URL wiring changes.
    """

    def has_permission(self, request, view):
        if is_client_deployment(getattr(settings, 'DEPLOYMENT_MODE', None)):
            return False
        return super().has_permission(request, view)
