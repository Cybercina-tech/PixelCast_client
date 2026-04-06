"""
Management command to run system backups.

Usage:
    python manage.py run_backup --type=database
    python manage.py run_backup --type=media
    python manage.py run_backup --type=full
"""
from django.core.management.base import BaseCommand, CommandError
from core.backup import backup_manager
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Run system backups (database, media, or full)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['database', 'media', 'full'],
            default='database',
            help='Type of backup to run'
        )
        parser.add_argument(
            '--compression',
            action='store_true',
            default=True,
            help='Enable compression (default: True)'
        )
        parser.add_argument(
            '--no-compression',
            action='store_false',
            dest='compression',
            help='Disable compression'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to attribute backup to (optional)'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        compression = options['compression']
        user_id = options.get('user_id')

        user = None
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise CommandError(f'User with ID {user_id} does not exist')

        self.stdout.write(f'Starting {backup_type} backup...')

        try:
            if backup_type == 'database':
                backup = backup_manager.backup_database(
                    include_media=False,
                    compression=compression,
                    user=user
                )
            elif backup_type == 'media':
                backup = backup_manager.backup_media(
                    compression=compression,
                    user=user
                )
            elif backup_type == 'full':
                backup = backup_manager.backup_full(
                    compression=compression,
                    user=user
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Backup completed successfully!\n'
                    f'  Status: {backup.status}\n'
                    f'  File: {backup.file_path}\n'
                    f'  Size: {backup.file_size / (1024*1024):.2f} MB\n'
                    f'  Checksum: {backup.checksum[:16]}...'
                )
            )

        except Exception as e:
            raise CommandError(f'Backup failed: {e}')

