"""
Management command to clean up old log entries.

This command removes log entries older than a specified number of days
to prevent database bloat.

Usage:
    python manage.py cleanup_logs --days 90  # Remove logs older than 90 days
    python manage.py cleanup_logs --days 30 --type screen-status  # Remove only screen status logs
    python manage.py cleanup_logs --days 90 --dry-run  # Show what would be deleted
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from log.models import ScreenStatusLog, ContentDownloadLog, CommandExecutionLog


class Command(BaseCommand):
    help = 'Clean up old log entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            required=True,
            help='Delete logs older than this many days'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['screen-status', 'content-download', 'command-execution', 'all'],
            default='all',
            help='Type of logs to clean up (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        log_type = options['type']
        dry_run = options.get('dry_run', False)
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f'Cleaning up logs older than {days} days (before {cutoff_date.date()})...')
        
        total_deleted = 0
        
        if log_type == 'screen-status' or log_type == 'all':
            deleted = self._cleanup_screen_status_logs(cutoff_date, dry_run)
            total_deleted += deleted
        
        if log_type == 'content-download' or log_type == 'all':
            deleted = self._cleanup_content_download_logs(cutoff_date, dry_run)
            total_deleted += deleted
        
        if log_type == 'command-execution' or log_type == 'all':
            deleted = self._cleanup_command_execution_logs(cutoff_date, dry_run)
            total_deleted += deleted
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY RUN] Would delete {total_deleted} log entry(ies)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully deleted {total_deleted} log entry(ies)'
                )
            )
    
    def _cleanup_screen_status_logs(self, cutoff_date, dry_run):
        """Clean up old screen status logs"""
        old_logs = ScreenStatusLog.objects.filter(recorded_at__lt=cutoff_date)
        count = old_logs.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would delete {count} screen status log(s)'
                )
            )
        else:
            old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted {count} screen status log(s)'
                )
            )
        
        return count
    
    def _cleanup_content_download_logs(self, cutoff_date, dry_run):
        """Clean up old content download logs"""
        old_logs = ContentDownloadLog.objects.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would delete {count} content download log(s)'
                )
            )
        else:
            old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted {count} content download log(s)'
                )
            )
        
        return count
    
    def _cleanup_command_execution_logs(self, cutoff_date, dry_run):
        """Clean up old command execution logs"""
        old_logs = CommandExecutionLog.objects.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would delete {count} command execution log(s)'
                )
            )
        else:
            old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted {count} command execution log(s)'
                )
            )
        
        return count
