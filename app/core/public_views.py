"""Public (unauthenticated) JSON endpoints for SPA / clients."""

from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.deployment import deployment_public_payload


@require_GET
def public_deployment(request):
    """
    Deployment flags for routing and feature toggles (no secrets).
    """
    payload = deployment_public_payload(
        getattr(settings, 'DEPLOYMENT_MODE', 'hybrid'),
        getattr(settings, 'PLATFORM_SAAS_ENABLED', False),
        getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '') or '',
    )
    return JsonResponse(payload)


@require_GET
def public_config(request):
    """Alias for SPA: same payload as public deployment (GET /api/config/)."""
    return public_deployment(request)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_pricing(request):
    """
    GET /api/public/pricing/ — active plans + defaults (no secrets).
    Kept for SPA compatibility; Stripe checkout/catalog UI is not shipped in CodeCanyon client.
    """
    from saas_platform.pricing_models import PlatformBillingSettings, SubscriptionPlan

    solo = PlatformBillingSettings.get_solo()
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'key')
    plans_data = [
        {
            'key': p.key,
            'label': p.label,
            'description': p.description,
            'kind': p.kind,
            'included_screens': p.included_screens,
            'is_unlimited': p.is_unlimited,
            'stripe_price_id': p.stripe_price_id,
            'min_quantity': p.min_quantity,
            'display_amount_cents': p.display_amount_cents,
            'currency': p.currency,
            'sort_order': p.sort_order,
            'is_active': p.is_active,
            'badge': p.badge,
            'highlight': p.highlight,
        }
        for p in plans
    ]
    return Response(
        {
            'plans': plans_data,
            'default_free_screen_limit': solo.default_free_screen_limit,
            'trial_days_display': solo.trial_days_display,
            'saas_enabled': bool(getattr(settings, 'PLATFORM_SAAS_ENABLED', False)),
        }
    )
