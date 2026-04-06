"""
Serializers for setup/installation API.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class DBCredentialsSerializer(serializers.Serializer):
    """Serializer for database credentials. Password is optional; if empty, username is used as password."""
    name = serializers.CharField(
        max_length=255,
        help_text="Database name"
    )
    user = serializers.CharField(
        max_length=255,
        help_text="Database user"
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default='',
        help_text="Database password (leave blank to use username as password)"
    )
    host = serializers.CharField(
        max_length=255,
        default='localhost',
        help_text="Database host"
    )
    port = serializers.IntegerField(
        default=5432,
        help_text="Database port"
    )


class DBCheckSerializer(serializers.Serializer):
    """Serializer for database connection test response."""
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    details = serializers.DictField(read_only=True, required=False)


class RunMigrationsSerializer(serializers.Serializer):
    """Serializer for running migrations."""
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    applied_migrations = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        required=False
    )


class SeedAssetsSerializer(serializers.Serializer):
    """Serializer for seeding default notification events and related assets."""
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)


class CreateAdminSerializer(serializers.Serializer):
    """Serializer for creating or updating admin user (upsert)."""
    organization_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Organization / business name (required for client deployment — fixed tenant)",
    )
    username = serializers.CharField(
        max_length=150,
        help_text="Username for the admin account"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Email address for the admin account"
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Password (leave blank to use username as password)"
    )
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="First name of the admin"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Last name of the admin"
    )

    def validate_password(self, value):
        """Require min 8 characters only when password is provided."""
        if value and len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        return value or ""


class FinalizeSerializer(serializers.Serializer):
    """Serializer for finalizing installation."""
    # Environment configuration (optional - can be provided during finalize)
    db_name = serializers.CharField(required=False, allow_blank=True)
    db_user = serializers.CharField(required=False, allow_blank=True)
    db_password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    db_host = serializers.CharField(required=False, allow_blank=True)
    db_port = serializers.IntegerField(required=False, default=5432)
    secret_key = serializers.CharField(required=False, allow_blank=True, write_only=True)
    base_url = serializers.CharField(required=False, allow_blank=True)
    debug = serializers.BooleanField(required=False, default=False)
    allowed_hosts = serializers.CharField(required=False, allow_blank=True)
    
    # Response fields
    status = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    restart_required = serializers.BooleanField(read_only=True)


class SetupStatusSerializer(serializers.Serializer):
    """Serializer for setup status."""
    installed = serializers.BooleanField(read_only=True)
    database_connected = serializers.BooleanField(read_only=True)
    migrations_applied = serializers.BooleanField(read_only=True)
    admin_exists = serializers.BooleanField(read_only=True)
    db_name = serializers.CharField(read_only=True, required=False)
    db_user = serializers.CharField(read_only=True, required=False)
    db_password_configured = serializers.BooleanField(
        read_only=True,
        help_text='True if DATABASES password is non-empty (value is never returned).',
    )
    db_host = serializers.CharField(read_only=True, required=False)
    db_port = serializers.CharField(read_only=True, required=False)
