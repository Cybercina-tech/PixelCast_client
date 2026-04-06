"""
Admin configuration for core models.
"""
from django.contrib import admin
from core.models import AuditLog, SystemBackup


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog."""
    list_display = [
        'timestamp',
        'username',
        'user_role',
        'action_type',
        'resource_type',
        'resource_name',
        'severity',
        'success',
        'ip_address',
    ]
    list_filter = [
        'action_type',
        'severity',
        'success',
        'resource_type',
        'timestamp',
    ]
    search_fields = [
        'username',
        'resource_name',
        'description',
        'ip_address',
    ]
    readonly_fields = [
        'id',
        'timestamp',
        'user',
        'username',
        'user_role',
        'changes',
        'metadata',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(SystemBackup)
class SystemBackupAdmin(admin.ModelAdmin):
    """Admin interface for SystemBackup."""
    list_display = [
        'id',
        'backup_type',
        'status',
        'file_size',
        'started_at',
        'completed_at',
        'created_by',
        'scheduled',
    ]
    list_filter = [
        'backup_type',
        'status',
        'scheduled',
        'compression',
        'encryption',
    ]
    search_fields = [
        'file_path',
        'schedule_name',
    ]
    readonly_fields = [
        'id',
        'status',
        'file_path',
        'file_size',
        'checksum',
        'started_at',
        'completed_at',
    ]
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
