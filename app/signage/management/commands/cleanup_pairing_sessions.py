"""
Management command to clean up expired pairing sessions.

This command should be run periodically (e.g., via cron) to mark expired
pairing sessions as 'expired' and optionally delete very old sessions.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from signage.models import PairingSession
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up expired pairing sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-old',
            action='store_true',
            help='Delete pairing sessions older than 7 days (not just mark as expired)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days old sessions must be before deletion (default: 7)',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        delete_old = options['delete_old']
        days = options['days']

        # Mark expired pending sessions as expired
        expired_sessions = PairingSession.objects.filter(
            status='pending',
            expires_at__lt=now
        )

        expired_count = expired_sessions.count()
        if expired_count > 0:
            expired_sessions.update(status='expired')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Marked {expired_count} expired pairing session(s) as expired'
                )
            )

        # Optionally delete very old sessions
        if delete_old:
            cutoff_date = now - timedelta(days=days)
            old_sessions = PairingSession.objects.filter(
                created_at__lt=cutoff_date
            )

            old_count = old_sessions.count()
            if old_count > 0:
                old_sessions.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {old_count} pairing session(s) older than {days} days'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'No pairing sessions older than {days} days found'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS('Pairing session cleanup completed')
        )

