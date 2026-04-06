"""
Promote an existing user to Developer (full access): is_superuser, is_staff, role=Developer.

``python manage.py createsuperuser`` already creates accounts this way; use this command
to repair legacy users or fix inconsistent rows.

Usage:
    python manage.py promote_developer
    python manage.py promote_developer --username siavash

Docker (example):
    docker compose exec web python manage.py promote_developer --username siavash
"""

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Set a user to Developer role with is_staff and is_superuser (emergency / ops).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='siavash',
            help='Username to promote (default: siavash)',
        )

    def handle(self, *args, **options):
        username = options['username'].strip()
        if not username:
            raise CommandError('Username must not be empty.')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            raise CommandError(f'No user with username "{username}".') from e

        user.is_superuser = True
        user.is_staff = True
        user.role = 'Developer'
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'OK: user id={user.id} username={user.username!r} '
                f'role={user.role!r} is_staff={user.is_staff} is_superuser={user.is_superuser}'
            )
        )
