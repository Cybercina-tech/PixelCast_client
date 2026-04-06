# Generated manually for self-hosted → operator ticket bridge

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('licensing', '0005_plan_types_and_local_gateway_sync'),
        ('tickets', '0003_reports_and_telemetry'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='bridge_requester_email',
            field=models.CharField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='ticket',
            name='bridge_requester_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='ticket',
            name='remote_ticket_id',
            field=models.UUIDField(
                blank=True,
                help_text='Ticket UUID on the self-hosted instance (idempotency / replies)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='ticket',
            name='registry_installation',
            field=models.ForeignKey(
                blank=True,
                help_text='Operator registry row when this ticket was ingested from a self-hosted site',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='bridged_tickets',
                to='licensing.licenseregistryinstallation',
            ),
        ),
        migrations.AddConstraint(
            model_name='ticket',
            constraint=models.UniqueConstraint(
                condition=Q(
                    registry_installation__isnull=False,
                    remote_ticket_id__isnull=False,
                ),
                fields=('registry_installation', 'remote_ticket_id'),
                name='tickets_ticket_registry_install_remote_uid',
            ),
        ),
    ]
