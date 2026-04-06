from django.db import migrations


def ensure_qr_tables(apps, schema_editor):
    QRActionLink = apps.get_model("templates", "QRActionLink")
    QRActionRule = apps.get_model("templates", "QRActionRule")
    QRScanEvent = apps.get_model("templates", "QRScanEvent")

    existing_tables = set(schema_editor.connection.introspection.table_names())

    # Respect FK dependencies when creating missing tables.
    if QRActionLink._meta.db_table not in existing_tables:
        schema_editor.create_model(QRActionLink)
        existing_tables.add(QRActionLink._meta.db_table)

    if QRActionRule._meta.db_table not in existing_tables:
        schema_editor.create_model(QRActionRule)
        existing_tables.add(QRActionRule._meta.db_table)

    if QRScanEvent._meta.db_table not in existing_tables:
        schema_editor.create_model(QRScanEvent)


class Migration(migrations.Migration):
    dependencies = [
        ("templates", "0008_widget_add_countdown_type"),
    ]

    operations = [
        migrations.RunPython(
            ensure_qr_tables,
            migrations.RunPython.noop,
        ),
    ]
