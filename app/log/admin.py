from django.contrib import admin
from django.utils.html import format_html
from .models import ScreenStatusLog, ContentDownloadLog, CommandExecutionLog


@admin.register(ScreenStatusLog)
class ScreenStatusLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Screen Status Logs.
    
    Read-only interface for monitoring screen health and status history.
    """
    
    list_display = [
        'screen', 'status', 'heartbeat_latency', 'cpu_usage', 'memory_usage', 'recorded_at'
    ]
    list_filter = ['status', 'recorded_at', 'screen']
    search_fields = ['screen__name', 'screen__device_id']
    readonly_fields = ['id', 'screen', 'status', 'heartbeat_latency', 'cpu_usage', 
                      'memory_usage', 'recorded_at']
    ordering = ['-recorded_at']
    date_hierarchy = 'recorded_at'
    
    def has_add_permission(self, request):
        """Disable manual addition - logs are created by backend services"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - logs are read-only"""
        return False


@admin.register(ContentDownloadLog)
class ContentDownloadLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Content Download Logs.
    
    Read-only interface for monitoring content download status and failures.
    """
    
    list_display = [
        'content', 'screen', 'status', 'retry_count', 'file_size_display', 
        'downloaded_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'screen', 'content']
    search_fields = [
        'content__name', 'screen__name', 'screen__device_id', 'error_message'
    ]
    readonly_fields = [
        'id', 'content', 'screen', 'status', 'retry_count', 'file_size',
        'error_message', 'downloaded_at', 'created_at'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size < 1024.0:
                    return f"{obj.file_size:.2f} {unit}"
                obj.file_size /= 1024.0
            return f"{obj.file_size:.2f} TB"
        return "-"
    file_size_display.short_description = 'File Size'
    
    def has_add_permission(self, request):
        """Disable manual addition - logs are created by backend services"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - logs are read-only"""
        return False


@admin.register(CommandExecutionLog)
class CommandExecutionLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Command Execution Logs.
    
    Read-only interface for monitoring command execution and responses.
    """
    
    list_display = [
        'command', 'screen', 'status', 'execution_time_display', 
        'started_at', 'finished_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'screen', 'command__type']
    search_fields = [
        'command__name', 'screen__name', 'screen__device_id', 'error_message'
    ]
    readonly_fields = [
        'id', 'command', 'screen', 'status', 'started_at', 'finished_at',
        'response_payload', 'error_message', 'created_at', 'execution_time_display'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def execution_time_display(self, obj):
        """Display execution time in human-readable format"""
        exec_time = obj.execution_time
        if exec_time is not None:
            if exec_time < 1:
                return f"{exec_time * 1000:.2f} ms"
            return f"{exec_time:.2f} s"
        return "-"
    execution_time_display.short_description = 'Execution Time'
    
    def has_add_permission(self, request):
        """Disable manual addition - logs are created by backend services"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - logs are read-only"""
        return False
