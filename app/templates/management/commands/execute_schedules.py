"""
Management command to execute scheduled templates on screens.

This command should be run periodically (e.g., via cron) to automatically
execute schedules that are due to run. Uses accurate recurrence calculation
for all schedule types including monthly recurrence.

Usage:
    python manage.py execute_schedules
    python manage.py execute_schedules --dry-run  # Show what would be executed
    python manage.py execute_schedules --schedule-id <uuid>  # Execute specific schedule
    python manage.py execute_schedules --force  # Force execution even if not due
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from templates.models import Schedule
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Execute schedules that are due to run'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be executed without actually executing'
        )
        parser.add_argument(
            '--schedule-id',
            type=str,
            help='Execute a specific schedule by ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution even if schedule is not due'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        schedule_id = options.get('schedule_id')
        force = options.get('force', False)
        
        if schedule_id:
            # Execute specific schedule
            try:
                schedule = Schedule.objects.get(id=schedule_id)
                self._execute_schedule(schedule, dry_run, force)
            except Schedule.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Schedule with ID {schedule_id} not found')
                )
        else:
            # Execute all due schedules
            self.stdout.write('Checking for schedules due to execute...')
            
            # Get all active schedules
            schedules = Schedule.objects.filter(is_active=True)
            
            executed_count = 0
            skipped_count = 0
            error_count = 0
            
            for schedule in schedules:
                try:
                    # Use accurate recurrence calculation
                    is_running = schedule.is_running_now
                    next_run = schedule.next_run()
                    
                    if is_running or force:
                        result = self._execute_schedule(schedule, dry_run, force)
                        if result:
                            executed_count += 1
                        else:
                            error_count += 1
                    else:
                        skipped_count += 1
                        if not dry_run:
                            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'Never'
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Skipped: {schedule.name} (not due to run, next: {next_run_str})'
                                )
                            )
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing schedule {schedule.id}: {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error processing schedule {schedule.name}: {str(e)}'
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary: {executed_count} executed, '
                    f'{skipped_count} skipped, {error_count} errors'
                )
            )
    
    def _execute_schedule(self, schedule, dry_run, force):
        """Execute a single schedule"""
        try:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] Would execute: {schedule.name} '
                        f'(Template: {schedule.template.name}, '
                        f'Screens: {schedule.screens.count()})'
                    )
                )
                return True
            
            self.stdout.write(f'Executing schedule: {schedule.name}...')
            result = schedule.execute_on_screens(force=force)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Executed on {result["screens_succeeded"]} screen(s), '
                        f'failed on {result["screens_failed"]} screen(s)'
                    )
                )
                
                # Show details if there are failures
                if result['screens_failed'] > 0:
                    for detail in result['details']:
                        if detail['status'] in ['failed', 'error', 'skipped']:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  - {detail["screen_name"]}: {detail.get("reason", detail.get("error", "Unknown error"))}'
                                )
                            )
                
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Execution failed: {result["message"]}')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error executing schedule {schedule.name}: {str(e)}')
            )
            return False
