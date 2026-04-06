"""
Management command to check screen heartbeats and mark offline screens.

This command should be run periodically (e.g., via cron) to automatically
mark screens as offline if they haven't sent a heartbeat within the timeout period.

Usage:
    python manage.py check_heartbeats
    python manage.py check_heartbeats --timeout 10  # 10 minutes timeout
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from signage.models import Screen


class Command(BaseCommand):
    help = 'Check screen heartbeats and mark offline screens that have missed heartbeats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Heartbeat timeout in minutes (default: 5)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually marking screens offline'
        )

    def handle(self, *args, **options):
        timeout_minutes = options['timeout']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Checking heartbeats with {timeout_minutes} minute timeout...')
        
        # Get all online screens
        online_screens = Screen.objects.filter(is_online=True)
        
        marked_offline_count = 0
        checked_count = 0
        
        for screen in online_screens:
            checked_count += 1
            
            if screen.is_heartbeat_stale(timeout_minutes=timeout_minutes):
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Would mark offline: {screen.name} '
                            f'(last heartbeat: {screen.last_heartbeat_at})'
                        )
                    )
                else:
                    screen.mark_offline()
                    self.stdout.write(
                        self.style.WARNING(
                            f'Marked offline: {screen.name} '
                            f'(last heartbeat: {screen.last_heartbeat_at})'
                        )
                    )
                marked_offline_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] Checked {checked_count} screens. '
                    f'Would mark {marked_offline_count} screens offline.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Checked {checked_count} screens. '
                    f'Marked {marked_offline_count} screens offline.'
                )
            )
