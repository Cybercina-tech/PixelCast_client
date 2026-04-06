"""
Management command to cleanup expired backups.

Usage:
    python manage.py cleanup_backups
"""
from django.core.management.base import BaseCommand
from core.backup import backup_manager


class Command(BaseCommand):
    help = 'Cleanup expired backups based on retention policy'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up expired backups...')

        deleted_count = backup_manager.cleanup_expired_backups()

        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Cleaned up {deleted_count} expired backup(s)'
                )
            )
        else:
            self.stdout.write('No expired backups found.')

