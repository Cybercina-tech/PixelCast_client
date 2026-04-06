"""Self-hosted plan tiers (CodeCanyon Basic vs SaaS) and feature snapshots for the license gateway."""

from __future__ import annotations

PLAN_BASIC = "basic"
PLAN_SAAS = "saas"

# Keys align with operator / client feature gating expectations.
_FEATURES_BASIC: dict[str, bool] = {
    "screens": True,
    "templates": True,
    "scheduling": True,
    "roles_manager_and_below": True,
    "super_admin": False,
    "saas_platform": False,
    "multi_tenant": False,
    "stripe_billing": False,
}

_FEATURES_SAAS: dict[str, bool] = {k: True for k in _FEATURES_BASIC}


def normalize_plan_type(value: str | None) -> str:
    t = (value or "").strip().lower()
    return t if t in (PLAN_BASIC, PLAN_SAAS) else ""


def features_for_plan(plan_type: str) -> dict[str, bool]:
    if normalize_plan_type(plan_type) == PLAN_BASIC:
        return dict(_FEATURES_BASIC)
    return dict(_FEATURES_SAAS)


def features_snapshot_list(plan_type: str) -> list[str]:
    d = features_for_plan(plan_type)
    return sorted(k for k, v in d.items() if v)
