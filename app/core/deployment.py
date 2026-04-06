"""
Deployment mode matrix (SaaS vs self-hosted vs hybrid vs client).

Use resolve_effective_platform_saas() from settings; do not duplicate logic in views.
"""

from __future__ import annotations

from typing import Any, Literal

DeploymentMode = Literal['saas', 'self_hosted', 'hybrid', 'client']

VALID_MODES = frozenset({'saas', 'self_hosted', 'hybrid', 'client'})

# Roles exposed in Pixelcast client product (no Developer / platform super-admin in UI)
CLIENT_AVAILABLE_ROLES: tuple[str, ...] = ('Visitor', 'Employee', 'Manager')


def normalize_deployment_mode(raw: str | None) -> DeploymentMode:
    """Return a valid deployment mode; invalid values fall back to hybrid."""
    if not raw:
        return 'hybrid'
    v = str(raw).strip().lower()
    if v in VALID_MODES:
        return v  # type: ignore[return-value]
    return 'hybrid'


def is_client_deployment(deployment_mode: str | None) -> bool:
    return normalize_deployment_mode(deployment_mode) == 'client'


def is_self_hosted_operator_bridge(deployment_mode: str | None) -> bool:
    """Ticket operator bridge: same behavior for dedicated installs and Pixelcast client."""
    mode = normalize_deployment_mode(deployment_mode)
    return mode in ('self_hosted', 'client')


def resolve_effective_platform_saas(deployment_mode: str | None, platform_saas_env_flag: bool) -> bool:
    """
    Effective PLATFORM_SAAS_ENABLED after applying DEPLOYMENT_MODE.

    - self_hosted / client: SaaS platform features are always off (Stripe, tenant admin API mount, etc.).
    - saas: always on (operator runs a SaaS deployment).
    - hybrid: follows PLATFORM_SAAS_ENABLED env (buyer can enable SaaS or stay license-only).
    """
    mode = normalize_deployment_mode(deployment_mode)
    if mode in ('self_hosted', 'client'):
        return False
    if mode == 'saas':
        return True
    return bool(platform_saas_env_flag)


def deployment_public_payload(
    deployment_mode: str | None,
    effective_platform_saas: bool,
    stripe_publishable_key: str = '',
) -> dict[str, Any]:
    """Safe JSON for anonymous clients (SPA routing / feature toggles)."""
    mode = normalize_deployment_mode(deployment_mode)
    is_client = mode == 'client'
    show_platform_routes = not is_client
    return {
        'deployment_mode': mode,
        'platform_saas_enabled': bool(effective_platform_saas),
        'stripe_publishable_key_configured': bool((stripe_publishable_key or '').strip()),
        'is_client': is_client,
        'show_platform_routes': show_platform_routes,
        'available_roles': list(CLIENT_AVAILABLE_ROLES) if is_client else None,
    }
