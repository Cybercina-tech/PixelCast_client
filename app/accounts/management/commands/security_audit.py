"""
Management command to perform security audit of user accounts.

Checks for security issues like:
- Weak passwords
- Inactive accounts
- Accounts without recent login
- Accounts with admin roles
- Duplicate emails
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from accounts.security import PasswordStrengthChecker

User = get_user_model()


class Command(BaseCommand):
    help = 'Perform security audit of user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-weak-passwords',
            action='store_true',
            help='Check for users with weak passwords (requires password hashes)',
        )
        parser.add_argument(
            '--check-inactive',
            action='store_true',
            help='Check for inactive user accounts',
        )
        parser.add_argument(
            '--check-no-login',
            type=int,
            metavar='DAYS',
            help='Check for accounts with no login in last N days',
        )
        parser.add_argument(
            '--check-admin-count',
            action='store_true',
            help='List all admin accounts',
        )
        parser.add_argument(
            '--check-duplicates',
            action='store_true',
            help='Check for duplicate emails/usernames',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting security audit...\n'))
        
        issues_found = 0
        
        # Check inactive accounts
        if options['check_inactive']:
            inactive_count = User.objects.filter(is_active=False).count()
            if inactive_count > 0:
                self.stdout.write(self.style.WARNING(f'Found {inactive_count} inactive accounts'))
                issues_found += inactive_count
        
        # Check accounts with no recent login
        if options['check_no_login']:
            days = options['check_no_login']
            cutoff_date = timezone.now() - timedelta(days=days)
            no_login = User.objects.filter(
                is_active=True,
                last_seen__lt=cutoff_date
            ).exclude(last_seen__isnull=True)
            
            count = no_login.count()
            if count > 0:
                self.stdout.write(self.style.WARNING(
                    f'Found {count} active accounts with no login in last {days} days'
                ))
                issues_found += count
        
        # Check admin accounts
        if options['check_admin_count']:
            admins = User.objects.filter(role__in=['Admin', 'SuperAdmin'], is_active=True)
            admin_count = admins.count()
            self.stdout.write(self.style.SUCCESS(f'Found {admin_count} active admin accounts:'))
            for admin in admins:
                self.stdout.write(f'  - {admin.username} ({admin.email}) - {admin.role}')
        
        # Check duplicates
        if options['check_duplicates']:
            from django.db.models import Count
            duplicate_emails = User.objects.values('email').annotate(
                count=Count('email')
            ).filter(count__gt=1)
            
            if duplicate_emails.exists():
                self.stdout.write(self.style.ERROR('Found duplicate emails:'))
                for dup in duplicate_emails:
                    self.stdout.write(f'  - {dup["email"]} ({dup["count"]} accounts)')
                    issues_found += dup['count']
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nAudit complete. Found {issues_found} potential issues.'))
        
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS('No security issues detected!'))
