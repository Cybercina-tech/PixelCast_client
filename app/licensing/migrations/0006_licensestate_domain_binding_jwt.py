from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("licensing", "0005_plan_types_and_local_gateway_sync"),
    ]

    operations = [
        migrations.AddField(
            model_name="licensestate",
            name="domain_binding_jwt",
            field=models.TextField(blank=True, default=""),
        ),
    ]
