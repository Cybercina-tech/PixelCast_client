from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin for Digital Signage System.
    
    Extends Django's default UserAdmin to show additional fields,
    resource counts, and role-based filtering.
    """
    
    # Fields to display in list view
    list_display = [
        'username', 'email', 'full_name', 'role', 'organization_name',
        'screens_count', 'templates_count', 'is_active', 'last_seen', 'date_joined'
    ]
    
    # Fields for filtering
    list_filter = [
        'role', 'is_active', 'is_staff', 'is_superuser',
        'organization_name', 'date_joined'
    ]
    
    # Fields for searching
    search_fields = [
        'username', 'email', 'full_name', 'phone_number', 'organization_name'
    ]
    
    # Fields to display in detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Role & Organization', {
            'fields': ('role', 'organization_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'last_seen')
        }),
    )
    
    # Fields for add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'full_name', 'role'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ['last_login', 'date_joined', 'last_seen', 'failed_login_attempts', 'locked_until']
    
    # Ordering
    ordering = ['-date_joined']
    
    # Custom methods for list display
    def screens_count(self, obj):
        """Display total screens count with active count"""
        total = obj.total_screens_count
        active = obj.active_screens_count
        if total > 0:
            color = 'green' if active > 0 else 'gray'
            return format_html(
                '<span style="color: {};">{}/{} active</span>',
                color, active, total
            )
        return format_html('<span style="color: gray;">0</span>')
    screens_count.short_description = 'Screens'
    screens_count.admin_order_field = 'owned_screens__count'
    
    def templates_count(self, obj):
        """Display total templates count with active count"""
        total = obj.total_templates_count
        active = obj.active_templates_count
        if total > 0:
            color = 'green' if active > 0 else 'gray'
            return format_html(
                '<span style="color: {};">{}/{} active</span>',
                color, active, total
            )
        return format_html('<span style="color: gray;">0</span>')
    templates_count.short_description = 'Templates'
    templates_count.admin_order_field = 'created_templates__count'
    
    # Actions
    actions = ['make_manager', 'make_viewer', 'deactivate_users']
    
    def make_manager(self, request, queryset):
        """Action to set selected users as Manager"""
        queryset.update(role='Manager')
        self.message_user(request, f"{queryset.count()} users set as Manager.")
    make_manager.short_description = "Set selected users as Manager"
    
    def make_viewer(self, request, queryset):
        """Action to set selected users as Viewer"""
        queryset.update(role='Viewer')
        self.message_user(request, f"{queryset.count()} users set as Viewer.")
    make_viewer.short_description = "Set selected users as Viewer"
    
    def deactivate_users(self, request, queryset):
        """Action to deactivate selected users"""
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated.")
    deactivate_users.short_description = "Deactivate selected users"
