"""
Serializers for bulk operations.

Provides validation and serialization for bulk operation requests and responses.
"""
from rest_framework import serializers
from typing import List, Dict, Any


class BulkOperationRequestSerializer(serializers.Serializer):
    """
    Base serializer for bulk operation requests.
    Validates list of item IDs.
    """
    item_ids = serializers.ListField(
        child=serializers.CharField(max_length=128),
        min_length=1,
        max_length=1000,
        help_text="List of item IDs to operate on (max 1000 items)"
    )
    
    def validate_item_ids(self, value):
        """Validate item IDs are non-empty strings"""
        if not value:
            raise serializers.ValidationError("At least one item ID is required")
        
        # Filter out empty strings
        valid_ids = [id for id in value if id and id.strip()]
        if not valid_ids:
            raise serializers.ValidationError("No valid item IDs provided")
        
        return valid_ids


class BulkUpdateRequestSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk update requests.
    Accepts item IDs and update data.
    """
    update_data = serializers.DictField(
        required=True,
        help_text="Dictionary of fields to update"
    )
    
    def validate_update_data(self, value):
        """Validate update data is not empty"""
        if not value:
            raise serializers.ValidationError("update_data cannot be empty")
        return value


class BulkScreenActivateTemplateSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk activate template on screens.
    """
    template_id = serializers.UUIDField(
        required=True,
        help_text="Template ID to activate on screens"
    )
    sync_content = serializers.BooleanField(
        default=True,
        help_text="Whether to sync content after activation"
    )


class BulkScreenSendCommandSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk send command to screens.
    """
    command_type = serializers.ChoiceField(
        choices=[
            ('restart', 'Restart'),
            ('refresh', 'Refresh'),
            ('change_template', 'Change Template'),
            ('display_message', 'Display Message'),
            ('sync_content', 'Sync Content'),
            ('custom', 'Custom'),
        ],
        required=True,
        help_text="Type of command to send"
    )
    payload = serializers.DictField(
        default=dict,
        help_text="Command payload (optional)"
    )
    priority = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text="Command priority (default: 0)"
    )


class BulkTemplateActivateSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk activate templates.
    """
    is_active = serializers.BooleanField(
        required=True,
        help_text="Set templates as active (True) or inactive (False)"
    )


class BulkTemplateActivateOnScreensSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk activate templates on screens.
    """
    screen_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of screen IDs to activate templates on"
    )
    sync_content = serializers.BooleanField(
        default=True,
        help_text="Whether to sync content after activation"
    )


class BulkContentDownloadSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk download content to screens.
    """
    screen_id = serializers.UUIDField(
        required=True,
        help_text="Screen ID to download content to"
    )
    max_retries = serializers.IntegerField(
        default=3,
        min_value=1,
        max_value=10,
        help_text="Maximum number of retry attempts"
    )


class BulkContentRetrySerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk retry content download.
    """
    screen_id = serializers.UUIDField(
        required=True,
        help_text="Screen ID to retry download on"
    )
    max_retries = serializers.IntegerField(
        default=3,
        min_value=1,
        max_value=10,
        help_text="Maximum number of retry attempts"
    )


class BulkScheduleActivateSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk activate schedules.
    """
    is_active = serializers.BooleanField(
        required=True,
        help_text="Set schedules as active (True) or inactive (False)"
    )


class BulkScheduleExecuteSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk execute schedules.
    """
    force = serializers.BooleanField(
        default=False,
        help_text="Force execution even if schedule is not due"
    )


class BulkCommandExecuteSerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk execute commands.
    """
    screen_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional screen ID override for command execution"
    )


class BulkCommandRetrySerializer(BulkOperationRequestSerializer):
    """
    Serializer for bulk retry commands.
    """
    pass
