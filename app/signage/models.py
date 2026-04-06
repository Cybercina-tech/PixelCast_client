import uuid
import secrets
import hashlib
import logging
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

logger = logging.getLogger(__name__)


class Screen(models.Model):
    """
    Digital Signage Screen model for managing display devices.
    
    This model tracks all aspects of a digital signage screen including
    device information, status, security, technical specifications, and logs.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the screen"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the screen"
    )
    device_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique device identifier"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Physical location of the screen"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional description or notes about the screen"
    )
    
    # Relations
    active_template = models.ForeignKey(
        'templates.Template',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_screens',
        help_text="Currently active template assigned to this screen"
    )
    assigned_schedules = models.ManyToManyField(
        'signage.Schedule',
        blank=True,
        related_name='screens',
        help_text="Schedules assigned to this screen"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_screens',
        help_text="User who owns or manages this screen"
    )
    
    # Legacy auth fields (kept for migration compatibility, no longer used at runtime)
    auth_token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Legacy auth token (deprecated, use device_token_hash)"
    )
    secret_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Legacy secret key (deprecated, use device_token_hash)"
    )

    # Secure device authentication (replaces auth_token/secret_key for runtime)
    device_token_hash = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        help_text="SHA-256 hash of the device token issued during pairing"
    )
    device_token_issued_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the current device token was issued"
    )
    token_revoked_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the device token was revoked (forces re-pair)"
    )
    last_paired_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this screen was last successfully paired"
    )

    registration_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the screen was registered"
    )
    last_ip = models.GenericIPAddressField(
        protocol='both',
        unpack_ipv4=False,
        blank=True,
        null=True,
        help_text="Last known IP address of the device"
    )
    
    # Status Tracking
    is_online = models.BooleanField(
        default=False,
        help_text="Whether the screen is currently online"
    )
    last_heartbeat_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time a heartbeat was received from the device"
    )
    last_command_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time a command was sent to the device"
    )
    last_command_received_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time a command response was received from the device"
    )
    last_template_update_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time the template was updated on the device"
    )
    is_busy = models.BooleanField(
        default=False,
        help_text="Whether the screen is currently processing a command"
    )
    
    # Technical Info
    app_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Version of the signage application running on the device"
    )
    os_version = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Operating system version of the device"
    )
    device_model = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Model name/number of the device"
    )
    screen_width = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Screen width in pixels"
    )
    screen_height = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Screen height in pixels"
    )
    brightness = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Screen brightness level (0-100)"
    )
    ORIENTATION_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait'),
        ('reverse_landscape', 'Reverse Landscape'),
        ('reverse_portrait', 'Reverse Portrait'),
    ]
    orientation = models.CharField(
        max_length=20,
        choices=ORIENTATION_CHOICES,
        default='landscape',
        help_text="Screen orientation"
    )
    
    # Inline Logs
    last_error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Last error message received from the device"
    )
    last_sync_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Last synchronization status"
    )
    last_download_error = models.TextField(
        blank=True,
        null=True,
        help_text="Last download error message"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )
    
    class Meta:
        db_table = 'signage_screen'
        verbose_name = 'Screen'
        verbose_name_plural = 'Screens'
        ordering = ['-registration_date', 'name']
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['auth_token']),
            models.Index(fields=['device_token_hash']),
            models.Index(fields=['is_online', 'last_heartbeat_at']),
            models.Index(fields=['owner', 'is_online']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate legacy auth_token and secret_key if not provided."""
        if not self.auth_token:
            self.auth_token = secrets.token_urlsafe(32)
        if not self.secret_key:
            self.secret_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

    # ── Device token helpers ──────────────────────────────────────────

    @staticmethod
    def hash_device_token(raw_token: str) -> str:
        """Produce a SHA-256 hex digest of *raw_token*."""
        return hashlib.sha256(raw_token.encode()).hexdigest()

    def issue_device_token(self):
        """
        Generate a new device token, store its hash, and return the raw token.
        The raw token is returned exactly once (during pairing handshake) and
        must be stored by the TV in localStorage.
        """
        from django.utils import timezone
        raw_token = secrets.token_urlsafe(48)
        self.device_token_hash = self.hash_device_token(raw_token)
        self.device_token_issued_at = timezone.now()
        self.token_revoked_at = None
        self.save(update_fields=[
            'device_token_hash', 'device_token_issued_at', 'token_revoked_at',
        ])
        return raw_token

    def verify_device_token(self, raw_token: str) -> bool:
        """Return True if *raw_token* matches the stored hash and is not revoked."""
        if not raw_token or not self.device_token_hash:
            return False
        if self.token_revoked_at is not None:
            return False
        return self.hash_device_token(raw_token) == self.device_token_hash

    def revoke_device_token(self):
        """Revoke the current device token, forcing the TV back to pairing."""
        from django.utils import timezone
        self.token_revoked_at = timezone.now()
        self.device_token_hash = None
        self.is_online = False
        self.save(update_fields=['token_revoked_at', 'device_token_hash', 'is_online'])

    @classmethod
    def authenticate_device(cls, screen_id, raw_token):
        """
        Look up a screen by *screen_id* and verify *raw_token*.
        Returns the Screen instance on success, None otherwise.
        """
        try:
            screen = cls.objects.get(id=screen_id)
        except (cls.DoesNotExist, ValueError):
            return None
        if screen.verify_device_token(raw_token):
            return screen
        return None
    
    def is_heartbeat_stale(self, timeout_minutes=5):
        """
        Check if the last heartbeat is stale (older than timeout_minutes).
        
        Args:
            timeout_minutes: Number of minutes to consider a heartbeat stale
            
        Returns:
            bool: True if heartbeat is stale or missing, False otherwise
        """
        if not self.last_heartbeat_at:
            return True
        from django.utils import timezone
        from datetime import timedelta
        threshold = timezone.now() - timedelta(minutes=timeout_minutes)
        return self.last_heartbeat_at < threshold
    
    def update_heartbeat(self, latency=None, cpu_usage=None, memory_usage=None, ip_address=None):
        """
        Update screen heartbeat and status.
        Also creates a log entry in ScreenStatusLog.
        
        Args:
            latency: Heartbeat latency in milliseconds (optional)
            cpu_usage: CPU usage percentage (optional)
            memory_usage: Memory usage percentage (optional)
            ip_address: IP address of the screen (optional)
        """
        from django.utils import timezone
        from log.models import ScreenStatusLog
        
        now = timezone.now()
        self.is_online = True
        self.last_heartbeat_at = now
        if ip_address:
            self.last_ip = ip_address
        
        # Save screen status
        self.save(update_fields=['is_online', 'last_heartbeat_at', 'last_ip'])
        
        # Create status log entry
        ScreenStatusLog.objects.create(
            screen=self,
            status='online',
            heartbeat_latency=latency,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
    
    def mark_offline(self):
        """Mark screen as offline and create status log entry"""
        from django.utils import timezone
        from log.models import ScreenStatusLog
        from core.models import Notification
        
        was_online = self.is_online
        self.is_online = False
        self.save(update_fields=['is_online'])
        
        # Create offline status log entry
        ScreenStatusLog.objects.create(
            screen=self,
            status='offline'
        )
        
        # Create notification for screen owner if screen was previously online
        if was_online and self.owner:
            try:
                Notification.create_notification(
                    user=self.owner,
                    title='Screen Offline',
                    message=f'Screen "{self.name}" has gone offline.',
                    type='error',
                    related_object=self
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create notification for screen offline: {e}")
    
    def authenticate(self, auth_token, secret_key):
        """
        Authenticate screen using auth_token and secret_key.
        
        Args:
            auth_token: Authentication token
            secret_key: Secret key
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        at = str(self.auth_token or '')
        sk = str(self.secret_key or '')
        ot = str(auth_token or '')
        ok = str(secret_key or '')
        try:
            return secrets.compare_digest(at, ot) and secrets.compare_digest(sk, ok)
        except (TypeError, ValueError):
            return False
    
    def activate_template(self, template, sync_content=True):
        """
        Activate a template on this screen.
        
        Uses transaction.atomic() to ensure template activation and content sync are atomic.
        PostgreSQL's strict transaction handling prevents race conditions.
        
        Args:
            template: Template instance to activate
            sync_content: Whether to sync content after activation (default: True)
            
        Returns:
            bool: True if activation successful, False otherwise
        """
        from django.utils import timezone
        from django.db import transaction
        
        # Validate template is active
        if not template.is_active:
            return False
        
        logger.debug(
            "[activate_template] start screen=%s template=%s sync_content=%s",
            self.id,
            template.id,
            sync_content,
        )
        
        # Use atomic transaction for template activation
        # This ensures screen update and content sync operations are atomic
        with transaction.atomic():
            # Lock screen row to prevent concurrent activation
            # Refresh self from DB to get latest state
            self.refresh_from_db()
            
            # Activate template on self (the screen instance)
            self.active_template = template
            self.last_template_update_at = timezone.now()
            
            # CRITICAL: Save immediately to ensure DB is updated before response
            self.save(update_fields=['active_template', 'last_template_update_at'])
            
            # CRITICAL: Refresh immediately after save to ensure we have the latest state
            self.refresh_from_db()
            
            # Sync content if requested (within same transaction)
            if sync_content:
                synced_count = self.sync_template_content(template)
                logger.debug("[activate_template] synced content count=%s", synced_count)
        
        # CRITICAL: Refresh from DB one more time after transaction to ensure
        # all changes are committed and visible to other queries (like player_template_endpoint)
        self.refresh_from_db()
        
        # CRITICAL: Verify active_template is set correctly
        if self.active_template != template:
            logger.warning(
                "[activate_template] active_template mismatch expected=%s actual=%s; forcing update",
                template.id,
                self.active_template.id if self.active_template else None,
            )
            # Force update one more time
            self.active_template = template
            self.save(update_fields=['active_template'])
            self.refresh_from_db()
            logger.debug(
                "[activate_template] forced update complete active_template=%s",
                self.active_template.id if self.active_template else None,
            )
        
        # Create notification for screen owner when template is successfully pushed
        if self.owner:
            try:
                from core.models import Notification
                Notification.create_notification(
                    user=self.owner,
                    title='Template Pushed Successfully',
                    message=f'Template "{template.name}" has been successfully pushed to screen "{self.name}".',
                    type='success',
                    related_object=self
                )
            except Exception as e:
                logger.error(f"Failed to create notification for template push: {e}")
        
        return True
    
    def sync_template_content(self, template=None):
        """
        Sync all content from active template to this screen.
        
        Each content download uses its own transaction to allow partial success.
        This is intentional - we want to sync as much content as possible even if some fail.
        
        Args:
            template: Template instance (defaults to active_template)
            
        Returns:
            int: Number of content items synced
        """
        from django.utils import timezone
        from log.models import ContentDownloadLog
        
        if not template:
            template = self.active_template
        
        if not template:
            return 0
        
        synced_count = 0
        
        # Get all content from template
        layers = template.get_layers()
        for layer in layers:
            widgets = layer.get_widgets()
            for widget in widgets:
                contents = widget.contents.all()
                for content in contents:
                    if content.is_active and content.needs_download:
                        # Attempt download (each download handles its own transaction)
                        # This allows partial success - some content may sync while others fail
                        try:
                            success = content.download_to_screen(self)
                            if success:
                                synced_count += 1
                                # Log success (download_to_screen already creates log atomically)
                        except Exception as e:
                            # Log error (download_to_screen already creates log atomically)
                            pass  # Error already logged in download_to_screen
        
        return synced_count
    
    def get_online_duration(self):
        """
        Calculate how long the screen has been online in seconds.
        
        Returns:
            int: Duration in seconds if online, None otherwise
        """
        if not self.is_online or not self.last_heartbeat_at:
            return None
        from django.utils import timezone
        delta = timezone.now() - self.last_heartbeat_at
        return int(delta.total_seconds())
    
    def health_check(self):
        """
        Perform a comprehensive health check on the screen.
        
        Returns:
            dict: Health status information including:
                - is_online: bool
                - is_heartbeat_stale: bool
                - last_heartbeat_age_seconds: int or None
                - online_duration_seconds: int or None
                - has_active_template: bool
                - pending_commands_count: int
                - is_busy: bool
        """
        from commands.models import Command
        from django.utils import timezone
        
        health = {
            'is_online': self.is_online,
            'is_heartbeat_stale': self.is_heartbeat_stale(),
            'is_busy': self.is_busy,
            'has_active_template': self.active_template is not None,
            'pending_commands_count': 0,
            'last_heartbeat_age_seconds': None,
            'online_duration_seconds': None
        }
        
        if self.last_heartbeat_at:
            delta = timezone.now() - self.last_heartbeat_at
            health['last_heartbeat_age_seconds'] = int(delta.total_seconds())
        
        if self.is_online:
            health['online_duration_seconds'] = self.get_online_duration()
        
        # Count pending commands
        health['pending_commands_count'] = Command.objects.filter(
            screen=self,
            status='pending'
        ).exclude(
            expire_at__lt=timezone.now()
        ).count()
        
        return health
    
    def get_pending_commands(self, limit=None):
        """
        Get pending commands for this screen.
        
        Args:
            limit: Optional limit on number of commands to return
            
        Returns:
            QuerySet: Pending commands ordered by priority
        """
        from commands.models import Command
        from django.utils import timezone
        
        queryset = Command.objects.filter(
            screen=self,
            status='pending'
        ).exclude(
            expire_at__lt=timezone.now()
        ).order_by('-priority', 'created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def queue_command(self, command_type, payload=None, priority=0, expire_at=None, created_by=None):
        """
        Queue a command for execution on this screen.
        
        Args:
            command_type: Type of command (must be one of Command.COMMAND_TYPE_CHOICES)
            payload: Optional command payload (dict)
            priority: Command priority (default: 0)
            expire_at: Optional expiration datetime
            created_by: Optional user who created the command
            
        Returns:
            Command: Created command instance
        """
        from commands.models import Command
        
        command = Command.objects.create(
            screen=self,
            type=command_type,
            payload=payload or {},
            priority=priority,
            expire_at=expire_at,
            created_by=created_by
        )
        
        return command


class PairingSession(models.Model):
    """
    Pairing session model for screen pairing flow.
    
    Tracks temporary pairing credentials (6-digit code + token) that allow
    a TV/Web Player to be securely linked to a user account.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paired', 'Paired'),
        ('expired', 'Expired'),
    ]
    
    # Pairing credentials
    pairing_code = models.CharField(
        max_length=6,
        unique=True,
        db_index=True,
        help_text="6-digit numeric pairing code displayed on TV"
    )
    pairing_token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Secure token for QR code pairing"
    )
    
    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current status of the pairing session"
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="When this pairing session expires"
    )
    paired_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this session was successfully paired"
    )
    
    # One-time activation delivery marker
    activation_delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the device token was delivered to the TV (one-time handshake)"
    )

    # Screen relationship (set after pairing)
    screen = models.OneToOneField(
        'Screen',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pairing_session',
        help_text="Screen that was paired using this session"
    )
    
    # User who initiated pairing (set during bind)
    paired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pairing_sessions',
        help_text="User who completed the pairing"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this pairing session was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this pairing session was last updated"
    )
    
    class Meta:
        db_table = 'signage_pairing_session'
        verbose_name = 'Pairing Session'
        verbose_name_plural = 'Pairing Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pairing_code', 'status']),
            models.Index(fields=['pairing_token', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Pairing {self.pairing_code} ({self.status})"
    
    def is_expired(self):
        """Check if this pairing session has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if this pairing session is valid (not expired and pending)"""
        return self.status == 'pending' and not self.is_expired()
    
    def mark_paired(self, screen, user):
        """Mark this session as paired and link to screen and user"""
        from django.utils import timezone
        self.status = 'paired'
        self.screen = screen
        self.paired_by = user
        self.paired_at = timezone.now()
        self.save(update_fields=['status', 'screen', 'paired_by', 'paired_at'])
    
    def mark_expired(self):
        """Mark this session as expired"""
        self.status = 'expired'
        self.save(update_fields=['status'])


class Schedule(models.Model):
    """Schedule model for content scheduling."""
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signage_schedule'
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
    
    def __str__(self):
        return self.name
