"""Create fixed Tenant + ClientConfig for DEPLOYMENT_MODE=client."""

from __future__ import annotations

from django.utils import timezone
from django.utils.text import slugify

from saas_platform.models import Tenant
from saas_platform.pricing_models import PlatformBillingSettings

from setup.models import ClientConfig


def create_or_get_client_tenant(organization_name: str) -> Tenant:
    """
    Idempotent: if ClientConfig row exists, return its tenant; else create Tenant + ClientConfig.
    """
    existing = ClientConfig.get_solo()
    if existing:
        return existing.tenant

    name = (organization_name or '').strip()[:255]
    if not name:
        raise ValueError('organization_name is required')

    free_limit = PlatformBillingSettings.get_solo().default_free_screen_limit
    base = slugify(name)[:80] or 'organization'
    slug = base
    i = 0
    while Tenant.objects.filter(slug=slug).exists():
        i += 1
        slug = f'{base}-{i}'[:80]

    tenant = Tenant.objects.create(
        name=name,
        slug=slug,
        organization_name_key=name,
        device_limit=free_limit,
    )
    ClientConfig.objects.update_or_create(
        pk=1,
        defaults={
            'tenant': tenant,
            'deployment_mode': 'client',
            'installed_at': timezone.now(),
        },
    )
    return tenant
