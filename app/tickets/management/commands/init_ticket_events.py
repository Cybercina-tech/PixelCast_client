"""Seed notification events used by the ticket system."""
from django.core.management.base import BaseCommand
from notifications.models import NotificationEvent


TICKET_EVENTS = [
    {'event_key': 'ticket.created', 'description': 'New ticket submitted', 'severity': 'info'},
    {'event_key': 'ticket.assigned', 'description': 'Ticket assigned to an agent', 'severity': 'info'},
    {'event_key': 'ticket.reply_received', 'description': 'New reply on a ticket', 'severity': 'info'},
    {'event_key': 'ticket.sla_warning', 'description': 'SLA approaching deadline', 'severity': 'warning'},
    {'event_key': 'ticket.sla_breached', 'description': 'SLA deadline exceeded', 'severity': 'critical'},
    {'event_key': 'ticket.csat_submitted', 'description': 'Customer satisfaction rating submitted', 'severity': 'info'},
]


class Command(BaseCommand):
    help = 'Create or update notification events for the ticket system'

    def handle(self, *args, **options):
        for ev in TICKET_EVENTS:
            obj, created = NotificationEvent.objects.update_or_create(
                event_key=ev['event_key'],
                defaults={
                    'description': ev['description'],
                    'severity': ev['severity'],
                    'is_active': True,
                },
            )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{verb} event: {obj.event_key}'))
