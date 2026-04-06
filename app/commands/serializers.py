from rest_framework import serializers
from django.utils import timezone
from .models import Command
from log.models import CommandExecutionLog


class CommandSerializer(serializers.ModelSerializer):
    """Serializer for Command model"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payload_summary = serializers.CharField(read_only=True)
    is_executable = serializers.BooleanField(read_only=True)
    is_expired = serializers.SerializerMethodField()
    can_retry = serializers.SerializerMethodField()
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Command
        fields = [
            'id', 'name', 'type', 'type_display', 'payload', 'status', 'status_display',
            'screen', 'screen_name', 'created_by', 'created_by_username', 'priority',
            'expire_at', 'executed_at', 'completed_at', 'last_attempt_at',
            'attempt_count', 'error_message', 'payload_summary', 'is_executable',
            'is_expired', 'can_retry', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'executed_at', 'completed_at', 'last_attempt_at',
            'attempt_count', 'error_message', 'created_at', 'updated_at'
        ]
    
    def get_is_expired(self, obj):
        """Check if command is expired"""
        return obj.is_expired()
    
    def get_can_retry(self, obj):
        """Check if command can be retried"""
        return obj.can_retry()
    
    def validate(self, attrs):
        """Validate command data"""
        # Validate payload based on command type
        command_type = attrs.get('type', self.instance.type if self.instance else None)
        payload = attrs.get('payload', self.instance.payload if self.instance else {})
        
        if command_type == 'change_template' and payload:
            if 'template_id' not in payload:
                raise serializers.ValidationError({
                    'payload': 'change_template command requires template_id in payload'
                })
        
        if command_type == 'display_message' and payload:
            if 'message' not in payload:
                raise serializers.ValidationError({
                    'payload': 'display_message command requires message in payload'
                })
        
        if command_type == 'sync_content' and payload:
            if 'content_ids' in payload and not isinstance(payload.get('content_ids'), list):
                raise serializers.ValidationError({
                    'payload': 'sync_content command requires content_ids to be a list (can be empty for all)'
                })
        
        return attrs


class CommandCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating commands"""
    screen_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Command
        fields = [
            'name', 'type', 'payload', 'screen_id', 'priority', 'expire_at'
        ]
    
    def validate_screen_id(self, value):
        """Validate screen exists"""
        from signage.models import Screen
        try:
            screen = Screen.objects.get(id=value)
        except Screen.DoesNotExist:
            raise serializers.ValidationError('Screen not found')
        return value
    
    def create(self, validated_data):
        """Create command with screen"""
        screen_id = validated_data.pop('screen_id')
        from signage.models import Screen
        screen = Screen.objects.get(id=screen_id)
        
        command = Command.objects.create(
            screen=screen,
            created_by=self.context['request'].user,
            **validated_data
        )
        return command


class CommandStatusSerializer(serializers.Serializer):
    """Serializer for command status response"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    type = serializers.CharField()
    type_display = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    executed_at = serializers.DateTimeField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)
    attempt_count = serializers.IntegerField()
    screen_id = serializers.UUIDField(allow_null=True)
    screen_name = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    created_by = serializers.UUIDField(allow_null=True)


class CommandExecutionSerializer(serializers.Serializer):
    """Serializer for command execution"""
    screen_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_screen_id(self, value):
        """Validate screen exists if provided"""
        if value:
            from signage.models import Screen
            try:
                screen = Screen.objects.get(id=value)
            except Screen.DoesNotExist:
                raise serializers.ValidationError('Screen not found')
        return value
