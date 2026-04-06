# Generated manually — default catalog rows for fresh installs.

from django.db import migrations


def seed_plans(apps, schema_editor):
    PlatformBillingSettings = apps.get_model('saas_platform', 'PlatformBillingSettings')
    SubscriptionPlan = apps.get_model('saas_platform', 'SubscriptionPlan')

    PlatformBillingSettings.objects.get_or_create(
        pk=1,
        defaults={
            'default_free_screen_limit': 1,
            'trial_days_display': 14,
            'checkout_allow_promotion_codes': True,
        },
    )

    defaults = [
        dict(
            key='free',
            label='Free',
            description='Get started with core signage features. Upgrade when you need more screens.',
            kind='free',
            included_screens=None,
            is_unlimited=False,
            stripe_price_id='',
            min_quantity=1,
            display_amount_cents=0,
            sort_order=0,
            is_active=True,
            badge='',
            highlight=False,
        ),
        dict(
            key='bundle_5',
            label='5 screens',
            description='Flat bundle for up to five paired displays — ideal for a small venue or pilot.',
            kind='bundle',
            included_screens=5,
            is_unlimited=False,
            stripe_price_id='',
            min_quantity=1,
            display_amount_cents=None,
            sort_order=10,
            is_active=True,
            badge='Popular',
            highlight=True,
        ),
        dict(
            key='per_screen',
            label='Per screen',
            description='Pay per active screen each month. Scale quantity as you add locations.',
            kind='per_screen',
            included_screens=None,
            is_unlimited=False,
            stripe_price_id='',
            min_quantity=1,
            display_amount_cents=500,
            sort_order=20,
            is_active=True,
            badge='',
            highlight=False,
        ),
        dict(
            key='vip',
            label='VIP',
            description='Unlimited screens for large fleets and rollouts — one predictable subscription.',
            kind='vip',
            included_screens=None,
            is_unlimited=True,
            stripe_price_id='',
            min_quantity=1,
            display_amount_cents=None,
            sort_order=30,
            is_active=True,
            badge='Unlimited',
            highlight=False,
        ),
    ]
    for row in defaults:
        SubscriptionPlan.objects.update_or_create(key=row['key'], defaults=row)


def unseed(apps, schema_editor):
    SubscriptionPlan = apps.get_model('saas_platform', 'SubscriptionPlan')
    SubscriptionPlan.objects.filter(key__in=['free', 'bundle_5', 'per_screen', 'vip']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saas_platform', '0006_pricing_catalog'),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed),
    ]
