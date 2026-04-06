# Generated manually for tiered RBAC (Developer / Manager / Employee)

from django.db import migrations, models


def forwards_remap_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    mapping = {
        'SuperAdmin': 'Developer',
        'Admin': 'Developer',
        'Manager': 'Manager',
        'Operator': 'Employee',
        'Viewer': 'Employee',
    }
    for old, new in mapping.items():
        User.objects.filter(role=old).update(role=new)
    # Sync Django flags: only Developer is superuser
    for u in User.objects.all():
        if u.role == 'Developer':
            User.objects.filter(pk=u.pk).update(is_superuser=True, is_staff=True)
        else:
            User.objects.filter(pk=u.pk).update(is_superuser=False)
            # Managers use Django admin UI for team: staff True; Employees not staff
            if u.role == 'Manager':
                User.objects.filter(pk=u.pk).update(is_staff=True)
            else:
                User.objects.filter(pk=u.pk).update(is_staff=False)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_remap_roles, noop_reverse),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('Developer', 'Developer'),
                    ('Manager', 'Manager'),
                    ('Employee', 'Employee'),
                ],
                default='Employee',
                help_text='User role in the system',
                max_length=20,
            ),
        ),
    ]
