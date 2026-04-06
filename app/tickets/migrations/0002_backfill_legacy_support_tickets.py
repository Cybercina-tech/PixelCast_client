"""Backfill data from core.SupportTicket into tickets.Ticket + TicketMessage."""

from django.db import migrations


def forwards(apps, schema_editor):
    SupportTicket = apps.get_model('core', 'SupportTicket')
    Ticket = apps.get_model('tickets', 'Ticket')
    TicketMessage = apps.get_model('tickets', 'TicketMessage')

    for st in SupportTicket.objects.select_related('user', 'user__tenant').iterator():
        tenant = getattr(st.user, 'tenant', None) if st.user else None
        if not tenant:
            continue

        last_number = (
            Ticket.objects
            .filter(tenant=tenant)
            .order_by('-number')
            .values_list('number', flat=True)
            .first()
        ) or 0

        status_map = {'open': 'open', 'closed': 'closed'}
        ticket = Ticket.objects.create(
            id=st.id,
            tenant=tenant,
            number=last_number + 1,
            subject=st.subject,
            status=status_map.get(st.status, 'open'),
            priority='medium',
            source='web',
            requester=st.user,
            created_at=st.created_at,
            updated_at=st.updated_at,
        )

        TicketMessage.objects.create(
            ticket=ticket,
            author=st.user,
            body=st.body,
            is_internal=False,
            source='web',
            created_at=st.created_at,
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('tickets', '0001_initial'),
        ('core', '0009_saas_completion'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards, elidable=True),
    ]
