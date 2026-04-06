from django.db import migrations


def ensure_notification_preference_table(apps, schema_editor):
    NotificationPreference = apps.get_model("core", "NotificationPreference")
    table_name = NotificationPreference._meta.db_table

    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name in existing_tables:
        return

    schema_editor.create_model(NotificationPreference)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_notificationpreference"),
    ]

    operations = [
        migrations.RunPython(
            ensure_notification_preference_table,
            migrations.RunPython.noop,
        ),
    ]

