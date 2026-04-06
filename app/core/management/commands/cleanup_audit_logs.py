"""
Management command to archive old audit logs (immutable — never hard-deleted).

Usage:
    python manage.py cleanup_audit_logs --days=365
    python manage.py cleanup_audit_logs --days=365 --hard-delete  # only if legally required
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import AuditLog
from django.conf import settings


class Command(BaseCommand):
    help = 'Archive old audit logs (soft-archive by default; immutable retention)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Archive logs older than N days (default: from AUDIT_LOGGING config)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be archived without actually archiving'
        )
        parser.add_argument(
            '--hard-delete',
            action='store_true',
            help='Hard-delete instead of archive (requires explicit opt-in for compliance)',
        )

    def handle(self, *args, **options):
        days = options.get('days')
        if not days:
            audit_config = getattr(settings, 'AUDIT_LOGGING', {})
            days = audit_config.get('RETENTION_DAYS', 365)

        dry_run = options['dry_run']
        hard_delete = options.get('hard_delete', False)

        cutoff_date = timezone.now() - timedelta(days=days)

        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date, is_archived=False)
        count = old_logs.count()

        verb = 'hard-delete' if hard_delete else 'archive'

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would {verb} {count} audit log(s) older than {days} days'
                )
            )
            return

        if count == 0:
            self.stdout.write('No audit logs to process.')
            return

        if hard_delete:
            deleted_count, _ = old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Hard-deleted {deleted_count} audit log(s) older than {days} days')
            )
        else:
            archived_count = old_logs.update(is_archived=True)
            self.stdout.write(
                self.style.SUCCESS(f'Archived {archived_count} audit log(s) older than {days} days')
            )

