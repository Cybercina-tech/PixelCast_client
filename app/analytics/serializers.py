"""
Serializers for analytics API responses.

Provides consistent response formatting for all analytics endpoints.
"""
from rest_framework import serializers
from typing import Dict, Any, Optional


class ScreenStatisticsSerializer(serializers.Serializer):
    """Serializer for screen statistics response."""
    total_screens = serializers.IntegerField()
    status_breakdown = serializers.DictField()
    health_metrics = serializers.DictField()
    health_score = serializers.FloatField()
    period = serializers.DictField(required=False)


class ScreenDetailSerializer(serializers.Serializer):
    """Serializer for detailed screen analytics."""
    screen_id = serializers.UUIDField()
    screen_name = serializers.CharField()
    device_id = serializers.CharField()
    is_online = serializers.BooleanField()
    current_metrics = serializers.DictField()
    recent_averages = serializers.DictField()
    status = serializers.DictField()
    command_statistics = serializers.DictField()
    active_template = serializers.DictField(required=False, allow_null=True)


class CommandStatisticsSerializer(serializers.Serializer):
    """Serializer for command statistics response."""
    overall = serializers.DictField()
    by_type = serializers.ListField(child=serializers.DictField())
    by_status = serializers.ListField(child=serializers.DictField())
    time_series = serializers.ListField(child=serializers.DictField())
    period = serializers.CharField()


class ContentStatisticsSerializer(serializers.Serializer):
    """Serializer for content statistics response."""
    download_statistics = serializers.DictField()
    type_distribution = serializers.ListField(child=serializers.DictField())
    downloads_by_type = serializers.ListField(child=serializers.DictField())
    total_content_items = serializers.IntegerField()


class TemplateStatisticsSerializer(serializers.Serializer):
    """Serializer for template statistics response."""
    total_templates = serializers.IntegerField()
    total_active_screens = serializers.IntegerField()
    most_active_templates = serializers.ListField(child=serializers.DictField())
    by_orientation = serializers.ListField(child=serializers.DictField())


class ActivityTrendsSerializer(serializers.Serializer):
    """Serializer for activity trends response."""
    period = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    screen_registrations = serializers.ListField(child=serializers.DictField())
    commands_created = serializers.ListField(child=serializers.DictField())
    templates_created = serializers.ListField(child=serializers.DictField())
    content_uploads = serializers.ListField(child=serializers.DictField())


class AnalyticsResponseSerializer(serializers.Serializer):
    """Base serializer for analytics API responses."""
    status = serializers.CharField(default='success')
    data = serializers.DictField()
    metadata = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField(required=False)
