"""Export a user's data as JSON (GDPR-style data portability)."""

import json
from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'Dump user-related data to stdout as JSON (for GDPR portability).'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.stderr.write(f'No user: {email}')
            return
        payload = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            },
            'onboarding_progress': user.onboarding_progress,
        }
        self.stdout.write(json.dumps(payload, indent=2, default=str))
