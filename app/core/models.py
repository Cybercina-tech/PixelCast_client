"""
Core models for audit logging and system tracking.
"""
import uuid
import json
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class AuditLog(models.Model):
    """
    Comprehensive audit log for tracking all critical system actions.

    Tracks:
    - CRUD operations on all models
    - Command executions
    - Template activations
    - Schedule changes
    - Authentication events
    - Permission changes
    - Bulk operations
    """

    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('execute', 'Execute'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('role_change', 'Role Change'),
        ('bulk_operation', 'Bulk Operation'),
        ('backup', 'Backup'),
        ('restore', 'Restore'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('other', 'Other'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the audit log entry"
    )

    # User and session info
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="User who performed the action"
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        help_text="Username at time of action (for historical accuracy)"
    )
    user_role = models.CharField(
        max_length=50,
        blank=True,
        help_text="User role at time of action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the client"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )

    # Action details
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium',
        help_text="Severity level of the action"
    )

    # Resource information (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Content type of the affected resource"
    )
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID of the affected resource"
    )
    resource = GenericForeignKey('content_type', 'object_id')

    # Resource details
    resource_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of resource (e.g., 'Screen', 'Template')"
    )
    resource_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name or identifier of the resource"
    )

    # Action details
    description = models.TextField(
        blank=True,
        help_text="Human-readable description of the action"
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object describing what changed (before/after)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the action"
    )

    # Result
    success = models.BooleanField(
        default=True,
        help_text="Whether the action was successful"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if action failed"
    )

    # Timestamp
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the action occurred"
    )

    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Archived logs are hidden from default queries but never deleted"
    )

    class Meta:
        db_table = 'core_audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['resource_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        """Return string representation."""
        user_str = self.username or 'Anonymous'
        action_str = self.get_action_type_display()
        resource_str = self.resource_name or self.resource_type or 'Unknown'
        return f"{user_str} {action_str} {resource_str} at {self.timestamp}"

    def get_changes_summary(self) -> str:
        """Get a summary of changes made."""
        if not self.changes:
            return "No changes recorded"

        # Ensure before and after are dictionaries, not None
        before = self.changes.get('before') or {}
        after = self.changes.get('after') or {}
        
        # Additional safety check: ensure they're actually dicts
        if not isinstance(before, dict):
            before = {}
        if not isinstance(after, dict):
            after = {}

        if not before and not after:
            return "No changes recorded"

        summary_parts = []
        # Safely get keys from both dicts
        before_keys = list(before.keys()) if before else []
        after_keys = list(after.keys()) if after else []
        
        for key in set(before_keys + after_keys):
            old_value = before.get(key, 'N/A') if before else 'N/A'
            new_value = after.get(key, 'N/A') if after else 'N/A'
            if old_value != new_value:
                summary_parts.append(f"{key}: {old_value} → {new_value}")

        return "; ".join(summary_parts) if summary_parts else "No changes recorded"


class SystemBackup(models.Model):
    """
    Tracks automated and manual backups of the system.
    """

    BACKUP_TYPES = [
        ('database', 'Database'),
        ('media', 'Media Files'),
        ('full', 'Full System'),
        ('incremental', 'Incremental'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the backup"
    )

    backup_type = models.CharField(
        max_length=20,
        choices=BACKUP_TYPES,
        help_text="Type of backup"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the backup"
    )

    # Backup metadata
    file_path = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Path to backup file (local or cloud)"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Size of backup file in bytes"
    )
    checksum = models.CharField(
        max_length=128,
        blank=True,
        help_text="Checksum/hash of backup file for integrity verification"
    )

    # Configuration
    include_media = models.BooleanField(
        default=False,
        help_text="Whether media files are included"
    )
    compression = models.BooleanField(
        default=True,
        help_text="Whether backup is compressed"
    )
    encryption = models.BooleanField(
        default=False,
        help_text="Whether backup is encrypted"
    )

    # Scheduling
    scheduled = models.BooleanField(
        default=False,
        help_text="Whether this was an automated scheduled backup"
    )
    schedule_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the schedule if scheduled"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional backup metadata"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if backup failed"
    )

    # User info
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_backups',
        help_text="User who triggered the backup"
    )

    # Timestamps
    started_at = models.DateTimeField(
        default=timezone.now,
        help_text="When backup started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When backup completed"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When backup expires (for retention policy)"
    )

    class Meta:
        db_table = 'core_system_backup'
        verbose_name = 'System Backup'
        verbose_name_plural = 'System Backups'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['backup_type', 'started_at']),
            models.Index(fields=['scheduled', 'started_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        """Return string representation."""
        return f"{self.get_backup_type_display()} backup - {self.get_status_display()} ({self.started_at})"

    @property
    def duration(self):
        """Calculate backup duration."""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None

    def is_expired(self) -> bool:
        """Check if backup has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class Notification(models.Model):
    """
    In-app notification model for user notifications.
    
    Simple notification system for displaying alerts and messages to users
    in the application interface.
    """
    
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the notification"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who should receive this notification"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )
    
    message = models.TextField(
        help_text="Notification message"
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        db_index=True,
        help_text="Notification type"
    )
    
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the notification has been read"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the notification was created"
    )
    
    # Optional: Link to related object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Content type of related object"
    )
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID of related object"
    )
    related_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        db_table = 'core_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username} ({'read' if self.is_read else 'unread'})"
    
    @classmethod
    def create_notification(cls, user, title, message, type='info', related_object=None):
        """Helper method to create a notification."""
        notification = cls(
            user=user,
            title=title,
            message=message,
            type=type
        )
        if related_object:
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = str(related_object.id)
        notification.save()
        return notification


class NotificationPreference(models.Model):
    """
    Per-user notification preferences used by Notification Center.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        help_text="User that owns these notification preferences",
    )
    screen_offline = models.BooleanField(
        default=True,
        help_text="Notify when a screen goes offline",
    )
    template_push = models.BooleanField(
        default=True,
        help_text="Notify when template push succeeds",
    )
    system_updates = models.BooleanField(
        default=False,
        help_text="Notify about system updates",
    )
    email_enabled = models.BooleanField(
        default=False,
        help_text="Enable email delivery for notifications",
    )
    notification_email = models.EmailField(
        blank=True,
        default='',
        help_text="Destination email for notifications when email delivery is enabled",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_notification_preference'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class SystemEmailSettings(models.Model):
    """
    Singleton (pk=1) system-wide SMTP / transactional email configuration.
    Controlled from the admin UI (Developer); password stored encrypted at rest.
    """

    DELIVERY_CONSOLE = 'console'
    DELIVERY_SMTP = 'smtp'
    DELIVERY_CHOICES = [
        (DELIVERY_CONSOLE, 'Console (development)'),
        (DELIVERY_SMTP, 'SMTP'),
    ]

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    delivery_mode = models.CharField(
        max_length=16,
        choices=DELIVERY_CHOICES,
        default=DELIVERY_CONSOLE,
        help_text='Console prints to logs; SMTP sends via configured host.',
    )
    smtp_host = models.CharField(max_length=255, blank=True, default='')
    smtp_port = models.PositiveIntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    smtp_username = models.CharField(max_length=255, blank=True, default='')
    smtp_password_encrypted = models.TextField(blank=True, default='')
    default_from_email = models.CharField(max_length=255, blank=True, default='')
    last_smtp_test_at = models.DateTimeField(null=True, blank=True)
    last_smtp_test_ok = models.BooleanField(null=True, blank=True)
    last_smtp_test_error_code = models.CharField(max_length=32, blank=True, default='')
    last_smtp_test_detail = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_system_email_settings'
        verbose_name = 'System email settings'
        verbose_name_plural = 'System email settings'

    def __str__(self):
        return 'System email settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        return cls.objects.get_or_create(pk=1, defaults={})[0]

    def set_smtp_password(self, plain: str | None) -> None:
        if plain is None:
            return
        plain = str(plain).strip()
        if not plain:
            return
        from core.email_crypto import encrypt_secret

        self.smtp_password_encrypted = encrypt_secret(plain)

    def get_smtp_password(self) -> str:
        from core.email_crypto import decrypt_secret

        return decrypt_secret(self.smtp_password_encrypted or '')

    def clear_smtp_password(self) -> None:
        self.smtp_password_encrypted = ''


class TVBrand(models.Model):
    """TV brand catalog entry for Data Center."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True, db_index=True)
    slug = models.SlugField(max_length=140, unique=True, db_index=True)
    logo_text = models.CharField(
        max_length=32,
        default='TV',
        help_text="Short brand mark rendered as logo fallback in UI",
    )
    logo_url = models.URLField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_tv_brand'
        verbose_name = 'TV Brand'
        verbose_name_plural = 'TV Brands'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class TVModel(models.Model):
    """TV model family catalog entry for Data Center."""

    PLATFORM_CHOICES = [
        ('android_tv', 'Android TV'),
        ('google_tv', 'Google TV'),
        ('tizen', 'Tizen'),
        ('webos', 'webOS'),
        ('android_soc', 'Android SoC'),
        ('other', 'Other'),
    ]

    OPERATION_TIME_CHOICES = [
        ('16_7', '16/7'),
        ('18_7', '18/7'),
        ('24_7', '24/7'),
    ]

    BRIGHTNESS_CLASS_CHOICES = [
        ('indoor', 'Indoor (300-350 nits)'),
        ('high_bright', 'High Bright (500-700 nits)'),
        ('window', 'Window Facing (2500+ nits)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(TVBrand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=180)
    model_code = models.CharField(max_length=120, blank=True, default='')
    series = models.CharField(max_length=120, blank=True, default='')
    platform = models.CharField(max_length=32, choices=PLATFORM_CHOICES, default='other', db_index=True)
    operation_time = models.CharField(max_length=16, choices=OPERATION_TIME_CHOICES, default='16_7', db_index=True)
    brightness_class = models.CharField(max_length=32, choices=BRIGHTNESS_CLASS_CHOICES, default='indoor', db_index=True)
    control_ports = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default='')
    is_download_enabled = models.BooleanField(default=False)
    download_url = models.URLField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_tv_model'
        verbose_name = 'TV Model'
        verbose_name_plural = 'TV Models'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['brand', 'is_active']),
            models.Index(fields=['platform', 'operation_time']),
            models.Index(fields=['brightness_class', 'operation_time']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['brand', 'name'], name='core_tv_model_brand_name_unique'),
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class SupportTicket(models.Model):
    """Lightweight in-app support ticket (foundation for helpdesk)."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='open', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject[:80]