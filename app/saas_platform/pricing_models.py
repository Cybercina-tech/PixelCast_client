"""Subscription catalog and platform billing defaults (SaaS)."""

from __future__ import annotations

from django.db import models


class PlatformBillingSettings(models.Model):
    """Singleton (pk=1) — defaults for free tier and checkout behavior."""

    default_free_screen_limit = models.PositiveIntegerField(
        default=1,
        help_text='New SaaS tenants get this device_limit until they subscribe.',
    )
    trial_days_display = models.PositiveSmallIntegerField(
        default=14,
        help_text='Shown on marketing pages (trial length is configured in Stripe).',
    )
    checkout_allow_promotion_codes = models.BooleanField(
        default=True,
        help_text='Allow customers to enter Stripe promotion codes at Checkout.',
    )

    class Meta:
        verbose_name = 'Platform billing settings'
        verbose_name_plural = 'Platform billing settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'default_free_screen_limit': 1,
                'trial_days_display': 14,
                'checkout_allow_promotion_codes': True,
            },
        )
        return obj


class SubscriptionPlan(models.Model):
    """Sellable / display plan row; paid plans reference a Stripe Price id."""

    KIND_FREE = 'free'
    KIND_BUNDLE = 'bundle'
    KIND_PER_SCREEN = 'per_screen'
    KIND_VIP = 'vip'
    KIND_CHOICES = [
        (KIND_FREE, 'Free'),
        (KIND_BUNDLE, 'Bundle (fixed screens)'),
        (KIND_PER_SCREEN, 'Per screen'),
        (KIND_VIP, 'VIP (unlimited screens)'),
    ]

    key = models.SlugField(max_length=64, unique=True, db_index=True)
    label = models.CharField(max_length=128)
    description = models.TextField(blank=True, default='')
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)

    included_screens = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='For bundle: e.g. 5. Null for per_screen/vip/free.',
    )
    is_unlimited = models.BooleanField(
        default=False,
        help_text='True for VIP (device_limit=null on tenant).',
    )

    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Stripe Price id (recurring). Empty for free tier.',
    )
    min_quantity = models.PositiveIntegerField(
        default=1,
        help_text='Minimum seats/screens for per_screen checkout.',
    )

    display_amount_cents = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Optional marketing display (e.g. base price); actual charge is Stripe.',
    )
    currency = models.CharField(max_length=8, default='usd')

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    badge = models.CharField(max_length=64, blank=True, default='')
    highlight = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'key']

    def __str__(self):
        return f'{self.label} ({self.key})'


class BillingPromotion(models.Model):
    """Optional pre-configured Stripe promotion code for Checkout."""

    label = models.CharField(max_length=128)
    stripe_promotion_code_id = models.CharField(
        max_length=255,
        help_text='Stripe Promotion Code id (promo_...)',
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'label']

    def __str__(self):
        return self.label
