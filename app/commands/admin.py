from django.contrib import admin
from django.utils.html import format_html
from .models import Command


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    """
    Admin interface for Command model.
    
    Provides filtering, searching, and actions for managing commands.
    """
    
    # Fields to display in list view
    list_display = [
        'id', 'screen', 'type', 'status', 'priority', 'created_by',
        'is_expired_display', 'attempt_count', 'created_at', 'expire_at'
    ]
    
    # Fields for filtering
    list_filter = [
        'status', 'type', 'priority', 'created_at', 'expire_at', 'screen'
    ]
    
    # Fields for searching
    search_fields = [
        'name', 'screen__name', 'screen__device_id', 'created_by__username',
        'created_by__email'
    ]
    
    # Fields to display in detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'screen', 'created_by', 'type')
        }),
        ('Command Details', {
            'fields': ('payload', 'priority', 'expire_at')
        }),
        ('Status & Execution', {
            'fields': ('status', 'attempt_count', 'last_attempt_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'last_attempt_at']
    
    # Ordering
    ordering = ['-priority', '-created_at']
    
    # Custom display methods
    def is_expired_display(self, obj):
        """Display expiry status with color coding"""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.expire_at:
            time_left = obj.time_until_expiry
            if time_left and time_left < 3600:  # Less than 1 hour
                return format_html('<span style="color: orange;">Expiring Soon</span>')
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: gray;">No Expiry</span>')
    is_expired_display.short_description = 'Expiry Status'
    
    # Actions
    actions = ['mark_as_done', 'mark_as_failed', 'reset_to_pending', 'execute_commands']
    
    def mark_as_done(self, request, queryset):
        """Action to mark selected commands as done"""
        count = 0
        for command in queryset:
            command.mark_done()
            count += 1
        self.message_user(request, f"{count} command(s) marked as done.")
    mark_as_done.short_description = "Mark selected commands as done"
    
    def mark_as_failed(self, request, queryset):
        """Action to mark selected commands as failed"""
        count = 0
        for command in queryset:
            command.mark_failed()
            count += 1
        self.message_user(request, f"{count} command(s) marked as failed.")
    mark_as_failed.short_description = "Mark selected commands as failed"
    
    def reset_to_pending(self, request, queryset):
        """Action to reset selected commands to pending"""
        count = 0
        for command in queryset:
            command.reset_status()
            count += 1
        self.message_user(request, f"{count} command(s) reset to pending.")
    reset_to_pending.short_description = "Reset selected commands to pending"
    
    def execute_commands(self, request, queryset):
        """Action to execute selected commands"""
        count = 0
        success = 0
        for command in queryset:
            if command.execute_command():
                success += 1
            count += 1
        self.message_user(
            request,
            f"Executed {count} command(s). {success} successful, {count - success} failed."
        )
    execute_commands.short_description = "Execute selected commands"
