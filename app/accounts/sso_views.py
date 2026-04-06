"""Enterprise SSO — extension points (OIDC/SAML adapters to be wired per deployment)."""

from __future__ import annotations

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def sso_providers_public(request):
    """Advertise which SSO modes are available (none until IdP credentials are configured)."""
    enabled = bool(getattr(settings, 'SSO_ENABLED', False))
    return Response(
        {
            'sso_enabled': enabled,
            'providers': [],
            'message': 'Configure SSO_ENABLED and IdP credentials to enable Google/Azure sign-in.',
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sso_account_link_status(request):
    """Whether the current user is linked to an SSO subject."""
    u = request.user
    return Response(
        {
            'sso_provider': getattr(u, 'sso_provider', '') or '',
            'sso_linked': bool(getattr(u, 'sso_subject', '') or ''),
        }
    )
