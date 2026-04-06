# Generated manually — assign each user to a Tenant from organization_name.

from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Tenant = apps.get_model('saas_platform', 'Tenant')

    default, _ = Tenant.objects.get_or_create(
        slug='default',
        defaults={'name': 'Default', 'organization_name_key': ''},
    )

    def get_or_create_tenant(org: str):
        slug_base = slugify(org)[:80] or 'org'
        slug = slug_base
        n = 0
        while True:
            existing = Tenant.objects.filter(slug=slug).first()
            if existing is None:
                return Tenant.objects.create(name=org, slug=slug, organization_name_key=org)
            if existing.organization_name_key == org:
                return existing
            n += 1
            slug = f'{slug_base}-{n}'[:80]

    for u in User.objects.all():
        org = (u.organization_name or '').strip()
        if not org:
            tid = default.id
        else:
            tid = get_or_create_tenant(org).id
        if u.tenant_id != tid:
            u.tenant_id = tid
            u.save(update_fields=['tenant_id'])


def backwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.all().update(tenant_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('saas_platform', '0001_initial'),
        ('accounts', '0004_user_tenant'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
