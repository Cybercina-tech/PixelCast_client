from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LicenseState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purchase_code", models.CharField(blank=True, default="", max_length=128)),
                ("activated_domain", models.CharField(blank=True, default="", max_length=255)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "license_status",
                    models.CharField(
                        choices=[
                            ("inactive", "Inactive"),
                            ("active", "Active"),
                            ("invalid", "Invalid"),
                            ("grace", "Grace"),
                        ],
                        db_index=True,
                        default="inactive",
                        max_length=20,
                    ),
                ),
                ("last_validation_at", models.DateTimeField(blank=True, null=True)),
                ("last_successful_validation_at", models.DateTimeField(blank=True, null=True)),
                ("grace_until", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("codecanyon_product_id_override", models.CharField(blank=True, default="", max_length=64)),
                ("validation_signature", models.CharField(blank=True, default="", max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "licensing_state",
                "verbose_name": "License State",
                "verbose_name_plural": "License State",
            },
        ),
    ]
