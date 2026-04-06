import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    """First-class customer account for multi-tenant SaaS operations (Platform admin)."""

    SUBSCRIPTION_STATUS_CHOICES = [
        ('none', 'None'),
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete expired'),
        ('paused', 'Paused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=80, unique=True, db_index=True)
    organization_name_key = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text='Legacy organization_name value used when migrating users into tenants',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    stripe_customer_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, db_index=True)

    subscription_status = models.CharField(
        max_length=32,
        default='none',
        choices=SUBSCRIPTION_STATUS_CHOICES,
    )
    plan_name = models.CharField(max_length=128, blank=True)
    plan_interval = models.CharField(
        max_length=16,
        blank=True,
        help_text='month, year, or empty',
    )

    device_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Null means unlimited')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    last_payment_failed_at = models.DateTimeField(null=True, blank=True)
    payment_failed_count = models.PositiveSmallIntegerField(default=0)
    card_expiring_soon = models.BooleanField(default=False)

    manual_access_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Manual ops override: treat as entitled until this instant',
    )
    manual_notes = models.TextField(blank=True)
    billing_grace_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='After failed payment, allow access until this time (dunning grace)',
    )

    feature_flags = models.JSONField(
        default=dict,
        blank=True,
        help_text='Per-tenant feature toggles (beta / enterprise overrides)',
    )

    access_locked = models.BooleanField(
        default=False,
        help_text='When True, sign-in is blocked for tenant users (Developer control).',
    )
    access_lock_reason = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Optional reason shown in admin tools for lock.',
    )
    access_lock_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional expiration for tenant lock; null means manually unlocked.',
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['stripe_customer_id']),
            models.Index(fields=['subscription_status', 'updated_at']),
        ]

    def __str__(self):
        return self.name

    def is_access_lock_active(self):
        """Return True when access lock is active (supports temporary locks)."""
        if not self.access_locked:
            return False
        if self.access_lock_until and self.access_lock_until <= timezone.now():
            return False
        return True


class BillingWebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=128, db_index=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_events',
    )
    payload_summary = models.JSONField(default=dict)
    processed_ok = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class TenantInvoice(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invoices')
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    number = models.CharField(max_length=64, blank=True)
    amount_due = models.IntegerField(default=0)
    amount_paid = models.IntegerField(default=0)
    currency = models.CharField(max_length=8, default='usd')
    status = models.CharField(max_length=32, db_index=True)
    hosted_invoice_url = models.URLField(blank=True)
    invoice_pdf = models.URLField(blank=True)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class TenantApiKey(models.Model):
    """API key for tenant integrations (hashed at rest)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='api_keys')
    label = models.CharField(max_length=128, blank=True)
    prefix = models.CharField(max_length=16, db_index=True)
    key_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class TenantWebhookEndpoint(models.Model):
    """Customer-owned webhook URL for outbound events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='webhook_endpoints')
    url = models.URLField(max_length=2048)
    signing_secret = models.CharField(max_length=128, blank=True, help_text='HMAC secret (server-generated)')
    event_types = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class PlatformExpense(models.Model):
    """Operational expense tracked by platform operators."""

    CATEGORY_CHOICES = [
        ('hosting', 'Hosting'),
        ('infrastructure', 'Infrastructure'),
        ('tools', 'Tools'),
        ('support', 'Support'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='other')
    amount_cents = models.IntegerField(default=0)
    spent_on = models.DateField()
    tenant = models.ForeignKey(
        Tenant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='expenses',
    )
    notes = models.TextField(blank=True, default='')
    is_recurring = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-spent_on']

    def __str__(self):
        return f'{self.title} ({self.amount_cents}c)'


class TenantAuditLog(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='platform_audit_actions',
    )
    action = models.CharField(max_length=64, db_index=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


from .pricing_models import BillingPromotion, PlatformBillingSettings, SubscriptionPlan  # noqa: F401, E402
