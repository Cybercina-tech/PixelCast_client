"""
Management command to create users.

This command allows batch creation of users with different roles.

Usage:
    python manage.py create_user --username admin --email admin@example.com --role Developer --is-superuser --is-staff
    python manage.py create_user --username user1 --email user1@example.com --role Manager --organization "Acme Corp"
    python manage.py create_user --username user2 --email user2@example.com --role Employee --no-password
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.models import User


class Command(BaseCommand):
    help = 'Create a new user account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username for the new user'
        )
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address for the new user'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the new user (will prompt if not provided)'
        )
        parser.add_argument(
            '--no-password',
            action='store_true',
            help='Create user without password (user must set password on first login)'
        )
        parser.add_argument(
            '--full-name',
            type=str,
            help='Full name of the user'
        )
        parser.add_argument(
            '--phone-number',
            type=str,
            help='Phone number of the user'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['Developer', 'Manager', 'Employee'],
            default='Employee',
            help='Role for the new user (default: Employee)'
        )
        parser.add_argument(
            '--organization',
            type=str,
            help='Organization name for the user'
        )
        parser.add_argument(
            '--is-active',
            action='store_true',
            default=True,
            help='Create user as active (default: True)'
        )
        parser.add_argument(
            '--is-staff',
            action='store_true',
            help='Create user as staff'
        )
        parser.add_argument(
            '--is-superuser',
            action='store_true',
            help='Create user as superuser'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options.get('password')
        no_password = options.get('no_password', False)
        full_name = options.get('full_name')
        phone_number = options.get('phone_number')
        role = options['role']
        organization = options.get('organization')
        is_active = options.get('is_active', True)
        is_staff = options.get('is_staff', False)
        is_superuser = options.get('is_superuser', False)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User with username "{username}" already exists.')
        
        if User.objects.filter(email=email.lower()).exists():
            raise CommandError(f'User with email "{email}" already exists.')
        
        # Get password
        if no_password:
            password = None
        elif not password:
            password = self._get_password()
        
        # Validate password if provided
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise CommandError(f'Password validation failed: {"; ".join(e.messages)}')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                phone_number=phone_number,
                role=role,
                organization_name=organization,
                is_active=is_active,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created user "{username}" with role "{role}"'
                )
            )
            
            if not password:
                self.stdout.write(
                    self.style.WARNING(
                        'User created without password. User must set password on first login.'
                    )
                )
            
            return user
            
        except Exception as e:
            raise CommandError(f'Error creating user: {str(e)}')
    
    def _get_password(self):
        """Get password from user input"""
        import getpass
        
        password = getpass.getpass('Password: ')
        password_confirm = getpass.getpass('Password (again): ')
        
        if password != password_confirm:
            raise CommandError('Passwords do not match.')
        
        if not password:
            raise CommandError('Password cannot be empty.')
        
        return password
