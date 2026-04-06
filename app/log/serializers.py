from rest_framework import serializers
from django.utils import timezone
from .models import ScreenStatusLog, ContentDownloadLog, CommandExecutionLog, ErrorLog


class ScreenStatusLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ScreenStatusLog model.
    Includes all relevant fields and calculated display fields.
    """
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    screen_id = serializers.UUIDField(source='screen.id', read_only=True)
    screen_device_id = serializers.CharField(source='screen.device_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ScreenStatusLog
        fields = [
            'id', 'screen', 'screen_id', 'screen_name', 'screen_device_id',
            'status', 'status_display', 'heartbeat_latency', 'cpu_usage',
            'memory_usage', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class ContentDownloadLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ContentDownloadLog model.
    Includes all relevant fields and calculated display fields.
    """
    content_name = serializers.CharField(source='content.name', read_only=True)
    content_id = serializers.UUIDField(source='content.id', read_only=True)
    content_type = serializers.CharField(source='content.type', read_only=True)
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    screen_id = serializers.UUIDField(source='screen.id', read_only=True)
    screen_device_id = serializers.CharField(source='screen.device_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    file_size_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentDownloadLog
        fields = [
            'id', 'content', 'content_id', 'content_name', 'content_type',
            'screen', 'screen_id', 'screen_name', 'screen_device_id',
            'status', 'status_display', 'retry_count', 'file_size',
            'file_size_mb', 'file_size_gb', 'error_message',
            'downloaded_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def get_file_size_gb(self, obj):
        """Convert file size to GB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024 * 1024), 2)
        return None


class CommandExecutionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for CommandExecutionLog model.
    Includes all relevant fields and calculated display fields.
    """
    command_name = serializers.CharField(source='command.name', read_only=True)
    command_id = serializers.UUIDField(source='command.id', read_only=True)
    command_type = serializers.CharField(source='command.type', read_only=True)
    command_type_display = serializers.CharField(source='command.get_type_display', read_only=True)
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    screen_id = serializers.UUIDField(source='screen.id', read_only=True)
    screen_device_id = serializers.CharField(source='screen.device_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    execution_time = serializers.SerializerMethodField()
    execution_time_ms = serializers.SerializerMethodField()
    
    class Meta:
        model = CommandExecutionLog
        fields = [
            'id', 'command', 'command_id', 'command_name', 'command_type',
            'command_type_display', 'screen', 'screen_id', 'screen_name',
            'screen_device_id', 'status', 'status_display', 'started_at',
            'finished_at', 'execution_time', 'execution_time_ms',
            'response_payload', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_execution_time(self, obj):
        """Get execution time in seconds"""
        return obj.execution_time
    
    def get_execution_time_ms(self, obj):
        """Get execution time in milliseconds"""
        exec_time = obj.execution_time
        if exec_time is not None:
            return round(exec_time * 1000, 2)
        return None


class LogSummarySerializer(serializers.Serializer):
    """
    Serializer for log summary statistics.
    Flexible serializer that handles different summary types.
    """
    total_count = serializers.IntegerField()
    
    # ScreenStatusLog specific
    online_count = serializers.IntegerField(required=False, allow_null=True)
    offline_count = serializers.IntegerField(required=False, allow_null=True)
    online_percentage = serializers.FloatField(required=False, allow_null=True)
    average_latency_ms = serializers.FloatField(required=False, allow_null=True)
    average_cpu_usage = serializers.FloatField(required=False, allow_null=True)
    average_memory_usage = serializers.FloatField(required=False, allow_null=True)
    
    # ContentDownloadLog specific
    success_count = serializers.IntegerField(required=False, allow_null=True)
    failed_count = serializers.IntegerField(required=False, allow_null=True)
    pending_count = serializers.IntegerField(required=False, allow_null=True)
    success_rate = serializers.FloatField(required=False, allow_null=True)
    total_size_bytes = serializers.IntegerField(required=False, allow_null=True)
    total_size_mb = serializers.FloatField(required=False, allow_null=True)
    average_retry_count = serializers.FloatField(required=False, allow_null=True)
    
    # CommandExecutionLog specific
    done_count = serializers.IntegerField(required=False, allow_null=True)
    running_count = serializers.IntegerField(required=False, allow_null=True)
    average_execution_time_seconds = serializers.FloatField(required=False, allow_null=True)


class ErrorLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ErrorLog model.
    Includes all relevant fields and user information.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'timestamp', 'level', 'level_display', 'message', 'user',
            'user_id', 'user_username', 'user_email', 'stack_trace', 'endpoint',
            'request_method', 'ip_address', 'user_agent', 'exception_type',
            'metadata', 'is_resolved', 'resolved_at', 'resolved_by',
            'resolved_by_username'
        ]
        read_only_fields = ['id', 'timestamp']
