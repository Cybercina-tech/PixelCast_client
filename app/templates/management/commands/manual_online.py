"""
Management command to manually set a screen as online.
Useful for testing or when screen needs to be marked online without waiting for heartbeat.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from signage.models import Screen


class Command(BaseCommand):
    help = 'Manually set a screen as online'

    def add_arguments(self, parser):
        parser.add_argument(
            '--screen-id',
            type=str,
            help='Screen ID (UUID) to set as online',
        )
        parser.add_argument(
            '--screen-name',
            type=str,
            help='Screen name to set as online',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Set all screens as online',
        )

    def handle(self, *args, **options):
        screen_id = options.get('screen_id')
        screen_name = options.get('screen_name')
        set_all = options.get('all', False)

        if set_all:
            screens = Screen.objects.all()
            count = screens.count()
            for screen in screens:
                screen.update_heartbeat()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set {count} screens as online')
            )
        elif screen_id:
            try:
                screen = Screen.objects.get(id=screen_id)
                screen.update_heartbeat()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully set screen "{screen.name}" (ID: {screen.id}) as online')
                )
            except Screen.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Screen with ID {screen_id} not found')
                )
        elif screen_name:
            try:
                screen = Screen.objects.get(name=screen_name)
                screen.update_heartbeat()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully set screen "{screen.name}" (ID: {screen.id}) as online')
                )
            except Screen.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Screen with name "{screen_name}" not found')
                )
            except Screen.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.ERROR(f'Multiple screens found with name "{screen_name}". Please use --screen-id instead.')
                )
        else:
            self.stdout.write(
                self.style.ERROR('Please provide --screen-id, --screen-name, or --all')
            )

