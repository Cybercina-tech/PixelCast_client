"""Restrict analytics data for Employee role to org / own screens."""

from __future__ import annotations

from typing import List, Optional

from django.db.models import Q


def employee_accessible_screen_id_strs(user) -> List[str]:
    """UUID strings for screens an Employee may see (same rule as commands queryset)."""
    from signage.models import Screen

    org = (getattr(user, 'organization_name', None) or '').strip()
    q = Q(owner=user)
    if org:
        q |= Q(owner__organization_name=org)
    return [str(x) for x in Screen.objects.filter(q).values_list('id', flat=True)]


def merge_analytics_screen_ids(user, requested: Optional[List[str]]) -> Optional[List[str]]:
    """
    Returns None if no extra restriction (Developer / Manager).
    Otherwise returns allowed id strings (possibly empty). Empty means no accessible screens.
    """
    if not getattr(user, 'is_authenticated', False):
        return None
    if user.is_developer() or user.is_manager():
        return requested
    if not user.is_employee():
        return requested

    allowed = set(employee_accessible_screen_id_strs(user))
    if not allowed:
        return []
    if not requested:
        return list(allowed)
    return [sid for sid in requested if sid in allowed]


def employee_may_view_screen_analytics(user, screen_id_str: str) -> bool:
    if user.is_developer() or user.is_manager():
        return True
    if not user.is_employee():
        return True
    return screen_id_str in set(employee_accessible_screen_id_strs(user))
