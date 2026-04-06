from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_ensure_notification_preference_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='TVBrand',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=120, unique=True)),
                ('slug', models.SlugField(db_index=True, max_length=140, unique=True)),
                ('logo_text', models.CharField(default='TV', help_text='Short brand mark rendered as logo fallback in UI', max_length=32)),
                ('logo_url', models.URLField(blank=True, default='')),
                ('description', models.TextField(blank=True, default='')),
                ('sort_order', models.PositiveIntegerField(db_index=True, default=0)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'TV Brand',
                'verbose_name_plural': 'TV Brands',
                'db_table': 'core_tv_brand',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='TVModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=180)),
                ('model_code', models.CharField(blank=True, default='', max_length=120)),
                ('series', models.CharField(blank=True, default='', max_length=120)),
                ('platform', models.CharField(choices=[('android_tv', 'Android TV'), ('google_tv', 'Google TV'), ('tizen', 'Tizen'), ('webos', 'webOS'), ('android_soc', 'Android SoC'), ('other', 'Other')], db_index=True, default='other', max_length=32)),
                ('operation_time', models.CharField(choices=[('16_7', '16/7'), ('18_7', '18/7'), ('24_7', '24/7')], db_index=True, default='16_7', max_length=16)),
                ('brightness_class', models.CharField(choices=[('indoor', 'Indoor (300-350 nits)'), ('high_bright', 'High Bright (500-700 nits)'), ('window', 'Window Facing (2500+ nits)')], db_index=True, default='indoor', max_length=32)),
                ('control_ports', models.JSONField(blank=True, default=list)),
                ('notes', models.TextField(blank=True, default='')),
                ('is_download_enabled', models.BooleanField(default=False)),
                ('download_url', models.URLField(blank=True, null=True)),
                ('sort_order', models.PositiveIntegerField(db_index=True, default=0)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='models', to='core.tvbrand')),
            ],
            options={
                'verbose_name': 'TV Model',
                'verbose_name_plural': 'TV Models',
                'db_table': 'core_tv_model',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='tvmodel',
            index=models.Index(fields=['brand', 'is_active'], name='core_tv_mod_brand_i_d81b0e_idx'),
        ),
        migrations.AddIndex(
            model_name='tvmodel',
            index=models.Index(fields=['platform', 'operation_time'], name='core_tv_mod_platfor_12e6ca_idx'),
        ),
        migrations.AddIndex(
            model_name='tvmodel',
            index=models.Index(fields=['brightness_class', 'operation_time'], name='core_tv_mod_brightn_1de33b_idx'),
        ),
        migrations.AddConstraint(
            model_name='tvmodel',
            constraint=models.UniqueConstraint(fields=('brand', 'name'), name='core_tv_model_brand_name_unique'),
        ),
    ]
