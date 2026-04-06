"""
Management command to initialize default notification events.

Creates predefined notification events for the PixelCast Signage system.
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationEvent


class Command(BaseCommand):
    help = 'Initialize default notification events'

    def handle(self, *args, **options):
        """Create default notification events"""
        
        events = [
            {
                'event_key': 'screen.offline',
                'description': 'Screen goes offline for more than 5 minutes',
                'severity': 'warning'
            },
            {
                'event_key': 'command.failed',
                'description': 'Command execution failed',
                'severity': 'warning'
            },
            {
                'event_key': 'content.sync_failed',
                'description': 'Content synchronization failed',
                'severity': 'warning'
            },
            {
                'event_key': 'schedule.execution_failed',
                'description': 'Schedule execution failed',
                'severity': 'warning'
            },
            {
                'event_key': 'security.rate_limit_breach',
                'description': 'Rate limit breach detected',
                'severity': 'warning'
            },
            {
                'event_key': 'security.invalid_signature',
                'description': 'Invalid HMAC signature detected',
                'severity': 'critical'
            },
            {
                'event_key': 'security.replay_attempt',
                'description': 'Replay attack attempt detected',
                'severity': 'critical'
            },
            {
                'event_key': 'security.invalid_timestamp',
                'description': 'Invalid timestamp detected',
                'severity': 'warning'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for event_data in events:
            event, created = NotificationEvent.objects.update_or_create(
                event_key=event_data['event_key'],
                defaults={
                    'description': event_data['description'],
                    'severity': event_data['severity'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created event: {event.event_key}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated event: {event.event_key}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )

