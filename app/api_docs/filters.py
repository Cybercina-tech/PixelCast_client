"""
Custom filters for excluding sensitive fields from OpenAPI schema.

This module provides security-aware schema generation that automatically
excludes sensitive fields from API documentation.
"""
from drf_spectacular.openapi import AutoSchema
import re


class SecureAutoSchema(AutoSchema):
    """
    Custom schema generator that excludes sensitive fields.
    
    Automatically excludes passwords, tokens, secrets, and other sensitive data
    from OpenAPI schema generation to prevent accidental exposure in documentation.
    
    Usage:
        In settings.py:
        SPECTACULAR_SETTINGS = {
            'DEFAULT_SCHEMA_CLASS': 'api_docs.filters.SecureAutoSchema',
            ...
        }
    """
    
    # Fields to exclude from all schemas
    SENSITIVE_FIELD_NAMES = [
        'password',
        'secret',
        'token',
        'api_key',
        'access_key',
        'private_key',
        'auth_token',
        'secret_key',
        'encryption_key',
        'refresh_token',
        'access_token',
        'bearer_token',
        'session_key',
        'session_id',
        'csrf_token',
        'csrfmiddlewaretoken',
    ]
    
    # Field patterns to exclude (regex)
    SENSITIVE_PATTERNS = [
        r'.*password.*',
        r'.*secret.*',
        r'.*token.*',
        r'.*key.*',
        r'.*credential.*',
        r'.*auth.*',
    ]
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field name is sensitive."""
        field_lower = field_name.lower()
        
        # Check exact matches
        if field_lower in self.SENSITIVE_FIELD_NAMES:
            return True
        
        # Check patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if re.match(pattern, field_lower):
                return True
        
        return False
    
    def _get_serializer(self, path, method):
        """Override to exclude sensitive fields from serializers."""
        serializer = super()._get_serializer(path, method)
        
        if serializer and hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'fields'):
            # Filter out sensitive fields
            if isinstance(serializer.Meta.fields, (list, tuple)):
                filtered_fields = [
                    field for field in serializer.Meta.fields
                    if not self._is_sensitive_field(field)
                ]
                serializer.Meta.fields = tuple(filtered_fields)
        
        return serializer
    
    def _map_serializer(self, serializer, direction):
        """Map serializer while excluding sensitive fields."""
        # Get mapped schema
        schema = super()._map_serializer(serializer, direction)
        
        # Filter properties if schema has them
        if schema and 'properties' in schema:
            schema['properties'] = {
                k: v for k, v in schema['properties'].items()
                if not self._is_sensitive_field(k)
            }
            
            # Update required fields
            if 'required' in schema:
                schema['required'] = [
                    field for field in schema['required']
                    if not self._is_sensitive_field(field)
                ]
        
        return schema
