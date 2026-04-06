"""
Clear API login lockout counters (Redis cache) for a username/email and/or IP.

After repeated wrong passwords, /api/auth/login/ returns 429 until LOCKOUT_DURATION expires.

Usage:
  python manage.py clear_login_lockout --email admin@pixelcast.com
  python manage.py clear_login_lockout --ip 172.18.0.5
  python manage.py clear_login_lockout --email user@x.com --ip 127.0.0.1

Docker:
  docker compose exec backend python manage.py clear_login_lockout --email admin@pixelcast.com
"""

from django.core.management.base import BaseCommand

from accounts.security import AccountLockoutManager


class Command(BaseCommand):
    help = 'Clear login lockout / attempt counters for username, email, and/or IP.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            default='',
            help='Username or email (normalized to lowercase; same key as login form)',
        )
        parser.add_argument(
            '--ip',
            action='append',
            default=[],
            help='Client IP (repeat for multiple). Optional.',
        )

    def handle(self, *args, **options):
        email = (options['email'] or '').strip().lower()
        ips = [x.strip() for x in (options['ip'] or []) if x and str(x).strip()]

        cleared = []
        if email:
            AccountLockoutManager.clear_failed_attempts(email)
            cleared.append(email)
        for ip in ips:
            AccountLockoutManager.clear_failed_attempts(ip)
            cleared.append(ip)

        if not cleared:
            self.stdout.write(self.style.WARNING('Nothing to clear — pass --email and/or --ip'))
            return

        self.stdout.write(self.style.SUCCESS(f'Cleared login lockout for: {", ".join(cleared)}'))
