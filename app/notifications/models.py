"""
Notification System Domain Models for PixelCast Signage Digital Signage System.

Provides secure, extensible notification infrastructure with:
- Event-driven architecture
- Multi-channel support (Email, SMS, Webhook)
- Panel-ready configuration
- Full audit trail
"""

import uuid
import json
import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache

# Optional cryptography import
try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

logger = logging.getLogger(__name__)


def default_json_dict():
    """Return an empty dict for JSONField default values."""
    return {}


class EncryptedJSONField(models.TextField):
    """
    Encrypted JSON field for storing sensitive channel configuration.
    
    Uses Fernet symmetric encryption to encrypt/decrypt JSON data at rest.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def get_encryption_key(self):
        """Get encryption key from settings or generate a default one."""
        if Fernet is None:
            raise ImportError("cryptography library is required for encrypted fields. Install with: pip install cryptography")
        
        key = getattr(settings, 'NOTIFICATION_ENCRYPTION_KEY', None)
        if not key:
            # In production, this should be set in settings
            logger.warning("NOTIFICATION_ENCRYPTION_KEY not set, using default (NOT SECURE FOR PRODUCTION)")
            key = Fernet.generate_key()
        if isinstance(key, str):
            key = key.encode()
        return key
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None:
            return None
        try:
            fernet = Fernet(self.get_encryption_key())
            decrypted = fernet.decrypt(value.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Error decrypting field: {str(e)}")
            return {}
    
    def to_python(self, value):
        """Convert value to Python object."""
        if isinstance(value, dict):
            return value
        if value is None:
            return {}
        return self.from_db_value(value, None, None)
    
    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None:
            return None
        try:
            fernet = Fernet(self.get_encryption_key())
            encrypted = fernet.encrypt(json.dumps(value).encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Error encrypting field: {str(e)}")
            return None


class NotificationEvent(models.Model):
    """
    Notification event definition.
    
    Defines what events can trigger notifications (e.g., screen.offline, command.failed).
    Events are predefined and cannot be created via API (admin-only).
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the event"
    )
    event_key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Event identifier (e.g., 'screen.offline', 'command.failed')"
    )
    description = models.TextField(
        help_text="Human-readable description of the event"
    )
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info',
        db_index=True,
        help_text="Default severity level for this event"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this event is active and can trigger notifications"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this event was created"
    )
    
    class Meta:
        db_table = 'notifications_event'
        verbose_name = 'Notification Event'
        verbose_name_plural = 'Notification Events'
        ordering = ['event_key']
        indexes = [
            models.Index(fields=['event_key', 'is_active']),
            models.Index(fields=['severity', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.event_key} ({self.severity})"
    
    def clean(self):
        """Validate event_key format"""
        super().clean()
        # Event keys must follow pattern: category.action
        if '.' not in self.event_key:
            raise ValidationError("event_key must follow pattern: 'category.action'")
        parts = self.event_key.split('.')
        if len(parts) != 2:
            raise ValidationError("event_key must have exactly one dot separator")
        # Sanitize: only alphanumeric, dots, underscores, hyphens
        if not all(c.isalnum() or c in ('.', '_', '-') for c in self.event_key):
            raise ValidationError("event_key contains invalid characters")


class NotificationChannel(models.Model):
    """
    Notification channel configuration.
    
    Defines how notifications are delivered (Email, SMS, Webhook).
    Configuration is encrypted at rest.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the channel"
    )
    CHANNEL_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
    ]
    type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPE_CHOICES,
        db_index=True,
        help_text="Channel type"
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this channel"
    )
    config = EncryptedJSONField(
        help_text="Encrypted channel configuration (provider credentials, endpoints, etc.)"
    )
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this channel is enabled"
    )
    organization = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notification_channels',
        null=True,
        blank=True,
        help_text="Organization/user this channel belongs to (null for system-wide)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this channel was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this channel was last updated"
    )
    
    class Meta:
        db_table = 'notifications_channel'
        verbose_name = 'Notification Channel'
        verbose_name_plural = 'Notification Channels'
        ordering = ['type', 'name']
        indexes = [
            models.Index(fields=['type', 'is_enabled']),
            models.Index(fields=['organization', 'is_enabled']),
        ]
    
    def __str__(self):
        org_str = f" ({self.organization.username})" if self.organization else " (System)"
        return f"{self.name} - {self.get_type_display()}{org_str}"
    
    def clean(self):
        """Validate channel configuration"""
        super().clean()
        if not self.config:
            raise ValidationError("Channel configuration is required")
        
        # Validate config structure based on type
        if self.type == 'email':
            cfg = self.config or {}
            if cfg.get('use_system_smtp'):
                if not cfg.get('to_emails'):
                    raise ValidationError(
                        "Email channel with use_system_smtp requires 'to_emails' in config"
                    )
            else:
                required_fields = ['smtp_host', 'smtp_port', 'from_email']
                for field in required_fields:
                    if field not in self.config:
                        raise ValidationError(f"Email channel requires '{field}' in config")
        
        elif self.type == 'sms':
            required_fields = ['provider', 'api_key']
            for field in required_fields:
                if field not in self.config:
                    raise ValidationError(f"SMS channel requires '{field}' in config")
        
        elif self.type == 'webhook':
            required_fields = ['url', 'secret_key']
            for field in required_fields:
                if field not in self.config:
                    raise ValidationError(f"Webhook channel requires '{field}' in config")
            
            # Validate URL
            url = self.config.get('url', '')
            if not url.startswith(('http://', 'https://')):
                raise ValidationError("Webhook URL must start with http:// or https://")
            
            # Enforce HTTPS in production
            if not settings.DEBUG and not url.startswith('https://'):
                raise ValidationError("Webhook URL must use HTTPS in production")


class NotificationRule(models.Model):
    """
    Notification rule mapping events to channels.
    
    This is the panel control layer - rules define which events trigger
    which channels, with severity filtering and cooldowns.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the rule"
    )
    organization = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notification_rules',
        null=True,
        blank=True,
        help_text="Organization/user this rule belongs to (null for system-wide)"
    )
    event = models.ForeignKey(
        NotificationEvent,
        on_delete=models.CASCADE,
        related_name='rules',
        help_text="Event that triggers this rule"
    )
    channels = models.ManyToManyField(
        NotificationChannel,
        related_name='rules',
        help_text="Channels to use for this rule"
    )
    severity_threshold = models.CharField(
        max_length=20,
        choices=NotificationEvent.SEVERITY_CHOICES,
        default='info',
        help_text="Minimum severity to trigger this rule"
    )
    cooldown_seconds = models.PositiveIntegerField(
        default=300,
        validators=[MinValueValidator(0), MaxValueValidator(86400)],
        help_text="Cooldown period in seconds (0-86400)"
    )
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this rule is enabled"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this rule was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this rule was last updated"
    )
    
    class Meta:
        db_table = 'notifications_rule'
        verbose_name = 'Notification Rule'
        verbose_name_plural = 'Notification Rules'
        ordering = ['-is_enabled', 'event__event_key']
        indexes = [
            models.Index(fields=['organization', 'is_enabled']),
            models.Index(fields=['event', 'is_enabled']),
            models.Index(fields=['is_enabled', 'severity_threshold']),
        ]
    
    def __str__(self):
        org_str = f" ({self.organization.username})" if self.organization else " (System)"
        return f"{self.event.event_key} → {self.channels.count()} channel(s){org_str}"
    
    def clean(self):
        """Validate rule configuration"""
        super().clean()
        if self.cooldown_seconds > 86400:
            raise ValidationError("Cooldown cannot exceed 24 hours (86400 seconds)")


class NotificationLog(models.Model):
    """
    Notification delivery log for audit and security.
    
    Records all notification delivery attempts with full audit trail.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the log entry"
    )
    rule = models.ForeignKey(
        NotificationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        help_text="Rule that triggered this notification"
    )
    event_key = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Event key that triggered this notification"
    )
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs',
        help_text="Channel used for delivery"
    )
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Delivery status"
    )
    provider_response = models.TextField(
        blank=True,
        null=True,
        help_text="Sanitized response from provider (no secrets)"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if delivery failed"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    idempotency_key = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Idempotency key for deduplication"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this log entry was created"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was successfully sent"
    )
    
    class Meta:
        db_table = 'notifications_log'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_key', 'status']),
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['created_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.event_key} via {self.channel.type if self.channel else 'N/A'} - {self.status}"
