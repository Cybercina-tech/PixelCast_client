"""
Management command to reset a user's password.

Usage:
    python manage.py reset_password
    python manage.py reset_password --username siavash
"""

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from accounts.models import User
import getpass


class Command(BaseCommand):
    help = 'Reset password for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the user to reset password for'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to reset password for'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        
        # Get username or email
        if not username and not email:
            username = input('Username or Email: ')
        
        # Find user
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=username)
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User with username/email "{username}" not found.'))
                    return
        
        if email and not user:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email "{email}" not found.'))
                return
        
        if not user:
            self.stdout.write(self.style.ERROR('User not found.'))
            return
        
        # Display user info
        self.stdout.write(f'Found user: {user.username} ({user.email})')
        self.stdout.write(f'  Is staff: {user.is_staff}')
        self.stdout.write(f'  Is superuser: {user.is_superuser}')
        self.stdout.write(f'  Is active: {user.is_active}')
        self.stdout.write('')
        
        # Get new password
        password = getpass.getpass('New password: ')
        password_confirm = getpass.getpass('New password (again): ')
        
        if password != password_confirm:
            self.stdout.write(self.style.ERROR('Passwords do not match.'))
            return
        
        if not password:
            self.stdout.write(self.style.ERROR('Password cannot be empty.'))
            return
        
        # Validate password
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            self.stdout.write(self.style.WARNING(f'Password validation warnings: {"; ".join(e.messages)}'))
            confirm = input('Continue anyway? (y/N): ')
            if confirm.lower() != 'y':
                return
        
        # Set password
        try:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully reset password for user "{user.username}"'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error resetting password: {str(e)}'))
