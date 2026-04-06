"""
Management command to execute pending commands.

This command should be run periodically (e.g., via cron) to automatically
execute pending commands on online screens.

Usage:
    python manage.py execute_pending_commands
    python manage.py execute_pending_commands --screen-id <uuid>  # Execute for specific screen
    python manage.py execute_pending_commands --limit 10  # Limit number of commands
    python manage.py execute_pending_commands --dry-run  # Show what would be executed
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from commands.models import Command


class Command(BaseCommand):
    help = 'Execute pending commands on online screens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--screen-id',
            type=str,
            help='Execute commands for a specific screen only'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of commands to execute (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be executed without actually executing'
        )

    def handle(self, *args, **options):
        screen_id = options.get('screen_id')
        limit = options.get('limit', 50)
        dry_run = options.get('dry_run', False)
        
        if screen_id:
            # Execute commands for specific screen
            from signage.models import Screen
            try:
                screen = Screen.objects.get(id=screen_id)
                self.stdout.write(f'Executing commands for screen: {screen.name}')
                commands = Command.get_executable_commands(screen=screen, limit=limit)
            except Screen.DoesNotExist:
                raise CommandError(f'Screen with ID {screen_id} not found')
        else:
            # Execute commands for all online screens
            self.stdout.write('Executing pending commands for all online screens...')
            commands = Command.get_executable_commands(limit=limit)
        
        executed_count = 0
        success_count = 0
        failed_count = 0
        
        for command in commands:
            executed_count += 1
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] Would execute: {command.name or command.get_type_display()} '
                        f'on screen {command.screen.name} (Priority: {command.priority})'
                    )
                )
            else:
                try:
                    self.stdout.write(
                        f'Executing command: {command.name or command.get_type_display()} '
                        f'on screen {command.screen.name}...'
                    )
                    
                    success = command.execute()
                    
                    if success:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Command executed successfully'
                            )
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Command execution failed: {command.error_message or "Unknown error"}'
                            )
                        )
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error executing command: {str(e)}'
                        )
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY RUN] Would execute {executed_count} command(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary: {executed_count} executed, '
                    f'{success_count} succeeded, {failed_count} failed'
                )
            )
