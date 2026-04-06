"""
Sidebar configuration and permission mapping system.

This module defines:
1. Permission strings for various features
2. Role-to-permission mappings
3. Sidebar items configuration with required permissions
"""

from django.conf import settings

from core.deployment import is_client_deployment

# Permission constants
PERMISSIONS = {
    # Dashboard
    'view_dashboard': 'view_dashboard',
    
    # Screens
    'view_screens': 'view_screens',
    'create_screens': 'create_screens',
    'edit_screens': 'edit_screens',
    'delete_screens': 'delete_screens',
    
    # Templates
    'view_templates': 'view_templates',
    'create_templates': 'create_templates',
    'edit_templates': 'edit_templates',
    'delete_templates': 'delete_templates',
    
    # Contents
    'view_contents': 'view_contents',
    'create_contents': 'create_contents',
    'edit_contents': 'edit_contents',
    'delete_contents': 'delete_contents',
    
    # Schedules
    'view_schedules': 'view_schedules',
    'create_schedules': 'create_schedules',
    'edit_schedules': 'edit_schedules',
    'delete_schedules': 'delete_schedules',
    
    # Commands
    'view_commands': 'view_commands',
    'create_commands': 'create_commands',
    'execute_commands': 'execute_commands',
    
    # Users
    'view_users': 'view_users',
    'create_users': 'create_users',
    'edit_users': 'edit_users',
    'delete_users': 'delete_users',
    'manage_roles': 'manage_roles',
    
    # Logs
    'view_logs': 'view_logs',
    
    # Analytics
    'view_analytics': 'view_analytics',
    
    # Core Infrastructure
    'view_audit_logs': 'view_audit_logs',
    'view_backups': 'view_backups',
    'manage_backups': 'manage_backups',
    
    # Settings
    'view_settings': 'view_settings',
    'edit_settings': 'edit_settings',
    
    # Tickets / helpdesk
    'view_tickets': 'view_tickets',
    'create_tickets': 'create_tickets',

    # Admin
    'view_errors': 'view_errors',  # Developer only

    # Platform (SaaS super-admin)
    'view_platform': 'view_platform',
}

# Role to permissions mapping
ROLE_PERMISSIONS = {
    'Developer': [
        'view_dashboard',
        'view_screens', 'create_screens', 'edit_screens', 'delete_screens',
        'view_templates', 'create_templates', 'edit_templates', 'delete_templates',
        'view_contents', 'create_contents', 'edit_contents', 'delete_contents',
        'view_schedules', 'create_schedules', 'edit_schedules', 'delete_schedules',
        'view_commands', 'create_commands', 'execute_commands',
        'view_users', 'create_users', 'edit_users', 'delete_users', 'manage_roles',
        'view_logs',
        'view_analytics',
        'view_audit_logs',
        'view_backups', 'manage_backups',
        'view_settings', 'edit_settings',
        'view_errors',
        'view_platform',
        'view_tickets', 'create_tickets',
    ],
    'Manager': [
        'view_dashboard',
        'view_screens', 'create_screens', 'edit_screens', 'delete_screens',
        'view_templates', 'create_templates', 'edit_templates', 'delete_templates',
        'view_contents', 'create_contents', 'edit_contents', 'delete_contents',
        'view_schedules', 'create_schedules', 'edit_schedules', 'delete_schedules',
        'view_commands', 'create_commands', 'execute_commands',
        'view_users', 'create_users', 'edit_users', 'delete_users',
        'view_analytics',
        'view_tickets', 'create_tickets',
    ],
    'Employee': [
        'view_dashboard',
        'view_screens', 'create_screens', 'edit_screens',
        'view_templates', 'create_templates', 'edit_templates',
        'view_schedules', 'create_schedules', 'edit_schedules', 'delete_schedules',
        'view_contents', 'create_contents', 'edit_contents',
        'view_commands', 'create_commands', 'execute_commands',
        'view_logs',
        'view_analytics',
        'view_settings', 'edit_settings',
        'view_tickets', 'create_tickets',
    ],
    'Visitor': [
        'view_dashboard',
        'view_screens',
        'view_templates',
        'view_contents',
        'view_schedules',
        'view_commands',
        'view_logs',
        'view_analytics',
        'view_tickets',
    ],
}


def get_user_permissions(user):
    """
    Get all permissions for a user based on their role.
    
    Args:
        user: User instance
        
    Returns:
        set: Set of permission strings
    """
    if not user or not user.is_authenticated:
        return set()

    client_mode = is_client_deployment(getattr(settings, 'DEPLOYMENT_MODE', None))
    role = user.role
    if client_mode:
        if role == 'Developer':
            role = 'Manager'
        if user.is_superuser:
            return set(ROLE_PERMISSIONS.get('Manager', []))
        return set(ROLE_PERMISSIONS.get(role, []))

    if user.is_superuser or role == 'Developer':
        permissions = set(PERMISSIONS.values())
    else:
        permissions = set(ROLE_PERMISSIONS.get(role, []))

    return permissions


def has_permission(user, permission):
    """
    Check if user has a specific permission.
    
    Args:
        user: User instance
        permission: Permission string
        
    Returns:
        bool: True if user has permission
    """
    if not user or not user.is_authenticated:
        return False
    
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


# Sidebar items configuration
SIDEBAR_ITEMS = [
    {
        'id': 'dashboard',
        'title': 'Dashboard',
        'icon': 'HomeIcon',
        'path': '/dashboard',
        'required_permissions': ['view_dashboard'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'screens',
        'title': 'Screens',
        'icon': 'TvIcon',
        'path': '/screens',
        'required_permissions': ['view_screens'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'templates',
        'title': 'Templates',
        'icon': 'DocumentTextIcon',
        'path': '/templates',
        'required_permissions': ['view_templates'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'contents',
        'title': 'Media library',
        'icon': 'FolderIcon',
        'path': '/contents',
        'required_permissions': ['view_contents'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'schedules',
        'title': 'Playlists',
        'icon': 'ClockIcon',
        'path': '/schedules',
        'required_permissions': ['view_schedules'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'commands',
        'title': 'Commands',
        'icon': 'CommandLineIcon',
        'path': '/commands',
        'required_permissions': ['view_commands'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'users',
        'title': 'Team management',
        'icon': 'UsersIcon',
        'path': '/users',
        'required_permissions': ['view_users'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'logs',
        'title': 'Logs & Reports',
        'icon': 'DocumentChartBarIcon',
        'path': '/logs',
        'required_permissions': ['view_logs'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'analytics',
        'title': 'Analytics',
        'icon': 'ChartBarIcon',
        'path': '/analytics',
        'required_permissions': ['view_analytics'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'tickets',
        'title': 'Tickets',
        'icon': 'TicketIcon',
        'path': '/tickets',
        'required_permissions': ['view_tickets'],
        'badge': None,
        'children': None,
    },
    {
        'id': 'settings',
        'title': 'Settings',
        'icon': 'Cog6ToothIcon',
        'path': '/settings',
        'required_permissions': ['view_settings'],
        'badge': None,
        'children': None,
    },
]


def filter_sidebar_items(user):
    """
    Filter sidebar items based on user permissions.
    
    Args:
        user: User instance
        
    Returns:
        list: Filtered sidebar items that user has access to
    """
    if not user or not user.is_authenticated:
        return []

    items_source = list(SIDEBAR_ITEMS)
    user_permissions = get_user_permissions(user)
    filtered_items = []
    
    for item in items_source:
        # Check if user has all required permissions for this item
        required_perms = item.get('required_permissions', [])
        if not required_perms or all(perm in user_permissions for perm in required_perms):
            # Create a copy of the item
            filtered_item = item.copy()
            
            # Filter children if they exist
            if item.get('children'):
                filtered_children = []
                for child in item['children']:
                    child_perms = child.get('required_permissions', [])
                    if not child_perms or all(perm in user_permissions for perm in child_perms):
                        filtered_children.append(child)
                
                if filtered_children:
                    filtered_item['children'] = filtered_children
                else:
                    # If no children are accessible, don't include parent
                    continue
            
            filtered_items.append(filtered_item)
    
    return filtered_items

