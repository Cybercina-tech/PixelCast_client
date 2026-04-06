"""
Example request/response data for API documentation.

Provides realistic examples for all endpoints.
"""
from drf_spectacular.utils import OpenApiExample


# Authentication Examples
LOGIN_REQUEST_EXAMPLE = OpenApiExample(
    'Login Request',
    value={
        'username': 'admin',
        'password': 'admin123'
    },
    request_only=True,
)

LOGIN_RESPONSE_EXAMPLE = OpenApiExample(
    'Login Response',
    value={
        'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
    },
    response_only=True,
)


# Screen Examples
SCREEN_CREATE_EXAMPLE = OpenApiExample(
    'Create Screen',
    value={
        'name': 'Lobby Display 1',
        'device_id': 'device-001',
        'location': 'Main Lobby',
        'description': 'Primary display in main lobby'
    },
    request_only=True,
)

SCREEN_RESPONSE_EXAMPLE = OpenApiExample(
    'Screen Response',
    value={
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'name': 'Lobby Display 1',
        'device_id': 'device-001',
        'is_online': True,
        'last_heartbeat_at': '2024-01-15T10:30:00Z'
    },
    response_only=True,
)


# Template Examples
TEMPLATE_CREATE_EXAMPLE = OpenApiExample(
    'Create Template',
    value={
        'name': 'Welcome Template',
        'description': 'Welcome message template',
        'width': 1920,
        'height': 1080,
        'orientation': 'landscape'
    },
    request_only=True,
)

TEMPLATE_RESPONSE_EXAMPLE = OpenApiExample(
    'Template Response',
    value={
        'id': '456e7890-e89b-12d3-a456-426614174001',
        'name': 'Welcome Template',
        'width': 1920,
        'height': 1080,
        'is_active': True
    },
    response_only=True,
)


# Command Examples
COMMAND_CREATE_EXAMPLE = OpenApiExample(
    'Create Command',
    value={
        'type': 'restart',
        'screen_id': '123e4567-e89b-12d3-a456-426614174000',
        'priority': 5,
        'payload': {}
    },
    request_only=True,
)

COMMAND_RESPONSE_EXAMPLE = OpenApiExample(
    'Command Response',
    value={
        'id': '789e0123-e89b-12d3-a456-426614174002',
        'type': 'restart',
        'status': 'pending',
        'created_at': '2024-01-15T10:30:00Z'
    },
    response_only=True,
)


# Content Examples
CONTENT_UPLOAD_EXAMPLE = OpenApiExample(
    'Upload Content',
    value={
        'name': 'Company Logo',
        'type': 'image',
        'file': '<binary file data>',
        'description': 'Company logo image'
    },
    request_only=True,
)

CONTENT_RESPONSE_EXAMPLE = OpenApiExample(
    'Content Response',
    value={
        'id': 'abc12345-e89b-12d3-a456-426614174003',
        'name': 'Company Logo',
        'type': 'image',
        'download_status': 'success',
        'file_size': 1024000
    },
    response_only=True,
)


# Analytics Examples
ANALYTICS_SCREEN_STATS_EXAMPLE = OpenApiExample(
    'Screen Statistics',
    value={
        'total_screens': 10,
        'status_breakdown': {
            'online': 8,
            'offline': 2
        },
        'health_metrics': {
            'avg_cpu_usage': 25.5,
            'avg_memory_usage': 45.0
        }
    },
    response_only=True,
)


# Error Examples
VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    'Validation Error',
    value={
        'status': 'error',
        'error': 'Invalid input data',
        'field_errors': {
            'name': ['This field is required.'],
            'device_id': ['Device ID must be unique.']
        },
        'timestamp': '2024-01-15T10:30:00Z'
    },
    response_only=True,
)

PERMISSION_ERROR_EXAMPLE = OpenApiExample(
    'Permission Denied',
    value={
        'detail': 'You do not have permission to perform this action.'
    },
    response_only=True,
)


# Core Infrastructure Examples
AUDIT_LOG_LIST_EXAMPLE = OpenApiExample(
    'Audit Log List',
    value={
        'count': 150,
        'next': 'http://localhost:8000/api/core/audit-logs/?page=2',
        'previous': None,
        'results': [
            {
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'username': 'admin',
                'user_role': 'Developer',
                'action_type': 'create',
                'resource_type': 'Screen',
                'resource_name': 'Lobby Display 1',
                'severity': 'medium',
                'success': True,
                'timestamp': '2024-01-15T10:30:00Z',
            }
        ]
    },
    response_only=True,
)

BACKUP_TRIGGER_REQUEST_EXAMPLE = OpenApiExample(
    'Trigger Backup Request',
    value={
        'backup_type': 'database',
        'compression': True,
        'include_media': False,
    },
    request_only=True,
)

BACKUP_RESPONSE_EXAMPLE = OpenApiExample(
    'Backup Response',
    value={
        'id': '456e7890-e89b-12d3-a456-426614174001',
        'backup_type': 'database',
        'status': 'completed',
        'file_path': '/backups/db_backup_20240115_103000.sql.gz',
        'file_size': 5242880,
        'file_size_mb': 5.0,
        'checksum': 'abc123def456...',
        'started_at': '2024-01-15T10:30:00Z',
        'completed_at': '2024-01-15T10:30:15Z',
        'duration_seconds': 15,
    },
    response_only=True,
)

BACKUP_VERIFY_RESPONSE_EXAMPLE = OpenApiExample(
    'Backup Verification Response',
    value={
        'is_valid': True,
        'checksum_match': True,
    },
    response_only=True,
)
