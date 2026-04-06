import uuid
from django.db import models
from django.db.models import Avg, Sum
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


def default_json_dict():
    """Return an empty dict for JSONField default values."""
    return {}


class ScreenStatusLog(models.Model):
    """
    Tracks the historical online/offline and health status of Screens.
    
    This model records periodic status updates from screens including
    online/offline state, heartbeat latency, and system resource usage.
    Logs are written by backend services when processing screen heartbeats.
    """
    
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the status log entry"
    )
    screen = models.ForeignKey(
        'signage.Screen',
        on_delete=models.CASCADE,
        related_name='status_logs',
        help_text="Screen that this status log belongs to"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Online or offline status"
    )
    heartbeat_latency = models.FloatField(
        blank=True,
        null=True,
        help_text="Heartbeat latency in milliseconds"
    )
    cpu_usage = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="CPU usage percentage (0-100)"
    )
    memory_usage = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Memory usage percentage (0-100)"
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this status was recorded"
    )
    
    class Meta:
        db_table = 'log_screen_status'
        verbose_name = 'Screen Status Log'
        verbose_name_plural = 'Screen Status Logs'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['screen', 'recorded_at']),
            models.Index(fields=['status', 'recorded_at']),
            models.Index(fields=['screen', 'status']),
        ]
    
    def __str__(self):
        """Return string representation: '{screen name} - {status} @ {recorded_at}'"""
        return f"{self.screen.name} - {self.get_status_display()} @ {self.recorded_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Helper Methods
    @classmethod
    def filter_by_screen(cls, screen):
        """Filter logs by screen"""
        return cls.objects.filter(screen=screen)
    
    @classmethod
    def filter_by_status(cls, status):
        """Filter logs by status"""
        return cls.objects.filter(status=status)
    
    @classmethod
    def filter_by_date_range(cls, start_date=None, end_date=None):
        """Filter logs by date range"""
        queryset = cls.objects.all()
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)
        return queryset
    
    @classmethod
    def get_summary_stats(cls, screen=None, start_date=None, end_date=None, base_queryset=None):
        """
        Get summary statistics for screen status logs.
        
        Args:
            screen: Optional Screen instance to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            base_queryset: Optional queryset to start from (e.g. org-scoped logs)
            
        Returns:
            dict: Summary statistics
        """
        queryset = base_queryset if base_queryset is not None else cls.objects.all()
        
        if screen:
            queryset = queryset.filter(screen=screen)
        
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)
        
        total_count = queryset.count()
        online_count = queryset.filter(status='online').count()
        offline_count = queryset.filter(status='offline').count()
        
        # Calculate average latency for online statuses
        online_logs = queryset.filter(status='online', heartbeat_latency__isnull=False)
        avg_latency = online_logs.aggregate(
            avg_latency=Avg('heartbeat_latency')
        )['avg_latency'] or 0
        
        # Calculate average CPU and memory usage
        online_logs_with_cpu = queryset.filter(status='online', cpu_usage__isnull=False)
        avg_cpu = online_logs_with_cpu.aggregate(
            avg_cpu=Avg('cpu_usage')
        )['avg_cpu'] or 0
        
        online_logs_with_memory = queryset.filter(status='online', memory_usage__isnull=False)
        avg_memory = online_logs_with_memory.aggregate(
            avg_memory=Avg('memory_usage')
        )['avg_memory'] or 0
        
        return {
            'total_count': total_count,
            'online_count': online_count,
            'offline_count': offline_count,
            'online_percentage': (online_count / total_count * 100) if total_count > 0 else 0,
            'average_latency_ms': round(avg_latency, 2),
            'average_cpu_usage': round(avg_cpu, 2),
            'average_memory_usage': round(avg_memory, 2),
        }


class ContentDownloadLog(models.Model):
    """
    Tracks download attempts and cache status of Content on each Screen.
    
    This model records all attempts to download content to screens,
    including success/failure status, retry counts, file sizes, and errors.
    Logs are written by backend services during content synchronization.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the download log entry"
    )
    content = models.ForeignKey(
        'templates.Content',
        on_delete=models.CASCADE,
        related_name='download_logs',
        help_text="Content that was downloaded"
    )
    screen = models.ForeignKey(
        'signage.Screen',
        on_delete=models.CASCADE,
        related_name='content_download_logs',
        help_text="Screen where content was downloaded"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Download status"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    file_size = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        help_text="File size in bytes"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if download failed"
    )
    downloaded_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When content was successfully downloaded"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this download log was created"
    )
    
    class Meta:
        db_table = 'log_content_download'
        verbose_name = 'Content Download Log'
        verbose_name_plural = 'Content Download Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content', 'created_at']),
            models.Index(fields=['screen', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['content', 'screen', 'status']),
        ]
    
    def __str__(self):
        """Return string representation: '{content name} on {screen name} - {status}'"""
        return f"{self.content.name} on {self.screen.name} - {self.get_status_display()}"
    
    # Helper Methods
    @classmethod
    def filter_by_content(cls, content):
        """Filter logs by content"""
        return cls.objects.filter(content=content)
    
    @classmethod
    def filter_by_screen(cls, screen):
        """Filter logs by screen"""
        return cls.objects.filter(screen=screen)
    
    @classmethod
    def filter_by_status(cls, status):
        """Filter logs by status"""
        return cls.objects.filter(status=status)
    
    @classmethod
    def filter_by_date_range(cls, start_date=None, end_date=None):
        """Filter logs by date range"""
        queryset = cls.objects.all()
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)
        return queryset
    
    @classmethod
    def get_summary_stats(cls, content=None, screen=None, start_date=None, end_date=None, base_queryset=None):
        """
        Get summary statistics for content download logs.
        
        Args:
            content: Optional Content instance to filter by
            screen: Optional Screen instance to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            base_queryset: Optional queryset to start from (e.g. org-scoped logs)
            
        Returns:
            dict: Summary statistics
        """
        queryset = base_queryset if base_queryset is not None else cls.objects.all()
        
        if content:
            queryset = queryset.filter(content=content)
        if screen:
            queryset = queryset.filter(screen=screen)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        total_count = queryset.count()
        success_count = queryset.filter(status='success').count()
        failed_count = queryset.filter(status='failed').count()
        pending_count = queryset.filter(status='pending').count()
        
        # Calculate total file size downloaded
        successful_downloads = queryset.filter(status='success', file_size__isnull=False)
        total_size_bytes = successful_downloads.aggregate(
            total_size=Sum('file_size')
        )['total_size'] or 0
        
        # Calculate average retry count for failed downloads
        failed_logs = queryset.filter(status='failed')
        avg_retries = failed_logs.aggregate(
            avg_retries=Avg('retry_count')
        )['avg_retries'] or 0
        
        return {
            'total_count': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'pending_count': pending_count,
            'success_rate': (success_count / total_count * 100) if total_count > 0 else 0,
            'total_size_bytes': total_size_bytes,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'average_retry_count': round(avg_retries, 2),
        }


class CommandExecutionLog(models.Model):
    """
    Tracks execution of Commands on Screens.
    
    This model records the execution lifecycle of commands sent to screens,
    including start time, finish time, status, response payload, and errors.
    Logs are written by backend services when executing commands.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the execution log entry"
    )
    command = models.ForeignKey(
        'commands.Command',
        on_delete=models.CASCADE,
        related_name='execution_logs',
        help_text="Command that was executed"
    )
    screen = models.ForeignKey(
        'signage.Screen',
        on_delete=models.CASCADE,
        related_name='command_execution_logs',
        help_text="Screen where command was executed"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Execution status"
    )
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When command execution started"
    )
    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When command execution finished"
    )
    response_payload = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Response payload from screen (JSON format)"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if execution failed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this execution log was created"
    )
    
    class Meta:
        db_table = 'log_command_execution'
        verbose_name = 'Command Execution Log'
        verbose_name_plural = 'Command Execution Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['command', 'created_at']),
            models.Index(fields=['screen', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['command', 'screen', 'status']),
        ]
    
    def __str__(self):
        """Return string representation: '{command type} on {screen name} - {status}'"""
        return f"{self.command.get_type_display()} on {self.screen.name} - {self.get_status_display()}"
    
    @property
    def execution_time(self):
        """
        Calculate execution duration in seconds.
        
        Returns:
            float: Duration in seconds if both started_at and finished_at are set, None otherwise
        """
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            return delta.total_seconds()
        return None
    
    # Helper Methods
    @classmethod
    def filter_by_command(cls, command):
        """Filter logs by command"""
        return cls.objects.filter(command=command)
    
    @classmethod
    def filter_by_screen(cls, screen):
        """Filter logs by screen"""
        return cls.objects.filter(screen=screen)
    
    @classmethod
    def filter_by_status(cls, status):
        """Filter logs by status"""
        return cls.objects.filter(status=status)
    
    @classmethod
    def filter_by_date_range(cls, start_date=None, end_date=None):
        """Filter logs by date range"""
        queryset = cls.objects.all()
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)
        return queryset
    
    @classmethod
    def get_summary_stats(cls, command=None, screen=None, start_date=None, end_date=None, base_queryset=None):
        """
        Get summary statistics for command execution logs.
        
        Args:
            command: Optional Command instance to filter by
            screen: Optional Screen instance to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            base_queryset: Optional queryset to start from (e.g. org-scoped logs)
            
        Returns:
            dict: Summary statistics
        """
        queryset = base_queryset if base_queryset is not None else cls.objects.all()
        
        if command:
            queryset = queryset.filter(command=command)
        if screen:
            queryset = queryset.filter(screen=screen)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        total_count = queryset.count()
        done_count = queryset.filter(status='done').count()
        failed_count = queryset.filter(status='failed').count()
        running_count = queryset.filter(status='running').count()
        pending_count = queryset.filter(status='pending').count()
        
        # Calculate average execution time for completed commands
        completed_logs = queryset.filter(
            status__in=['done', 'failed'],
            started_at__isnull=False,
            finished_at__isnull=False
        )
        
        execution_times = []
        for log in completed_logs:
            exec_time = log.execution_time
            if exec_time is not None:
                execution_times.append(exec_time)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            'total_count': total_count,
            'done_count': done_count,
            'failed_count': failed_count,
            'running_count': running_count,
            'pending_count': pending_count,
            'success_rate': (done_count / total_count * 100) if total_count > 0 else 0,
            'average_execution_time_seconds': round(avg_execution_time, 2),
        }


class BulkOperationLog(models.Model):
    """
    Tracks bulk operations for auditing purposes.
    
    Records who performed bulk operations, what items were affected,
    success/failure counts, and timestamps.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the bulk operation log entry"
    )
    user_id = models.IntegerField(
        db_index=True,
        help_text="ID of user who performed the operation"
    )
    username = models.CharField(
        max_length=150,
        db_index=True,
        help_text="Username who performed the operation"
    )
    operation_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Type of operation (e.g., 'bulk_delete', 'bulk_update', 'bulk_activate')"
    )
    module = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Module name (e.g., 'screens', 'templates', 'contents')"
    )
    item_ids = models.JSONField(
        default=list,
        help_text="List of item IDs affected by the operation"
    )
    item_count = models.PositiveIntegerField(
        help_text="Total number of items in the operation"
    )
    success_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of successful operations"
    )
    failure_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of failed operations"
    )
    details = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Additional details about the operation"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the operation was performed"
    )
    
    class Meta:
        db_table = 'log_bulk_operation'
        verbose_name = 'Bulk Operation Log'
        verbose_name_plural = 'Bulk Operation Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
            models.Index(fields=['operation_type', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
        ]
    
    def __str__(self):
        """Return string representation"""
        return f"{self.username} - {self.operation_type} on {self.module} ({self.success_count}/{self.item_count} succeeded)"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.item_count == 0:
            return 0
        return round((self.success_count / self.item_count) * 100, 2)


class ContentValidationLog(models.Model):
    """
    Tracks content validation attempts for auditing and security.
    
    Records who uploaded what content, validation results, and errors.
    """
    
    VALIDATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('security_risk', 'Security Risk'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the validation log entry"
    )
    user_id = models.IntegerField(
        db_index=True,
        help_text="ID of user who uploaded the content"
    )
    username = models.CharField(
        max_length=150,
        db_index=True,
        help_text="Username who uploaded the content"
    )
    content_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Content ID (if saved after validation)"
    )
    filename = models.CharField(
        max_length=500,
        help_text="Original filename"
    )
    sanitized_filename = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Sanitized filename after validation"
    )
    content_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Content type (image, video, text, etc.)"
    )
    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    mime_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Detected MIME type"
    )
    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Validation status"
    )
    is_valid = models.BooleanField(
        default=False,
        help_text="Whether validation passed"
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation errors"
    )
    validation_warnings = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation warnings"
    )
    metadata = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Extracted metadata (dimensions, format, etc.)"
    )
    security_flags = models.JSONField(
        default=list,
        blank=True,
        help_text="Security flags raised during validation"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When validation was performed"
    )
    
    class Meta:
        db_table = 'log_content_validation'
        verbose_name = 'Content Validation Log'
        verbose_name_plural = 'Content Validation Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['content_type', 'timestamp']),
            models.Index(fields=['validation_status', 'timestamp']),
            models.Index(fields=['is_valid', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
        ]
    
    def __str__(self):
        """Return string representation"""
        status = "✓" if self.is_valid else "✗"
        return f"{status} {self.username} - {self.filename} ({self.content_type})"


class ErrorLog(models.Model):
    """
    Tracks all application errors for Super Admin monitoring.
    
    This model records server-side errors, API exceptions, and backend process failures.
    Errors are automatically logged by middleware and can be viewed by SuperAdmin users.
    """
    
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the error log entry"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the error occurred"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='ERROR',
        db_index=True,
        help_text="Error severity level"
    )
    message = models.TextField(
        help_text="Error message"
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs',
        help_text="User who triggered the error (if applicable)"
    )
    stack_trace = models.TextField(
        blank=True,
        null=True,
        help_text="Full stack trace of the error"
    )
    endpoint = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        db_index=True,
        help_text="API endpoint or URL where error occurred"
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="HTTP method (GET, POST, etc.)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the client"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string"
    )
    exception_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Type of exception (e.g., ValueError, PermissionDenied)"
    )
    metadata = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Additional error metadata"
    )
    is_resolved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the error has been resolved"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the error was marked as resolved"
    )
    resolved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_errors',
        help_text="User who resolved the error"
    )
    
    class Meta:
        db_table = 'log_error'
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['exception_type', 'timestamp']),
            models.Index(fields=['is_resolved', 'timestamp']),
        ]
    
    def __str__(self):
        """Return string representation"""
        user_str = f"User: {self.user.username}" if self.user else "Anonymous"
        endpoint_str = f" @ {self.endpoint}" if self.endpoint else ""
        return f"[{self.get_level_display()}] {self.message[:50]}... ({user_str}{endpoint_str})"
    
    @classmethod
    def filter_by_date_range(cls, start_date=None, end_date=None):
        """Filter errors by date range"""
        queryset = cls.objects.all()
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        return queryset
    
    @classmethod
    def filter_by_level(cls, level):
        """Filter errors by severity level"""
        return cls.objects.filter(level=level)
    
    @classmethod
    def filter_by_endpoint(cls, endpoint):
        """Filter errors by endpoint"""
        return cls.objects.filter(endpoint__icontains=endpoint)
    
    @classmethod
    def get_unresolved_count(cls):
        """Get count of unresolved errors"""
        return cls.objects.filter(is_resolved=False).count()
    
    @classmethod
    def get_recent_errors(cls, hours=24, limit=100):
        """Get recent errors within specified hours"""
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(timestamp__gte=cutoff).order_by('-timestamp')[:limit]