from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_notification_core_notifi_user_id_f286cd_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('screen_offline', models.BooleanField(default=True, help_text='Notify when a screen goes offline')),
                ('template_push', models.BooleanField(default=True, help_text='Notify when template push succeeds')),
                ('system_updates', models.BooleanField(default=False, help_text='Notify about system updates')),
                ('email_enabled', models.BooleanField(default=False, help_text='Enable email delivery for notifications')),
                ('notification_email', models.EmailField(blank=True, default='', help_text='Destination email for notifications when email delivery is enabled', max_length=254)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(help_text='User that owns these notification preferences', on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification Preference',
                'verbose_name_plural': 'Notification Preferences',
                'db_table': 'core_notification_preference',
            },
        ),
    ]
