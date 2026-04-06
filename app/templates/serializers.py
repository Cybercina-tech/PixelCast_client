from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from .models import (
    Template,
    Layer,
    Widget,
    Content,
    Schedule,
    QRActionLink,
    QRActionRule,
    QRScanEvent,
)
from accounts.permissions import RolePermissions


def _extract_local_storage_path(file_url: str) -> str | None:
    """Convert a local media URL/path into a storage-relative path."""
    if not file_url:
        return None

    raw = str(file_url).strip()
    if not raw:
        return None

    # Remote URLs are not checked via local storage.
    if raw.startswith('http://') or raw.startswith('https://'):
        return None

    clean = raw.lstrip('/')
    media_prefix = str(getattr(settings, 'MEDIA_URL', '/media/')).strip('/')
    if media_prefix and clean.startswith(f'{media_prefix}/'):
        clean = clean[len(media_prefix) + 1:]

    return clean.strip('/') or None


def _local_file_exists(content_obj) -> bool:
    """
    Check whether a locally stored media file still exists.
    Returns True for remote/S3 content to avoid false negatives.
    """
    if getattr(settings, 'USE_S3_STORAGE', False):
        return True

    path = getattr(content_obj, 'storage_path', None) or _extract_local_storage_path(getattr(content_obj, 'file_url', None))
    if not path:
        return True

    try:
        return default_storage.exists(path)
    except Exception:
        return False


class ContentSerializer(serializers.ModelSerializer):
    """Serializer for Content model"""
    is_downloaded = serializers.BooleanField(read_only=True)
    needs_download = serializers.BooleanField(read_only=True)
    file_extension = serializers.CharField(read_only=True)
    is_media_file = serializers.BooleanField(read_only=True)
    estimated_size_mb = serializers.FloatField(read_only=True)
    absolute_file_url = serializers.SerializerMethodField()
    secure_url = serializers.SerializerMethodField()
    is_assigned = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'name', 'description', 'type', 'file_url', 'absolute_file_url', 'secure_url', 'content_json',
            'text_content', 'duration', 'autoplay', 'order', 'widget', 'is_active',
            'downloaded', 'download_status', 'last_download_attempt',
            'retry_count', 'is_downloaded', 'needs_download', 'file_extension',
            'is_media_file', 'estimated_size_mb', 'image_width', 'image_height', 'video_duration',
            'file_size', 'is_assigned', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'downloaded', 'download_status', 'last_download_attempt',
            'retry_count', 'created_at', 'updated_at', 'image_width', 'image_height', 'video_duration', 'file_size'
        ]
    
    def get_absolute_file_url(self, obj):
        """Return absolute URL for the file"""
        if not obj.file_url:
            return None
        if not _local_file_exists(obj):
            return None
        
        # If already absolute URL, return as is
        if obj.file_url.startswith('http://') or obj.file_url.startswith('https://'):
            return obj.file_url
        
        # Get request context for building absolute URL
        request = self.context.get('request')
        actual_request = None
        if request:
            # DRF Request object has _request attribute
            actual_request = getattr(request, '_request', request)
            if hasattr(actual_request, 'build_absolute_uri'):
                try:
                    # file_url is stored like /media/... — build_absolute_uri handles it
                    if obj.file_url.startswith('/'):
                        return actual_request.build_absolute_uri(obj.file_url)
                except Exception:
                    pass
        
        # Fallback: construct absolute URL from settings (no duplicate /media/)
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        media_prefix = media_url.rstrip('/').lstrip('/')  # "media"

        raw = obj.file_url.strip()
        if raw.startswith('/'):
            return f"{base_url.rstrip('/')}{raw}"

        clean_url = raw.lstrip('/')
        # Already "media/users/..." or full relative path under site root
        if clean_url.startswith(f'{media_prefix}/'):
            return f"{base_url.rstrip('/')}/{clean_url}"

        return f"{base_url.rstrip('/')}{media_url.rstrip('/')}/{clean_url}"
    
    def get_secure_url(self, obj):
        """Return secure URL for the content file"""
        if not _local_file_exists(obj):
            return None
        try:
            return obj.get_secure_url()
        except Exception:
            return obj.absolute_file_url or obj.file_url
    
    def get_is_assigned(self, obj):
        """Check if content is assigned to a widget"""
        return obj.widget is not None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not _local_file_exists(instance):
            # Avoid emitting stale URLs when DB points to missing local media files.
            data['file_url'] = None
            data['absolute_file_url'] = None
            data['secure_url'] = None
        return data


class WidgetSerializer(serializers.ModelSerializer):
    """Serializer for Widget model"""
    contents = ContentSerializer(many=True, read_only=True)
    active_contents_count = serializers.SerializerMethodField()
    total_contents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Widget
        fields = [
            'id', 'name', 'type', 'content_url', 'content_json',
            'font_size', 'color', 'alignment', 'autoplay',
            'x', 'y', 'width', 'height', 'z_index', 'layer',
            'is_active', 'contents', 'active_contents_count',
            'total_contents_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_contents_count(self, obj):
        """Get count of active contents"""
        return obj.get_active_contents().count()
    
    def get_total_contents_count(self, obj):
        """Get total count of contents"""
        return obj.get_contents_count()


class QRActionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRActionRule
        fields = [
            'id',
            'link',
            'name',
            'priority',
            'target_url',
            'start_hour',
            'end_hour',
            'days_of_week',
            'is_active',
            'condition_json',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        start_hour = attrs.get('start_hour', getattr(self.instance, 'start_hour', None))
        end_hour = attrs.get('end_hour', getattr(self.instance, 'end_hour', None))
        for value, name in ((start_hour, 'start_hour'), (end_hour, 'end_hour')):
            if value is not None and (value < 0 or value > 23):
                raise serializers.ValidationError({name: 'Hour must be between 0 and 23.'})
        days_of_week = attrs.get('days_of_week', getattr(self.instance, 'days_of_week', []))
        if days_of_week:
            try:
                normalized = sorted({int(item) for item in days_of_week})
            except (TypeError, ValueError):
                raise serializers.ValidationError({'days_of_week': 'Use weekday indexes 0..6.'})
            if any(item < 0 or item > 6 for item in normalized):
                raise serializers.ValidationError({'days_of_week': 'Use weekday indexes 0..6.'})
            attrs['days_of_week'] = normalized
        return attrs


class QRActionLinkSerializer(serializers.ModelSerializer):
    rules = QRActionRuleSerializer(many=True, read_only=True)
    redirect_url = serializers.SerializerMethodField()

    class Meta:
        model = QRActionLink
        fields = [
            'id',
            'widget',
            'slug',
            'default_url',
            'campaign_id',
            'is_active',
            'error_correction_level',
            'settings_json',
            'redirect_url',
            'rules',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_redirect_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f"/qr/{obj.slug}/")
        return f"/qr/{obj.slug}/"


class QRScanEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRScanEvent
        fields = [
            'id',
            'link',
            'matched_rule',
            'campaign_id',
            'resolved_url',
            'request_ip',
            'user_agent',
            'referrer',
            'query_params',
            'source_screen',
            'created_at',
        ]
        read_only_fields = fields


class LayerSerializer(serializers.ModelSerializer):
    """Serializer for Layer model"""
    widgets = WidgetSerializer(many=True, read_only=True)
    active_widgets_count = serializers.SerializerMethodField()
    total_widgets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Layer
        fields = [
            'id', 'name', 'description', 'x', 'y', 'width', 'height',
            'z_index', 'background_color', 'opacity', 'animation_type',
            'animation_duration', 'template', 'is_active', 'widgets',
            'active_widgets_count', 'total_widgets_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_widgets_count(self, obj):
        """Get count of active widgets"""
        return obj.get_active_widgets().count()
    
    def get_total_widgets_count(self, obj):
        """Get total count of widgets"""
        return obj.get_widgets().count()


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model"""
    layers = LayerSerializer(many=True, read_only=True)
    layers_count = serializers.SerializerMethodField()
    widgets_count = serializers.SerializerMethodField()
    contents_count = serializers.SerializerMethodField()
    screens_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'orientation', 'width', 'height',
            'thumbnail', 'created_by', 'is_active', 'is_sample', 'version', 'config_json',
            'meta_data', 'layers', 'layers_count', 'widgets_count',
            'contents_count', 'screens_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'orientation': {'required': False},  # Has default
            'width': {'required': False},  # Has default
            'height': {'required': False},  # Has default
            'is_active': {'required': False},  # Has default
        }
    
    def validate_name(self, value):
        """Validate template name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Template name is required and cannot be empty.")
        if len(value.strip()) > 255:
            raise serializers.ValidationError("Template name cannot exceed 255 characters.")
        return value.strip()
    
    def validate_width(self, value):
        """Validate template width"""
        if value is not None and value < 1:
            raise serializers.ValidationError("Width must be at least 1 pixel.")
        return value
    
    def validate_height(self, value):
        """Validate template height"""
        if value is not None and value < 1:
            raise serializers.ValidationError("Height must be at least 1 pixel.")
        return value
    
    def validate(self, attrs):
        """Validate template data"""
        # Ensure name is provided
        if not attrs.get('name'):
            raise serializers.ValidationError({
                'name': 'Template name is required.'
            })

        request = self.context.get('request')
        if request is not None and 'is_sample' in attrs:
            u = request.user
            if not (u.is_developer() or u.is_manager()):
                raise serializers.ValidationError({
                    'is_sample': 'Only Developer or Manager can mark templates as sample templates.'
                })
        
        return attrs
    
    def get_layers_count(self, obj):
        """Get count of layers"""
        return obj.get_layers().count()
    
    def get_widgets_count(self, obj):
        """Get count of widgets"""
        return obj.get_widgets().count()
    
    def get_contents_count(self, obj):
        """Get count of contents"""
        return obj.get_all_contents().count()
    
    def get_screens_count(self, obj):
        """Get count of screens"""
        return obj.screens.count()


class TemplateListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Template list view"""
    layers_count = serializers.SerializerMethodField()
    screens_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'orientation', 'width', 'height',
            'thumbnail', 'is_active', 'is_sample', 'version', 'layers_count',
            'screens_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_layers_count(self, obj):
        return obj.get_layers().count()
    
    def get_screens_count(self, obj):
        return obj.screens.count()


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for Schedule model"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_id = serializers.UUIDField(source='template.id', read_only=True)
    screens_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    is_running_now = serializers.SerializerMethodField()
    next_run = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'name', 'description', 'template', 'template_id', 'template_name',
            'start_time', 'end_time', 'is_active', 'repeat_type',
            'last_executed_at', 'is_currently_running', 'screens_count',
            'duration', 'is_past', 'is_running_now', 'next_run',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_executed_at', 'is_currently_running',
            'created_at', 'updated_at'
        ]
    
    def get_screens_count(self, obj):
        """Get count of screens assigned to this schedule"""
        return obj.screens_count
    
    def get_duration(self, obj):
        """Get duration of the schedule"""
        return obj.duration
    
    def get_is_past(self, obj):
        """Check if schedule is in the past"""
        return obj.is_past
    
    def get_is_running_now(self, obj):
        """Check if schedule is currently running"""
        return obj.is_running_now
    
    def get_screens_count(self, obj):
        """Get count of screens assigned to this schedule"""
        return obj.screens_count
    
    def get_duration(self, obj):
        """Get duration of the schedule"""
        return obj.duration
    
    def get_is_past(self, obj):
        """Check if schedule is in the past"""
        return obj.is_past
    
    def get_is_running_now(self, obj):
        """Check if schedule is currently running"""
        return obj.is_running_now
    
    def get_next_run(self, obj):
        """Get next run time"""
        next_run = obj.next_run()
        return next_run.isoformat() if next_run else None
    
    def validate(self, attrs):
        """Validate schedule data"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time.'
                })
        
        return attrs


class ScheduleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Schedule list view"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    screens_count = serializers.SerializerMethodField()
    is_running_now = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'name', 'description', 'template', 'template_name',
            'start_time', 'end_time', 'is_active', 'repeat_type',
            'is_currently_running', 'screens_count', 'is_running_now',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_screens_count(self, obj):
        """Get count of screens assigned to this schedule"""
        return obj.screens_count
    
    def get_is_running_now(self, obj):
        """Check if schedule is currently running"""
        return obj.is_running_now


class TemplateActivationSerializer(serializers.Serializer):
    """Serializer for template activation on screen"""
    screen_id = serializers.UUIDField(required=True)
    sync_content = serializers.BooleanField(default=True)
    
    def validate_screen_id(self, value):
        """Validate screen exists"""
        from signage.models import Screen
        try:
            screen = Screen.objects.get(id=value)
        except Screen.DoesNotExist:
            raise serializers.ValidationError('Screen not found')
        return value


class ScheduleExecutionSerializer(serializers.Serializer):
    """Serializer for schedule execution"""
    force = serializers.BooleanField(default=False, help_text='Force execution even if not due')
    
    def validate(self, attrs):
        """Validate schedule can be executed"""
        schedule = self.instance
        if not schedule:
            raise serializers.ValidationError('Schedule instance required')
        
        if not schedule.is_active:
            raise serializers.ValidationError('Schedule is not active')
        
        if not schedule.screens.exists():
            raise serializers.ValidationError('No screens assigned to this schedule')
        
        return attrs
