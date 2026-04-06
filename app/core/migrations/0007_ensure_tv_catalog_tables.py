from django.db import migrations


def ensure_tv_catalog_tables(apps, schema_editor):
    TVBrand = apps.get_model("core", "TVBrand")
    TVModel = apps.get_model("core", "TVModel")
    existing = schema_editor.connection.introspection.table_names()
    brand_table = TVBrand._meta.db_table
    model_table = TVModel._meta.db_table
    if brand_table not in existing:
        schema_editor.create_model(TVBrand)
    if model_table not in existing:
        schema_editor.create_model(TVModel)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_tv_catalog"),
    ]

    operations = [
        migrations.RunPython(ensure_tv_catalog_tables, migrations.RunPython.noop),
    ]
