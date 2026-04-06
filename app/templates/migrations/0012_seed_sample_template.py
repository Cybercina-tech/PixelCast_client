# Generated manually for Visitor onboarding

from django.db import migrations


def seed_sample_template(apps, schema_editor):
    Template = apps.get_model('templates', 'Template')
    User = apps.get_model('accounts', 'User')
    if Template.objects.filter(is_sample=True).exists():
        return
    creator = User.objects.filter(is_superuser=True).first()
    Template.objects.create(
        name='Sample template',
        description='Explore the editor; Visitor accounts cannot save changes.',
        is_sample=True,
        is_active=True,
        created_by=creator,
        config_json={'widgets': []},
    )


def unseed_sample_template(apps, schema_editor):
    Template = apps.get_model('templates', 'Template')
    Template.objects.filter(is_sample=True, name='Sample template').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('templates', '0011_visitor_role_and_template_sample'),
    ]

    operations = [
        migrations.RunPython(seed_sample_template, unseed_sample_template),
    ]
