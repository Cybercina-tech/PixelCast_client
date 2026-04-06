from django.utils.text import slugify
from rest_framework import serializers
from django.utils import timezone

from .models import BillingWebhookEvent, Tenant, TenantAuditLog, TenantInvoice
from .usage import billing_alerts_for_tenant, churn_metrics_for_tenant, tenant_health_score


class TenantListSerializer(serializers.ModelSerializer):
    billing_alerts = serializers.SerializerMethodField()
    churn = serializers.SerializerMethodField()
    engagement = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'organization_name_key',
            'stripe_customer_id',
            'stripe_subscription_id',
            'subscription_status',
            'plan_name',
            'plan_interval',
            'device_limit',
            'current_period_end',
            'trial_end',
            'cancel_at_period_end',
            'last_payment_failed_at',
            'payment_failed_count',
            'billing_grace_until',
            'manual_access_until',
            'feature_flags',
            'access_locked',
            'access_lock_reason',
            'access_lock_until',
            'billing_alerts',
            'churn',
            'engagement',
            'health',
            'created_at',
            'updated_at',
        ]

    def _metrics(self, obj):
        cache = getattr(self, '_churn_cache', None)
        if cache is None:
            cache = {}
            setattr(self, '_churn_cache', cache)
        if obj.pk not in cache:
            cache[obj.pk] = churn_metrics_for_tenant(obj)
        return cache[obj.pk]

    def get_billing_alerts(self, obj):
        return billing_alerts_for_tenant(obj)

    def get_churn(self, obj):
        m = self._metrics(obj)
        return {
            'days_since_last_user_activity': m['days_since_last_user_activity'],
            'churn_risk_level': m['churn_risk_level'],
            'flags': m['flags'],
        }

    def get_engagement(self, obj):
        m = self._metrics(obj)
        return {
            'user_count': m['user_count'],
            'screen_count': m['screen_count'],
            'offline_screen_count': m['offline_screen_count'],
        }

    def get_health(self, obj):
        cache = getattr(self, '_health_cache', None)
        if cache is None:
            cache = {}
            setattr(self, '_health_cache', cache)
        if obj.pk not in cache:
            cache[obj.pk] = tenant_health_score(obj)
        return cache[obj.pk]


class TenantDetailSerializer(TenantListSerializer):
    invoices = serializers.SerializerMethodField()
    recent_events = serializers.SerializerMethodField()
    session_metrics = serializers.SerializerMethodField()

    class Meta(TenantListSerializer.Meta):
        fields = TenantListSerializer.Meta.fields + [
            'current_period_start',
            'payment_failed_count',
            'card_expiring_soon',
            'manual_notes',
            'session_metrics',
            'invoices',
            'recent_events',
        ]

    def get_invoices(self, obj):
        qs = obj.invoices.all()[:25]
        return TenantInvoiceSerializer(qs, many=True).data

    def get_recent_events(self, obj):
        qs = obj.webhook_events.all()[:20]
        return BillingWebhookEventSerializer(qs, many=True).data

    def get_session_metrics(self, obj):
        """
        Active session metrics for this tenant:
        - active_session_count: unexpired, non-blacklisted refresh sessions
        - active_user_count: distinct users with at least one active session
        """
        try:
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

            now = timezone.now()
            token_rows = list(
                OutstandingToken.objects.filter(
                    user__tenant=obj,
                    expires_at__gt=now,
                ).values_list('id', 'user_id')
            )
            if not token_rows:
                return {'active_session_count': 0, 'active_user_count': 0}

            token_ids = [row[0] for row in token_rows]
            blacklisted_ids = set(
                BlacklistedToken.objects.filter(token_id__in=token_ids).values_list('token_id', flat=True)
            )
            active_users = set()
            active_sessions = 0
            for token_id, user_id in token_rows:
                if token_id in blacklisted_ids:
                    continue
                active_sessions += 1
                active_users.add(int(user_id))

            return {
                'active_session_count': int(active_sessions),
                'active_user_count': int(len(active_users)),
            }
        except Exception:
            return {'active_session_count': 0, 'active_user_count': 0}


class TenantInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantInvoice
        fields = [
            'stripe_invoice_id',
            'number',
            'amount_due',
            'amount_paid',
            'currency',
            'status',
            'hosted_invoice_url',
            'invoice_pdf',
            'period_start',
            'period_end',
            'created_at',
        ]


class BillingWebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingWebhookEvent
        fields = [
            'stripe_event_id',
            'event_type',
            'processed_ok',
            'error_message',
            'created_at',
        ]


class ManualOverrideSerializer(serializers.Serializer):
    manual_access_until = serializers.DateTimeField(required=False, allow_null=True)
    device_limit = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)


class TenantAuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.SerializerMethodField()

    class Meta:
        model = TenantAuditLog
        fields = ['action', 'details', 'created_at', 'actor_username']

    def get_actor_username(self, obj):
        return obj.actor.username if obj.actor_id else None


class TenantWriteSerializer(serializers.ModelSerializer):
    """Create/update serializer for platform operator tenant management."""

    class Meta:
        model = Tenant
        fields = [
            'name',
            'slug',
            'organization_name_key',
            'subscription_status',
            'plan_name',
            'plan_interval',
            'device_limit',
            'access_locked',
            'access_lock_reason',
            'access_lock_until',
        ]
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
            'organization_name_key': {'required': False, 'allow_blank': True},
            'plan_name': {'required': False, 'allow_blank': True},
            'plan_interval': {'required': False, 'allow_blank': True},
            'device_limit': {'required': False, 'allow_null': True},
            'subscription_status': {'required': False},
            'access_locked': {'required': False},
            'access_lock_reason': {'required': False, 'allow_blank': True},
            'access_lock_until': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        incoming_slug = (attrs.get('slug') or '').strip()
        if incoming_slug:
            attrs['slug'] = incoming_slug
            return attrs

        if self.instance:
            # On update, keep existing slug if caller doesn't supply one.
            return attrs

        name = (attrs.get('name') or '').strip()
        base = slugify(name)[:70] or 'tenant'
        candidate = base
        index = 2
        while Tenant.objects.filter(slug=candidate).exists():
            suffix = f'-{index}'
            candidate = f'{base[: max(1, 80 - len(suffix))]}{suffix}'
            index += 1
        attrs['slug'] = candidate
        return attrs
