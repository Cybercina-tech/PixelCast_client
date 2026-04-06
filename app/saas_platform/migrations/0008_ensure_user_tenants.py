# Generated manually — ensure every user has a tenant; rehome legacy slug=default.

from django.db import migrations


def forwards(apps, schema_editor):
    from django.contrib.auth import get_user_model
    from saas_platform.tenant_assignment import ensure_user_tenant, rehome_from_legacy_default

    User = get_user_model()
    for user in User.objects.select_related('tenant').iterator(chunk_size=500):
        ensure_user_tenant(user)
        user.refresh_from_db()
        rehome_from_legacy_default(user)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('saas_platform', '0007_seed_default_subscription_plans'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
