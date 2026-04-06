from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
import logging
from .models import Screen, PairingSession
from commands.models import Command
from templates.models import Template, Content, Layer, Widget
from log.models import CommandExecutionLog, ScreenStatusLog, ContentDownloadLog
from .weather_service import enrich_weather_style

logger = logging.getLogger(__name__)


def _extract_local_storage_path(file_url: str) -> str | None:
    if not file_url:
        return None

    raw = str(file_url).strip()
    if not raw:
        return None
    if raw.startswith('http://') or raw.startswith('https://'):
        return None

    clean = raw.lstrip('/')
    media_prefix = str(getattr(settings, 'MEDIA_URL', '/media/')).strip('/')
    if media_prefix and clean.startswith(f'{media_prefix}/'):
        clean = clean[len(media_prefix) + 1:]

    return clean.strip('/') or None


def _local_file_exists(content_obj) -> bool:
    if getattr(settings, 'USE_S3_STORAGE', False):
        return True

    path = getattr(content_obj, 'storage_path', None) or _extract_local_storage_path(getattr(content_obj, 'file_url', None))
    if not path:
        return True

    try:
        return default_storage.exists(path)
    except Exception:
        return False


class ScreenSerializer(serializers.ModelSerializer):
    """Serializer for Screen model"""
    is_heartbeat_stale = serializers.SerializerMethodField()
    online_duration_seconds = serializers.SerializerMethodField()
    active_template = serializers.SerializerMethodField()
    
    class Meta:
        model = Screen
        fields = [
            'id', 'name', 'device_id', 'location', 'description',
            'active_template', 'is_online', 'last_heartbeat_at',
            'last_ip', 'app_version', 'os_version', 'device_model',
            'screen_width', 'screen_height', 'brightness', 'orientation',
            'is_busy', 'is_heartbeat_stale', 'online_duration_seconds',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_online', 'last_heartbeat_at', 'last_ip',
            'is_busy', 'created_at', 'updated_at'
        ]
    
    def get_is_heartbeat_stale(self, obj):
        """Check if heartbeat is stale"""
        return obj.is_heartbeat_stale()
    
    def get_online_duration_seconds(self, obj):
        """Calculate online duration in seconds"""
        if not obj.is_online or not obj.last_heartbeat_at:
            return None
        delta = timezone.now() - obj.last_heartbeat_at
        return int(delta.total_seconds())
    
    def get_active_template(self, obj):
        """
        Return active template with id and name
        CRITICAL FIX: Return template object with name instead of just ID
        This ensures frontend can display template name instead of "None"
        """
        if obj.active_template:
            return {
                'id': obj.active_template.id,
                'name': obj.active_template.name
            }
        return None


class HeartbeatSerializer(serializers.Serializer):
    """Serializer for heartbeat POST requests"""
    auth_token = serializers.CharField(required=True, write_only=True)
    secret_key = serializers.CharField(required=True, write_only=True)
    latency = serializers.FloatField(required=False, allow_null=True)
    cpu_usage = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    memory_usage = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    app_version = serializers.CharField(required=False, allow_blank=True, max_length=50)
    os_version = serializers.CharField(required=False, allow_blank=True, max_length=100)
    device_model = serializers.CharField(required=False, allow_blank=True, max_length=255)
    screen_width = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    screen_height = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    brightness = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    orientation = serializers.ChoiceField(required=False, choices=Screen.ORIENTATION_CHOICES)
    
    def validate(self, attrs):
        """Validate authentication credentials"""
        import logging
        logger = logging.getLogger(__name__)
        
        auth_token = attrs.get('auth_token')
        secret_key = attrs.get('secret_key')
        
        # Log validation attempt (masked)
        logger.debug(f"HeartbeatSerializer validation: auth_token={auth_token[:8] + '...' if auth_token else 'MISSING'}, secret_key={'***' if secret_key else 'MISSING'}")
        
        # Check if credentials are provided
        if not auth_token or not auth_token.strip():
            logger.warning("HeartbeatSerializer: auth_token is missing or empty")
            raise serializers.ValidationError({'auth_token': 'Authentication token is required'})
        
        if not secret_key or not secret_key.strip():
            logger.warning("HeartbeatSerializer: secret_key is missing or empty")
            raise serializers.ValidationError({'secret_key': 'Secret key is required'})
        
        try:
            screen = Screen.objects.get(auth_token=auth_token)
            logger.debug(f"HeartbeatSerializer: Screen found with auth_token. Screen ID: {screen.id}, Name: {screen.name}")
        except Screen.DoesNotExist:
            logger.warning(f"HeartbeatSerializer: No screen found with auth_token: {auth_token[:8]}...")
            raise serializers.ValidationError({'auth_token': 'Invalid authentication token'})
        except Exception as e:
            logger.error(f"HeartbeatSerializer: Error fetching screen: {str(e)}", exc_info=True)
            raise serializers.ValidationError({'auth_token': 'Error validating authentication token'})
        
        # Authenticate
        if not screen.authenticate(auth_token, secret_key):
            logger.warning(f"HeartbeatSerializer: Authentication failed for screen {screen.id}. Token matches but secret_key is incorrect.")
            raise serializers.ValidationError({'secret_key': 'Invalid secret key'})
        
        logger.info(f"HeartbeatSerializer: Authentication successful for screen {screen.id} ({screen.name})")
        attrs['screen'] = screen
        return attrs


class CommandSerializer(serializers.ModelSerializer):
    """Serializer for Command model"""
    payload_summary = serializers.CharField(read_only=True)
    is_executable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Command
        fields = [
            'id', 'name', 'type', 'payload', 'priority', 'status',
            'expire_at', 'attempt_count', 'last_attempt_at',
            'payload_summary', 'is_executable', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'attempt_count', 'last_attempt_at', 'created_at'
        ]


class CommandPullSerializer(serializers.Serializer):
    """Serializer for command pull GET requests"""
    auth_token = serializers.CharField(required=True)
    secret_key = serializers.CharField(required=True)
    limit = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    
    def validate(self, attrs):
        """Validate authentication credentials"""
        auth_token = attrs.get('auth_token')
        secret_key = attrs.get('secret_key')
        
        try:
            screen = Screen.objects.get(auth_token=auth_token)
        except Screen.DoesNotExist:
            raise serializers.ValidationError({'auth_token': 'Invalid authentication token'})
        
        if not screen.authenticate(auth_token, secret_key):
            raise serializers.ValidationError({'secret_key': 'Invalid secret key'})
        
        attrs['screen'] = screen
        return attrs


class CommandResponseSerializer(serializers.Serializer):
    """Serializer for command execution response POST requests"""
    auth_token = serializers.CharField(required=True)
    secret_key = serializers.CharField(required=True)
    command_id = serializers.UUIDField(required=True)
    status = serializers.ChoiceField(required=True, choices=['done', 'failed'])
    response_payload = serializers.JSONField(required=False, default=dict)
    error_message = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate authentication and command"""
        auth_token = attrs.get('auth_token')
        secret_key = attrs.get('secret_key')
        command_id = attrs.get('command_id')
        
        try:
            screen = Screen.objects.get(auth_token=auth_token)
        except Screen.DoesNotExist:
            raise serializers.ValidationError({'auth_token': 'Invalid authentication token'})
        
        if not screen.authenticate(auth_token, secret_key):
            raise serializers.ValidationError({'secret_key': 'Invalid secret key'})
        
        try:
            command = Command.objects.get(id=command_id, screen=screen)
        except Command.DoesNotExist:
            raise serializers.ValidationError({'command_id': 'Command not found or does not belong to this screen'})
        
        attrs['screen'] = screen
        attrs['command'] = command
        return attrs


class ContentSyncSerializer(serializers.Serializer):
    """Serializer for content sync POST requests"""
    auth_token = serializers.CharField(required=True)
    secret_key = serializers.CharField(required=True)
    sync_type = serializers.ChoiceField(required=True, choices=['request', 'status'])
    content_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    download_status = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )
    
    def validate(self, attrs):
        """Validate authentication"""
        auth_token = attrs.get('auth_token')
        secret_key = attrs.get('secret_key')
        
        try:
            screen = Screen.objects.get(auth_token=auth_token)
        except Screen.DoesNotExist:
            raise serializers.ValidationError({'auth_token': 'Invalid authentication token'})
        
        if not screen.authenticate(auth_token, secret_key):
            raise serializers.ValidationError({'secret_key': 'Invalid secret key'})
        
        attrs['screen'] = screen
        return attrs
    
    def validate_download_status(self, value):
        """Validate download status format"""
        if value:
            for item in value:
                if 'content_id' not in item:
                    raise serializers.ValidationError('Each download_status item must have content_id')
                if 'status' not in item:
                    raise serializers.ValidationError('Each download_status item must have status')
                if item['status'] not in ['success', 'failed', 'pending']:
                    raise serializers.ValidationError('Status must be one of: success, failed, pending')
        return value


class TemplateContentSerializer(serializers.ModelSerializer):
    """Serializer for Template content information"""
    class Meta:
        model = Content
        fields = [
            'id', 'name', 'type', 'file_url', 'content_json',
            'duration', 'order', 'is_active', 'download_status'
        ]


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model (simplified for API)"""
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'orientation',
            'width', 'height', 'version', 'is_active'
        ]


# Player-specific serializers for complete template structure
class PlayerContentSerializer(serializers.ModelSerializer):
    """Serializer for Content in player context"""
    secure_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'name', 'type', 'secure_url', 'content_json', 'text_content',
            'duration', 'autoplay', 'order', 'file_size', 'file_hash', 'is_active'
        ]

    def to_representation(self, instance):
        """
        Ensure text payload is always available for player clients.
        Some widgets rely on content_json.text while others read text_content directly.
        """
        data = super().to_representation(instance)

        if instance.type in {'text', 'marquee'}:
            text_value = (instance.text_content or '').strip()
            if text_value:
                if not isinstance(data.get('content_json'), dict):
                    data['content_json'] = {}
                data['content_json']['text'] = text_value
                data['text_content'] = text_value

        return data
    
    def get_secure_url(self, obj):
        """Get secure URL with appropriate expiration and make it absolute"""
        if not obj.file_url:
            return ''
        if not _local_file_exists(obj):
            return ''
        
        # Get the original file_url
        url = obj.file_url
        
        # If already absolute URL, return as is
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Get request context for building absolute URL
        request = self.context.get('request')
        
        # Try to get the actual request object (might be wrapped)
        actual_request = None
        if request:
            # DRF Request object has _request attribute
            actual_request = getattr(request, '_request', request)
            if hasattr(actual_request, 'build_absolute_uri'):
                try:
                    # Use build_absolute_uri to ensure we get http://localhost:8000
                    absolute_url = actual_request.build_absolute_uri(url)
                    # Log for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Built absolute URL for content {obj.id}: {absolute_url} (from {url})")
                    return absolute_url
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to build absolute URI from request: {e}, falling back to BASE_URL")
            elif hasattr(request, 'build_absolute_uri'):
                # Try DRF request directly
                try:
                    absolute_url = request.build_absolute_uri(url)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Built absolute URL for content {obj.id}: {absolute_url} (from {url})")
                    return absolute_url
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to build absolute URI from DRF request: {e}")
        
        # Fallback: construct absolute URL from settings
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        # Clean up the URL
        clean_url = url.lstrip('/')
        
        # If URL already starts with MEDIA_URL, use it as is
        if url.startswith(media_url):
            clean_url = url[len(media_url):].lstrip('/')
        
        # Construct full absolute URL
        absolute_url = f"{base_url.rstrip('/')}{media_url.rstrip('/')}/{clean_url}"
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Constructed absolute URL for content {obj.id}: {absolute_url} (from file_url: {url})")
        
        return absolute_url


class PlayerWidgetSerializer(serializers.ModelSerializer):
    """Serializer for Widget in player context"""
    contents = serializers.SerializerMethodField()
    
    class Meta:
        model = Widget
        fields = [
            'id', 'name', 'type',
            'content_url', 'content_json',
            'font_size', 'color', 'alignment', 'autoplay',
            'x', 'y', 'width', 'height', 'z_index',
            'is_active', 'contents'
        ]
    
    def get_contents(self, obj):
        """Get active contents with request context for absolute URLs"""
        active_contents = obj.get_active_contents()
        return PlayerContentSerializer(active_contents, many=True, context=self.context).data
    
class PlayerLayerSerializer(serializers.ModelSerializer):
    """Serializer for Layer in player context"""
    widgets = serializers.SerializerMethodField()
    
    class Meta:
        model = Layer
        fields = [
            'id', 'name', 'x', 'y', 'width', 'height', 'z_index',
            'background_color', 'opacity', 'animation_type',
            'animation_duration', 'is_active', 'widgets'
        ]
    
    def get_widgets(self, obj):
        """Get active widgets with request context for absolute URLs"""
        active_widgets = obj.get_active_widgets()
        return PlayerWidgetSerializer(active_widgets, many=True, context=self.context).data

class PlayerTemplateSerializer(serializers.ModelSerializer):
    """Serializer for complete template structure for player"""
    layers = serializers.SerializerMethodField()
    config_json = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'orientation', 'width', 'height',
            'version', 'config_json', 'layers'
        ]
    
    def get_layers(self, obj):
        """
        Get only active layers, ordered by z_index.
        CRITICAL: This fetches layers from the database (not config_json).
        Widgets are loaded via PlayerLayerSerializer -> PlayerWidgetSerializer.
        """
        # Use prefetch_related to efficiently load widgets and contents
        active_layers = obj.layers.filter(is_active=True).prefetch_related(
            'widgets__contents'
        ).order_by('z_index', 'name')
        return PlayerLayerSerializer(active_layers, many=True, context=self.context).data
    
    def get_config_json(self, obj):
        """
        Get config_json with all URLs converted to absolute URLs.
        This ensures screens can properly load images and media files.
        """
        if not obj.config_json:
            return obj.config_json
        
        import copy
        config = copy.deepcopy(obj.config_json)
        
        # Get request context for building absolute URLs
        request = self.context.get('request')
        screen = self.context.get('screen')
        
        # Helper function to convert relative URL to absolute
        def make_absolute_url(url):
            """Convert relative URL to absolute URL"""
            if not url or not isinstance(url, str):
                return url
            
            # If already absolute URL, return as is
            if url.startswith('http://') or url.startswith('https://'):
                return url
            
            # Try to build absolute URL from request
            if request:
                actual_request = getattr(request, '_request', request)
                if hasattr(actual_request, 'build_absolute_uri'):
                    try:
                        absolute_url = actual_request.build_absolute_uri(url)
                        logger.debug(f"Built absolute URL in config_json: {absolute_url} (from {url})")
                        return absolute_url
                    except Exception as e:
                        logger.warning(f"Failed to build absolute URI from request: {e}, falling back to BASE_URL")
            
            # Fallback: construct absolute URL from settings
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            
            # Clean up the URL
            clean_url = url.lstrip('/')
            
            # If URL already starts with MEDIA_URL, use it as is
            if url.startswith(media_url):
                clean_url = url[len(media_url):].lstrip('/')
            
            # Construct full absolute URL
            absolute_url = f"{base_url.rstrip('/')}{media_url.rstrip('/')}/{clean_url}"
            logger.debug(f"Constructed absolute URL in config_json: {absolute_url} (from {url})")
            return absolute_url
        
        # Recursively process config_json to find and convert URLs
        def process_widget(widget):
            """Process a widget and convert all URLs to absolute"""
            if not isinstance(widget, dict):
                return widget
            
            # Process content field (common for image/video widgets)
            if 'content' in widget and widget['content']:
                widget['content'] = make_absolute_url(widget['content'])
            
            # Process style object for background images
            if 'style' in widget and isinstance(widget['style'], dict):
                if 'backgroundImage' in widget['style']:
                    widget['style']['backgroundImage'] = make_absolute_url(widget['style']['backgroundImage'])
                if 'background-image' in widget['style']:
                    widget['style']['background-image'] = make_absolute_url(widget['style']['background-image'])
                if widget.get('type') == 'weather':
                    widget['style'] = enrich_weather_style(widget['style'])
            
            # Process any other URL-like fields
            url_fields = ['image_url', 'file_url', 'file_path', 'src', 'url', 'media_url']
            for field in url_fields:
                if field in widget and widget[field]:
                    widget[field] = make_absolute_url(widget[field])
            
            return widget
        
        # Process widgets array if present
        if 'widgets' in config and isinstance(config['widgets'], list):
            config['widgets'] = [process_widget(widget) for widget in config['widgets']]
        
        # Process backgroundImage in config_json root
        if 'backgroundImage' in config:
            config['backgroundImage'] = make_absolute_url(config['backgroundImage'])
        
        return config


# Pairing serializers
class PairingSessionSerializer(serializers.ModelSerializer):
    """Serializer for pairing session (TV side - public)"""
    is_expired = serializers.SerializerMethodField()
    expires_in_seconds = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PairingSession
        fields = [
            'pairing_code', 'pairing_token', 'status',
            'expires_at', 'is_expired', 'expires_in_seconds',
            'qr_code_url', 'created_at'
        ]
        read_only_fields = ['pairing_code', 'pairing_token', 'status', 'expires_at', 'created_at']
    
    def get_is_expired(self, obj):
        """Check if pairing session is expired"""
        return obj.is_expired()
    
    def get_expires_in_seconds(self, obj):
        """Calculate seconds until expiration"""
        if obj.is_expired():
            return 0
        delta = obj.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))
    
    def get_qr_code_url(self, obj):
        """Generate QR code URL for pairing"""
        from django.conf import settings
        # Try to get from settings, fallback to localhost
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        # Remove trailing slash if present
        base_url = base_url.rstrip('/')
        return f"{base_url}/screens/add?token={obj.pairing_token}"


class PairingBindSerializer(serializers.Serializer):
    """Serializer for binding a pairing session to a user (Dashboard side)"""
    pairing_code = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=6,
        help_text="6-digit pairing code (alternative to pairing_token)"
    )
    pairing_token = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=255,
        help_text="Pairing token from QR code (alternative to pairing_code)"
    )
    screen_name = serializers.CharField(
        required=False,
        max_length=255,
        allow_blank=True,
        allow_null=True,
        help_text="Optional name for the screen"
    )
    
    def validate(self, attrs):
        """Validate that either pairing_code or pairing_token is provided"""
        pairing_code = attrs.get('pairing_code')
        pairing_token = attrs.get('pairing_token')
        
        # Clean up empty strings
        if pairing_code == '':
            pairing_code = None
        if pairing_token == '':
            pairing_token = None
        
        if not pairing_code and not pairing_token:
            raise serializers.ValidationError({
                'non_field_errors': ['Either pairing_code or pairing_token must be provided']
            })
        
        # Find pairing session
        try:
            if pairing_code:
                session = PairingSession.objects.get(
                    pairing_code=pairing_code,
                    status='pending'
                )
            else:
                session = PairingSession.objects.get(
                    pairing_token=pairing_token,
                    status='pending'
                )
        except PairingSession.DoesNotExist:
            raise serializers.ValidationError({
                'non_field_errors': ['Invalid or expired pairing code/token']
            })
        
        # Check if expired
        if session.is_expired():
            session.mark_expired()
            raise serializers.ValidationError({
                'non_field_errors': ['Pairing code/token has expired. Please generate a new one.']
            })
        
        # Check if already paired
        if session.status != 'pending':
            raise serializers.ValidationError({
                'non_field_errors': ['This pairing code/token has already been used']
            })
        
        attrs['session'] = session
        return attrs


class PairingStatusSerializer(serializers.Serializer):
    """Serializer for checking pairing status (TV side polling)"""
    pairing_token = serializers.CharField(required=True)
    
    def validate_pairing_token(self, value):
        """Validate pairing token and return session"""
        try:
            session = PairingSession.objects.get(pairing_token=value)
        except PairingSession.DoesNotExist:
            raise serializers.ValidationError("Invalid pairing token")
        
        # Check if expired
        if session.is_expired() and session.status == 'pending':
            session.mark_expired()
        
        return session
