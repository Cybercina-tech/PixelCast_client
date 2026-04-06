"""
Django Admin configuration for Notifications app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import NotificationEvent, NotificationChannel, NotificationRule, NotificationLog


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    """Admin interface for NotificationEvent"""
    list_display = ['event_key', 'severity', 'is_active', 'created_at']
    list_filter = ['severity', 'is_active', 'created_at']
    search_fields = ['event_key', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['event_key']


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Admin interface for NotificationChannel"""
    list_display = ['name', 'type', 'is_enabled', 'organization', 'created_at']
    list_filter = ['type', 'is_enabled', 'created_at']
    search_fields = ['name', 'type']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['type', 'name']
    
    # Don't show encrypted config directly
    exclude = ['config']
    
    def get_readonly_fields(self, request, obj=None):
        """Make config read-only (encrypted)"""
        return self.readonly_fields + ['config']


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    """Admin interface for NotificationRule"""
    list_display = ['event', 'severity_threshold', 'cooldown_seconds', 'is_enabled', 'organization', 'created_at']
    list_filter = ['is_enabled', 'severity_threshold', 'created_at']
    search_fields = ['event__event_key']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['channels']
    ordering = ['-is_enabled', 'event__event_key']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin interface for NotificationLog"""
    list_display = ['event_key', 'channel_type', 'status', 'retry_count', 'created_at', 'sent_at']
    list_filter = ['status', 'event_key', 'created_at']
    search_fields = ['event_key', 'idempotency_key']
    readonly_fields = ['id', 'created_at', 'sent_at']
    ordering = ['-created_at']
    
    def channel_type(self, obj):
        """Display channel type"""
        return obj.channel.type if obj.channel else 'N/A'
    channel_type.short_description = 'Channel Type'
