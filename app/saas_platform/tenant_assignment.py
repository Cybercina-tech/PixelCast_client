"""Assign every user account to a Tenant (tickets, isolation, billing defaults)."""

from __future__ import annotations

from django.utils.text import slugify

from .models import Tenant
from .pricing_models import PlatformBillingSettings


def _default_device_limit():
    solo = PlatformBillingSettings.get_solo()
    return solo.default_free_screen_limit


def _tenant_for_organization(org: str) -> Tenant:
    free_limit = _default_device_limit()
    slug = slugify(org)[:80] or 'org'
    base = slug
    i = 0
    while Tenant.objects.filter(slug=slug).exclude(organization_name_key=org).exists():
        i += 1
        slug = f'{base}-{i}'[:80]
    tenant, _ = Tenant.objects.get_or_create(
        organization_name_key=org,
        defaults={'name': org[:255], 'slug': slug, 'device_limit': free_limit},
    )
    return tenant


def _tenant_personal(user) -> Tenant:
    free_limit = _default_device_limit()
    key = f'__user__{user.pk}'
    existing = Tenant.objects.filter(organization_name_key=key).first()
    if existing:
        return existing
    name = (
        (getattr(user, 'full_name', None) or '').strip()
        or (getattr(user, 'username', None) or '').strip()
        or getattr(user, 'email', '') or 'Account'
    )[:255]
    uid = str(user.pk).replace('-', '')
    base = (slugify(user.username or '') or 'user')[:40]
    slug = f'{base}-{uid}'[:80]
    n = 0
    while Tenant.objects.filter(slug=slug).exists():
        n += 1
        slug = f'{base}-{uid}-{n}'[:80]
    return Tenant.objects.create(
        name=name,
        slug=slug,
        organization_name_key=key,
        device_limit=free_limit,
    )


def ensure_user_tenant(user) -> None:
    """
    If the user has no tenant, assign one: shared tenant per organization_name,
    or a personal tenant named after the account when organization_name is empty.
    """
    if getattr(user, 'tenant_id', None):
        return
    org = (user.organization_name or '').strip()
    if org:
        tenant = _tenant_for_organization(org)
    else:
        tenant = _tenant_personal(user)
    user.tenant = tenant
    user.save(update_fields=['tenant'])


def assign_tenant_for_new_user(user) -> None:
    """Backward-compatible alias for signup and other create flows."""
    ensure_user_tenant(user)


def rehome_from_legacy_default(user) -> None:
    """
    Move users still on the shared slug=default tenant to the correct tenant:
    organization tenant if organization_name is set, else personal tenant.
    """
    tenant = getattr(user, 'tenant', None)
    if tenant is None and getattr(user, 'tenant_id', None):
        tenant = Tenant.objects.filter(pk=user.tenant_id).first()
    if not tenant or tenant.slug != 'default':
        return
    org = (user.organization_name or '').strip()
    if org:
        new_tenant = _tenant_for_organization(org)
    else:
        new_tenant = _tenant_personal(user)
    if new_tenant.pk != tenant.pk:
        user.tenant = new_tenant
        user.save(update_fields=['tenant'])
