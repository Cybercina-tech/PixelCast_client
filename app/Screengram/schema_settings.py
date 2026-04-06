"""
OpenAPI/Swagger schema configuration for PixelCast Signage API.

Defines schema generation settings, security schemes, and metadata.

This file is imported by settings.py to configure drf-spectacular.
"""
# OpenAPI Schema Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'PixelCast Signage API',
    'DESCRIPTION': """
# PixelCast Signage Digital Signage Management API

Complete API documentation for PixelCast Signage backend, covering all endpoints for managing screens, templates, content, schedules, commands, users, analytics, audit logs, and backups.

## Authentication

Most endpoints require JWT authentication. Obtain a token by calling `/api/auth/token/` with your credentials.

### Using JWT Token

Include the token in the Authorization header:
```
Authorization: Bearer <your-access-token>
```

Tokens expire after 60 minutes. Use `/api/auth/token/refresh/` to get a new token.

## Permissions

- **SuperAdmin**: Full access to all resources and system administration
- **Admin**: Full access to all resources
- **Manager**: Can manage own resources, view analytics, and access audit logs
- **Operator**: Can manage assigned screens and templates
- **Viewer**: Read-only access

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Default: 60 requests per minute, 1000 per hour, 10000 per day
- Analytics endpoints: 100 requests per 60 seconds per user
- Role-based limits: Different limits apply based on user role
- Rate limit headers are included in responses

## Security

- All sensitive fields (passwords, tokens, secrets) are excluded from documentation
- Swagger/ReDoc/OpenAPI schema are readable without login; APIs still enforce JWT where applicable
- HTTPS is required in production
- Audit logging tracks all critical actions
- Backup files are stored securely with integrity verification

## Core Infrastructure

- **Audit Logging**: Comprehensive tracking of all system actions
- **Backups**: Automated database and media file backups
- **Caching**: Redis-based caching for improved performance
- **Rate Limiting**: Protection against abuse and DDoS attacks

## Support

For API support or questions, contact the development team.
""",
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    
    # Security Schemes
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT token obtained from /api/auth/token/ endpoint'
            },
            'SessionAuth': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'sessionid',
                'description': 'Session cookie for browser-based authentication'
            },
        }
    },
    
    # Default Security
    'SECURITY': [
        {
            'BearerAuth': [],
        }
    ],
    
    # Tags
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and token management'},
        {'name': 'Users & Roles', 'description': 'User management and role-based access control'},
        {'name': 'Screens', 'description': 'Digital signage screen management and monitoring'},
        {'name': 'Templates', 'description': 'Template creation and management'},
        {'name': 'Layers', 'description': 'Template layer management'},
        {'name': 'Widgets', 'description': 'Widget management within layers'},
        {'name': 'Contents', 'description': 'Content (media files) management'},
        {'name': 'Schedules', 'description': 'Content scheduling and automation'},
        {'name': 'Commands', 'description': 'Real-time command execution on screens'},
        {'name': 'Logs', 'description': 'System logs and audit trails'},
        {'name': 'Analytics', 'description': 'Analytics and statistics dashboard'},
        {'name': 'Bulk Operations', 'description': 'Bulk CRUD operations for multiple resources'},
        {'name': 'Content Validation', 'description': 'Content validation and security checks'},
        {'name': 'Core Infrastructure', 'description': 'Core infrastructure features: audit logging, backups, system management'},
    ],
    
    # Exclude sensitive fields
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'filter': True,
        'tryItOutEnabled': True,
        'supportedSubmitMethods': ['get', 'post', 'put', 'patch', 'delete'],
        'validatorUrl': None,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'expandResponses': '200,201',
        'pathInMiddlePanel': True,
    },
    
    # Customize schema generation
    'PREPROCESSING_HOOKS': [],
    'POSTPROCESSING_HOOKS': [],
    
    # Use custom schema class for security
    'SCHEMA_PATH_PREFIX_TRIM': True,
    
    # Exclude sensitive fields
    'SERVE_AUTHENTICATION': ['rest_framework.authentication.SessionAuthentication'],
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    
    # Custom schema class (optional, can use SecureAutoSchema)
    # 'DEFAULT_SCHEMA_CLASS': 'api_docs.filters.SecureAutoSchema',
    
    # Extension Settings
    'EXTENSIONS_INFO': {
        'x-logo': {
            'url': '/static/logo.png',
            'altText': 'PixelCast Signage Logo'
        }
    },
    
    # Exclude paths
    'EXCLUDE_PATH': [
        '/admin/',
        '/api/schema/',
        '/api/docs/',
        '/api/redoc/',
        '/static/',
        '/media/',
    ],
    
    # Authentication classes for schema generation
    'AUTHENTICATION_WHITELIST': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
