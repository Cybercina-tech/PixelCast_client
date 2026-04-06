"""
Custom OpenAPI schemas and examples for PixelCast Signage API.

Provides reusable schemas, examples, and security definitions.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status


# Common Parameters
SCREEN_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description='Screen UUID',
    required=True,
    examples=[
        OpenApiExample(
            'Example UUID',
            value='123e4567-e89b-12d3-a456-426614174000'
        )
    ]
)

TEMPLATE_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description='Template UUID',
    required=True,
)

COMMAND_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description='Command UUID',
    required=True,
)

CONTENT_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description='Content UUID',
    required=True,
)

SCHEDULE_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description='Schedule UUID',
    required=True,
)

USER_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description='User ID',
    required=True,
)

# Query Parameters
DATE_START_PARAMETER = OpenApiParameter(
    name='start_date',
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    description='Start date (YYYY-MM-DD)',
    required=False,
    examples=[
        OpenApiExample('Example date', value='2024-01-01')
    ]
)

DATE_END_PARAMETER = OpenApiParameter(
    name='end_date',
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    description='End date (YYYY-MM-DD)',
    required=False,
    examples=[
        OpenApiExample('Example date', value='2024-01-31')
    ]
)

SCREEN_IDS_PARAMETER = OpenApiParameter(
    name='screen_ids',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description='Comma-separated list of screen UUIDs',
    required=False,
    examples=[
        OpenApiExample('Single screen', value='123e4567-e89b-12d3-a456-426614174000'),
        OpenApiExample('Multiple screens', value='123e4567-e89b-12d3-a456-426614174000,789e0123-e89b-12d3-a456-426614174001')
    ]
)

PERIOD_PARAMETER = OpenApiParameter(
    name='period',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description='Aggregation period',
    required=False,
    enum=['day', 'week', 'month'],
    examples=[
        OpenApiExample('Daily', value='day'),
        OpenApiExample('Weekly', value='week'),
        OpenApiExample('Monthly', value='month'),
    ]
)

PAGE_PARAMETER = OpenApiParameter(
    name='page',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    description='Page number',
    required=False,
    examples=[OpenApiExample('Page 1', value=1)]
)

PAGE_SIZE_PARAMETER = OpenApiParameter(
    name='page_size',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    description='Number of items per page',
    required=False,
    examples=[OpenApiExample('50 items', value=50)]
)

# Response Examples
ERROR_400_EXAMPLE = OpenApiExample(
    'Validation Error',
    value={
        'status': 'error',
        'error': 'Invalid input data',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    response_only=True,
    status_codes=[status.HTTP_400_BAD_REQUEST]
)

ERROR_401_EXAMPLE = OpenApiExample(
    'Unauthorized',
    value={
        'detail': 'Authentication credentials were not provided.'
    },
    response_only=True,
    status_codes=[status.HTTP_401_UNAUTHORIZED]
)

ERROR_403_EXAMPLE = OpenApiExample(
    'Forbidden',
    value={
        'detail': 'You do not have permission to perform this action.'
    },
    response_only=True,
    status_codes=[status.HTTP_403_FORBIDDEN]
)

ERROR_404_EXAMPLE = OpenApiExample(
    'Not Found',
    value={
        'status': 'error',
        'error': 'Resource not found',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    response_only=True,
    status_codes=[status.HTTP_404_NOT_FOUND]
)

ERROR_500_EXAMPLE = OpenApiExample(
    'Internal Server Error',
    value={
        'status': 'error',
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    response_only=True,
    status_codes=[status.HTTP_500_INTERNAL_SERVER_ERROR]
)


# Security Scheme Tags
SECURITY_SCHEME_JWT = {
    'type': 'http',
    'scheme': 'bearer',
    'bearerFormat': 'JWT',
    'description': 'JWT token obtained from /api/auth/token/ endpoint. Include in Authorization header as: Bearer <token>'
}

SECURITY_SCHEME_SESSION = {
    'type': 'apiKey',
    'in': 'cookie',
    'name': 'sessionid',
    'description': 'Session cookie for browser-based authentication'
}


# Tags for grouping endpoints
TAGS = {
    'authentication': 'Authentication',
    'users': 'Users & Roles',
    'screens': 'Screens',
    'templates': 'Templates',
    'layers': 'Layers',
    'widgets': 'Widgets',
    'contents': 'Contents',
    'schedules': 'Schedules',
    'commands': 'Commands',
    'logs': 'Logs',
    'analytics': 'Analytics',
    'bulk_operations': 'Bulk Operations',
    'content_validation': 'Content Validation',
    'core': 'Core Infrastructure',
}
