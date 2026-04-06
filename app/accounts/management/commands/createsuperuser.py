"""
Override django.contrib.auth's createsuperuser so PixelCast Signage RBAC stays aligned.

Superusers are created with role=Developer, is_staff=True, is_superuser=True
via accounts.models.UserManager.create_superuser (see models.User.objects).
"""

from django.contrib.auth.management.commands.createsuperuser import (
    Command as AuthCreatesuperuserCommand,
)


class Command(AuthCreatesuperuserCommand):
    help = (
        'Creates a Django superuser with Developer role (full access), '
        'is_staff, and is_superuser — same hierarchy as the rest of PixelCast Signage.'
    )
