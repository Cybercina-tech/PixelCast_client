from django.db import migrations
from django.utils import timezone


def _calc_priority(start_time):
    if not start_time:
        return 0
    value = start_time
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return int(value.timestamp())


def forward_set_priority(apps, schema_editor):
    Schedule = apps.get_model('templates', 'Schedule')
    for schedule in Schedule.objects.all().only('id', 'start_time', 'priority'):
        schedule.priority = _calc_priority(schedule.start_time)
        schedule.save(update_fields=['priority'])


def backward_noop(apps, schema_editor):
    # Priority is now generated automatically; no safe rollback value.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('templates', '0002_make_content_widget_nullable_and_add_metadata'),
    ]

    operations = [
        migrations.RunPython(forward_set_priority, backward_noop),
    ]
