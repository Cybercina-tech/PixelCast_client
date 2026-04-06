"""
Decorators for adding OpenAPI documentation to views.

Provides reusable decorators for common documentation patterns.
"""
from functools import wraps
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status


def analytics_required(view_func):
    """Decorator to mark endpoint as requiring Manager/Admin role."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    wrapper._analytics_required = True
    return wrapper


def exclude_sensitive_fields(serializer_class, fields_to_exclude):
    """
    Create a serializer with sensitive fields excluded.
    
    Args:
        serializer_class: Base serializer class
        fields_to_exclude: List of field names to exclude
        
    Returns:
        Modified serializer class
    """
    class ExcludedSerializer(serializer_class):
        class Meta(serializer_class.Meta):
            fields = [f for f in serializer_class.Meta.fields if f not in fields_to_exclude]
    
    return ExcludedSerializer


# Common response examples
SUCCESS_RESPONSE_200 = OpenApiExample(
    'Success',
    value={'status': 'success', 'data': {}},
    response_only=True,
    status_codes=[status.HTTP_200_OK]
)

CREATED_RESPONSE_201 = OpenApiExample(
    'Created',
    value={'id': '123e4567-e89b-12d3-a456-426614174000', 'status': 'created'},
    response_only=True,
    status_codes=[status.HTTP_201_CREATED]
)

BAD_REQUEST_400 = OpenApiExample(
    'Validation Error',
    value={
        'status': 'error',
        'error': 'Invalid input data',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    response_only=True,
    status_codes=[status.HTTP_400_BAD_REQUEST]
)

UNAUTHORIZED_401 = OpenApiExample(
    'Unauthorized',
    value={'detail': 'Authentication credentials were not provided.'},
    response_only=True,
    status_codes=[status.HTTP_401_UNAUTHORIZED]
)

FORBIDDEN_403 = OpenApiExample(
    'Forbidden',
    value={'detail': 'You do not have permission to perform this action.'},
    response_only=True,
    status_codes=[status.HTTP_403_FORBIDDEN]
)

NOT_FOUND_404 = OpenApiExample(
    'Not Found',
    value={
        'status': 'error',
        'error': 'Resource not found',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    response_only=True,
    status_codes=[status.HTTP_404_NOT_FOUND]
)
