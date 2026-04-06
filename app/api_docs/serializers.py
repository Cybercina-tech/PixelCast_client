"""
Custom serializers for API documentation examples.

Provides example request/response schemas for documentation.
"""
from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response format."""
    status = serializers.CharField(default='error', help_text='Response status')
    error = serializers.CharField(help_text='Error message')
    message = serializers.CharField(required=False, help_text='Detailed error message')
    timestamp = serializers.DateTimeField(help_text='Error timestamp')


class SuccessResponseSerializer(serializers.Serializer):
    """Standard success response format."""
    status = serializers.CharField(default='success', help_text='Response status')
    data = serializers.DictField(help_text='Response data')
    timestamp = serializers.DateTimeField(required=False, help_text='Response timestamp')


class PaginatedResponseSerializer(serializers.Serializer):
    """Paginated response format."""
    count = serializers.IntegerField(help_text='Total number of items')
    next = serializers.URLField(required=False, allow_null=True, help_text='URL to next page')
    previous = serializers.URLField(required=False, allow_null=True, help_text='URL to previous page')
    results = serializers.ListField(help_text='List of items')
