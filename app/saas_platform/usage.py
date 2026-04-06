"""Usage and churn signals for tenants."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Max, Q
from django.utils import timezone

from signage.models import Screen


def billing_alerts_for_tenant(tenant) -> list[str]:
    alerts: list[str] = []
    if tenant.last_payment_failed_at:
        alerts.append('payment_failed')
    if tenant.card_expiring_soon:
        alerts.append('card_expiring')
    now = timezone.now()
    if tenant.trial_end and tenant.trial_end > now and (tenant.trial_end - now).total_seconds() <= 2 * 86400:
        alerts.append('trial_ending_soon')
    if tenant.cancel_at_period_end and tenant.subscription_status == 'active':
        alerts.append('cancel_at_period_end')
    if tenant.subscription_status == 'past_due':
        alerts.append('past_due')
    if tenant.subscription_status == 'unpaid':
        alerts.append('unpaid')
    return alerts


def churn_metrics_for_tenant(tenant) -> dict:
    users = tenant.users.all()
    user_count = users.count()
    last_seen = users.aggregate(m=Max('last_seen'))['m']
    days_since = None
    if last_seen:
        days_since = (timezone.now() - last_seen).days
    threshold = timezone.now() - timedelta(minutes=30)
    screens = Screen.objects.filter(owner__tenant=tenant)
    screen_count = screens.count()
    offline = screens.filter(
        Q(last_heartbeat_at__isnull=True) | Q(last_heartbeat_at__lt=threshold)
    ).count()
    flags = []
    if days_since is not None and days_since >= 30:
        flags.append('inactive_login_30d')
    if screen_count > 0 and offline == screen_count:
        flags.append('all_screens_offline')
    if days_since is not None and days_since >= 14:
        flags.append('inactive_login_14d')

    risk = 'low'
    if len(flags) >= 2:
        risk = 'high'
    elif len(flags) == 1:
        risk = 'medium'

    return {
        'user_count': user_count,
        'screen_count': screen_count,
        'offline_screen_count': offline,
        'days_since_last_user_activity': days_since,
        'churn_risk_level': risk,
        'flags': flags,
    }


def tenant_health_score(tenant) -> dict:
    """Map churn signals to a 0-100 score for platform overview (stub-friendly aggregate)."""
    m = churn_metrics_for_tenant(tenant)
    risk = m.get('churn_risk_level', 'low')
    if risk == 'high':
        score = 25
    elif risk == 'medium':
        score = 55
    else:
        score = 85
    return {'score': score, 'churn_risk_level': risk, **m}
