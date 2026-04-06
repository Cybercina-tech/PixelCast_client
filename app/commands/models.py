import uuid
import json
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def default_command_payload():
    """Return an empty dict for command payload default values."""
    return {}


class Command(models.Model):
    """
    Digital Signage Command model for managing immediate commands sent to Screens.
    
    Commands are instructions that can be sent to screens for immediate execution,
    such as restart, refresh, change template, or display messages. Commands are
    queued and executed when the screen is online, with retry logic and priority support.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the command"
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional description or name for the command"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this command was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this command was last updated"
    )
    
    # Relations
    screen = models.ForeignKey(
        'signage.Screen',
        on_delete=models.CASCADE,
        related_name='commands',
        help_text="Screen that should execute this command"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_commands',
        help_text="User who created/sent this command"
    )
    
    # Command Type & Payload
    COMMAND_TYPE_CHOICES = [
        ('restart', 'Restart'),
        ('refresh', 'Refresh'),
        ('change_template', 'Change Template'),
        ('display_message', 'Display Message'),
        ('sync_content', 'Sync Content'),
        ('custom', 'Custom'),
    ]
    type = models.CharField(
        max_length=50,
        choices=COMMAND_TYPE_CHOICES,
        help_text="Type of command to execute"
    )
    payload = models.JSONField(
        default=default_command_payload,
        blank=True,
        help_text="Additional parameters for command execution (JSON format)"
    )
    priority = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Priority level (higher number = higher priority)"
    )
    expire_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Command expires after this time (optional)"
    )
    
    # Status Tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the command"
    )
    executed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When command execution started"
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When command execution completed"
    )
    last_attempt_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time command execution was attempted"
    )
    attempt_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of times execution was attempted"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if command execution failed"
    )
    
    class Meta:
        db_table = 'commands_command'
        verbose_name = 'Command'
        verbose_name_plural = 'Commands'
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['screen', 'status']),
            models.Index(fields=['screen', 'priority', 'status']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['expire_at', 'status']),
            models.Index(fields=['status', 'executed_at']),
            models.Index(fields=['status', 'completed_at']),
        ]
    
    def __str__(self):
        """Return string representation: '{screen name} - {type} ({status})'"""
        status_display = self.get_status_display()
        return f"{self.screen.name} - {self.get_type_display()} ({status_display})"
    
    def clean(self):
        """Validate command data"""
        super().clean()
        
        # Validate payload based on command type
        if self.payload:
            try:
                # Ensure payload is valid JSON
                json.dumps(self.payload)
            except (TypeError, ValueError):
                raise ValidationError({
                    'payload': 'Payload must be valid JSON'
                })
            
            # Type-specific validation
            if self.type == 'change_template' and 'template_id' not in self.payload:
                raise ValidationError({
                    'payload': 'change_template command requires template_id in payload'
                })
            
            if self.type == 'display_message' and 'message' not in self.payload:
                raise ValidationError({
                    'payload': 'display_message command requires message in payload'
                })
            
            if self.type == 'sync_content':
                # sync_content can have optional content_ids array, or sync all if empty
                if 'content_ids' in self.payload and not isinstance(self.payload.get('content_ids'), list):
                    raise ValidationError({
                        'payload': 'sync_content command requires content_ids to be a list (can be empty for all)'
                    })
        
        # Validate expire_at is in the future if set
        if self.expire_at and self.expire_at <= timezone.now():
            raise ValidationError({
                'expire_at': 'Expiration time must be in the future'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # Status Management Methods
    def mark_done(self):
        """Mark command as successfully executed"""
        self.status = 'done'
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.last_attempt_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'last_attempt_at'])
    
    def mark_failed(self, error_message=None):
        """
        Mark command execution as failed.
        
        Args:
            error_message: Optional error message describing the failure
        """
        self.status = 'failed'
        self.attempt_count += 1
        self.last_attempt_at = timezone.now()
        if error_message:
            self.error_message = error_message
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save(update_fields=['status', 'attempt_count', 'last_attempt_at', 'error_message', 'completed_at'])
    
    def get_status(self):
        """
        Get comprehensive status information for the command.
        
        Returns:
            dict: Status information including status, timestamps, and error message
        """
        # Get latest execution log for additional details
        latest_log = self.execution_logs.order_by('-created_at').first()
        
        return {
            'id': str(self.id),
            'name': self.name,
            'type': self.type,
            'type_display': self.get_type_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'attempt_count': self.attempt_count,
            'is_expired': self.is_expired(),
            'can_retry': self.can_retry(),
            'screen_id': str(self.screen.id) if self.screen else None,
            'screen_name': self.screen.name if self.screen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by.id) if self.created_by else None,
            'latest_execution_log': {
                'status': latest_log.status if latest_log else None,
                'started_at': latest_log.started_at.isoformat() if latest_log and latest_log.started_at else None,
                'finished_at': latest_log.finished_at.isoformat() if latest_log and latest_log.finished_at else None,
                'error_message': latest_log.error_message if latest_log else None,
            } if latest_log else None,
        }
    
    def reset_status(self):
        """Reset command status to pending (for retry)"""
        self.status = 'pending'
        self.last_attempt_at = None
        self.save(update_fields=['status', 'last_attempt_at'])
    
    # Operational Methods
    def is_expired(self):
        """Check if command has expired"""
        if not self.expire_at:
            return False
        return timezone.now() > self.expire_at
    
    def can_retry(self, max_retries=3):
        """
        Check if command can be retried.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            bool: True if command can be retried, False otherwise
        """
        # Can only retry if status is 'failed' or 'pending'
        # Cannot retry if already done or currently executing
        if self.status == 'done':
            return False
        
        if self.status == 'executing':
            return False
        
        # Cannot retry if expired
        if self.is_expired():
            return False
        
        # Cannot retry if exceeded max attempts
        if self.attempt_count >= max_retries:
            return False
        
        # Can retry if status is 'failed' or 'pending'
        return self.status in ['failed', 'pending']
    
    def execute(self, screen=None):
        """
        Execute the command on a given Screen.
        Also creates a log entry in CommandExecutionLog.
        
        Uses transaction.atomic() to ensure command status and log updates are atomic.
        PostgreSQL's strict transaction handling prevents race conditions.
        
        Args:
            screen: Screen instance to execute command on. If None, uses self.screen.
        
        Returns:
            bool: True if execution successful, False otherwise
        """
        from log.models import CommandExecutionLog
        from django.db import transaction
        
        # Use provided screen or default to self.screen
        target_screen = screen or self.screen
        if not target_screen:
            self.mark_failed('No screen specified for command execution')
            return False
        
        # Check if command is expired
        if self.is_expired():
            with transaction.atomic():
                self.status = 'failed'
                self.completed_at = timezone.now()
                self.error_message = 'Command expired'
                self.save(update_fields=['status', 'completed_at', 'error_message'])
                # Log expired command
                CommandExecutionLog.objects.create(
                    command=self,
                    screen=target_screen,
                    status='failed',
                    error_message='Command expired'
                )
            return False
        
        # Check if screen is online
        if not target_screen.is_online:
            # Screen is offline, keep command as pending
            with transaction.atomic():
                CommandExecutionLog.objects.create(
                    command=self,
                    screen=target_screen,
                    status='pending',
                    error_message='Screen is offline'
                )
            return False
        
        # Use atomic transaction for command execution and logging
        # This ensures status updates and logs are consistent in PostgreSQL
        with transaction.atomic():
            # Lock command row to prevent concurrent execution
            command = Command.objects.select_for_update().get(id=self.id)
            
            # Update status to executing
            command.status = 'executing'
            command.attempt_count += 1
            command.executed_at = timezone.now()
            command.last_attempt_at = timezone.now()
            command.save(update_fields=['status', 'attempt_count', 'executed_at', 'last_attempt_at'])
            
            # Create execution log entry
            exec_log = CommandExecutionLog.objects.create(
                command=command,
                screen=target_screen,
                status='running',
                started_at=timezone.now()
            )
        
        try:
            # Execute command based on type (outside transaction to avoid long locks)
            success = self._execute_by_type_for_screen(target_screen)
            
            # Update status atomically after execution
            with transaction.atomic():
                command = Command.objects.select_for_update().get(id=self.id)
                exec_log = CommandExecutionLog.objects.filter(
                    id=exec_log.id
                ).first()
                
                if success:
                    command.mark_done()
                    if exec_log:
                        exec_log.status = 'done'
                        exec_log.finished_at = timezone.now()
                        exec_log.save(update_fields=['status', 'finished_at'])
                    return True
                else:
                    command.mark_failed('Command execution failed')
                    if exec_log:
                        exec_log.status = 'failed'
                        exec_log.finished_at = timezone.now()
                        exec_log.error_message = 'Command execution failed'
                        exec_log.save(update_fields=['status', 'finished_at', 'error_message'])
                    return False
                
        except Exception as e:
            # Log error atomically
            error_msg = str(e)
            with transaction.atomic():
                command = Command.objects.select_for_update().get(id=self.id)
                command.mark_failed(error_msg)
                exec_log = CommandExecutionLog.objects.filter(
                    id=exec_log.id
                ).first()
                if exec_log:
                    exec_log.status = 'failed'
                    exec_log.finished_at = timezone.now()
                    exec_log.error_message = error_msg
                    exec_log.save(update_fields=['status', 'finished_at', 'error_message'])
            return False
    
    def execute_command(self):
        """
        Execute the command on the target screen (backward compatibility).
        Also creates a log entry in CommandExecutionLog.
        
        Returns:
            bool: True if execution successful, False otherwise
        """
        return self.execute(self.screen)
    
    def _execute_by_type_for_screen(self, screen):
        """
        Execute command based on its type for a specific screen.
        
        Args:
            screen: Screen instance to execute command on
            
        Returns:
            bool: True if execution successful, False otherwise
        """
        if self.type == 'restart':
            return self._send_to_screen(screen, 'restart', {})
        
        elif self.type == 'refresh':
            return self._send_to_screen(screen, 'refresh', {})
        
        elif self.type == 'change_template':
            template_id = self.payload.get('template_id')
            if not template_id:
                return False
            # Activate template on screen
            try:
                from templates.models import Template
                template = Template.objects.get(id=template_id)
                return template.activate_on_screen(screen, sync_content=True)
            except Template.DoesNotExist:
                return False
        
        elif self.type == 'display_message':
            message = self.payload.get('message')
            if not message:
                return False
            return self._send_to_screen(screen, 'display_message', {'message': message})
        
        elif self.type == 'sync_content':
            # Check if this is a direct content download command (from content.download_to_screen)
            # These commands have content_id, content_url, etc. in payload
            if 'content_id' in self.payload and 'content_url' in self.payload:
                # Direct content download - send command to screen
                # The screen will handle the actual download
                return self._send_to_screen(screen, 'sync_content', self.payload)
            
            # Otherwise, this is a bulk sync command
            content_ids = self.payload.get('content_ids', [])
            if content_ids:
                # Sync specific content items
                from templates.models import Content
                contents = Content.objects.filter(id__in=content_ids, is_active=True)
                success_count = 0
                for content in contents:
                    try:
                        # Create individual download commands for each content
                        # Don't call download_to_screen() here to avoid recursion
                        # Instead, send the download instruction directly
                        secure_url = content.get_secure_url()
                        download_payload = {
                            'content_id': str(content.id),
                            'content_url': secure_url,
                            'content_type': content.type,
                            'file_size': content.file_size,
                            'file_hash': content.file_hash,
                            'hash_algorithm': content.hash_algorithm,
                        }
                        if self._send_to_screen(screen, 'sync_content', download_payload):
                            success_count += 1
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error syncing content {content.id} to screen {screen.id}: {str(e)}")
                return success_count > 0
            else:
                # Sync all active template content
                if screen.active_template:
                    synced_count = screen.sync_template_content()
                    return synced_count > 0
                return False
        
        elif self.type == 'custom':
            return self._send_to_screen(screen, 'custom', self.payload)
        
        return False
    
    def _send_to_screen(self, screen, command_type, data):
        """
        Send command to screen via WebSocket (primary) or HTTP (fallback).
        
        This method:
        1. Tries WebSocket first (if screen is connected)
        2. Falls back to HTTP POST if WebSocket unavailable
        3. Handles authentication and security
        4. Updates screen's last_command_sent_at on success
        
        Args:
            screen: Screen instance to send command to
            command_type: Type of command to send
            data: Command data/payload
            
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not screen.is_online:
            return False
        
        # Prepare command payload
        from commands.security import ScreenSecurity
        
        command_payload = {
            'command_id': str(self.id),
            'command_type': command_type,
            'payload': data,
            'priority': self.priority,
            'expire_at': self.expire_at.isoformat() if self.expire_at else None
        }
        
        # Create signed payload
        signed_payload = ScreenSecurity.create_signed_payload(
            screen.secret_key,
            command_payload
        )
        
        # Try WebSocket first
        from commands.connection_registry import ScreenConnectionRegistry
        
        if ScreenConnectionRegistry.is_connected(str(screen.id)):
            success = ScreenConnectionRegistry.send_command_to_screen(
                str(screen.id),
                signed_payload
            )
            if success:
                screen.last_command_sent_at = timezone.now()
                screen.save(update_fields=['last_command_sent_at'])
                return True
        
        # For sync_content commands, if WebSocket is not available,
        # we can still mark command as pending - screen will pull it via /iot/commands/pending/
        # This is better than failing immediately
        if command_type == 'sync_content':
            # Screen will fetch this command via polling endpoint
            # Mark command as pending (it's already pending, but ensure it's queued)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"WebSocket not available for screen {screen.id}, "
                f"command {self.id} will be fetched via polling endpoint"
            )
            # Command is already pending, screen will fetch it
            # Return True to indicate command is queued (not failed)
            return True
        
        # For other command types, try HTTP fallback
        try:
            from commands.views import send_command_via_http
            success = send_command_via_http(screen, signed_payload)
            if success:
                screen.last_command_sent_at = timezone.now()
                screen.save(update_fields=['last_command_sent_at'])
                return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"HTTP fallback failed for screen {screen.id}: {str(e)}")
        
        return False
    
    # Helper Methods for Command Management
    @classmethod
    def queue_command(cls, command_type, screen, payload=None, name=None, priority=0, expire_at=None, created_by=None):
        """
        Queue a command for execution on a screen.
        
        Uses transaction.atomic() to ensure command creation is atomic.
        PostgreSQL's strict transaction handling prevents race conditions.
        
        Args:
            command_type: Type of command (must be one of COMMAND_TYPE_CHOICES)
            screen: Screen instance
            payload: Optional command payload (dict)
            name: Optional command name
            priority: Command priority (default: 0)
            expire_at: Optional expiration datetime
            created_by: Optional user who created the command
            
        Returns:
            Command: Created command instance
        """
        from django.db import transaction
        
        with transaction.atomic():
            command = cls.objects.create(
                name=name,
                type=command_type,
                screen=screen,
                payload=payload or {},
                priority=priority,
                expire_at=expire_at,
                created_by=created_by
            )
        return command
    
    @classmethod
    def get_pending_commands(cls, screen=None, limit=None):
        """
        Get pending commands for a screen or all screens.
        
        Args:
            screen: Optional Screen instance to filter by
            limit: Optional limit on number of commands to return
            
        Returns:
            QuerySet: Pending commands ordered by priority
        """
        queryset = cls.objects.filter(
            status='pending'
        ).exclude(
            expire_at__lt=timezone.now()
        ).order_by('-priority', 'created_at')
        
        if screen:
            queryset = queryset.filter(screen=screen)
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @classmethod
    def get_executable_commands(cls, screen=None, limit=None):
        """
        Get commands that can be executed now (pending and screen is online).
        
        Args:
            screen: Optional Screen instance to filter by
            limit: Optional limit on number of commands to return
            
        Returns:
            QuerySet: Executable commands ordered by priority
        """
        queryset = cls.get_pending_commands(screen=screen, limit=limit)
        
        if screen:
            # Filter for online screens only
            if not screen.is_online:
                return queryset.none()
        else:
            # Filter for commands where screen is online
            queryset = queryset.filter(screen__is_online=True)
        
        return queryset
    
    # Property Methods
    @property
    def is_pending(self):
        """Check if command is pending execution"""
        return self.status == 'pending' and not self.is_expired()
    
    @property
    def is_executable(self):
        """Check if command can be executed now"""
        return (
            self.is_pending and
            self.screen.is_online and
            not self.is_expired()
        )
    
    @property
    def time_until_expiry(self):
        """Calculate time remaining until expiry (in seconds)"""
        if not self.expire_at:
            return None
        delta = self.expire_at - timezone.now()
        return max(0, delta.total_seconds())
    
    @property
    def payload_summary(self):
        """Get a summary of payload for display"""
        if not self.payload:
            return "No payload"
        
        # Create a readable summary
        if self.type == 'change_template':
            return f"Template ID: {self.payload.get('template_id', 'N/A')}"
        elif self.type == 'display_message':
            message = self.payload.get('message', '')
            return f"Message: {message[:50]}..." if len(message) > 50 else f"Message: {message}"
        elif self.type == 'sync_content':
            content_ids = self.payload.get('content_ids', [])
            if content_ids:
                return f"Sync {len(content_ids)} content item(s)"
            else:
                return "Sync all pending content"
        elif self.type == 'custom':
            return f"Custom data: {len(self.payload)} fields"
        else:
            return "Standard command"
