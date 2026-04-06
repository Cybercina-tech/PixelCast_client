import uuid
import os
import requests
import json
from django.db import models
from django.db import transaction
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta


def default_json_dict():
    """Return an empty dict for JSONField default values."""
    return {}


def template_thumbnail_upload_path(instance, filename):
    """
    Generate upload path for template thumbnails.
    Organizes files by template ID for better file management.
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join('templates', 'thumbnails', filename)


class Template(models.Model):
    """
    Digital Signage Template model for managing display templates.
    
    Templates define the layout, content, and configuration for digital signage screens.
    Each template can contain multiple layers and widgets, and can be assigned to screens.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the template"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the template"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the template"
    )
    ORIENTATION_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait'),
    ]
    orientation = models.CharField(
        max_length=20,
        choices=ORIENTATION_CHOICES,
        default='landscape',
        help_text="Template orientation"
    )
    width = models.PositiveIntegerField(
        default=1920,
        validators=[MinValueValidator(1)],
        help_text="Template width in pixels"
    )
    height = models.PositiveIntegerField(
        default=1080,
        validators=[MinValueValidator(1)],
        help_text="Template height in pixels"
    )
    thumbnail = models.ImageField(
        upload_to=template_thumbnail_upload_path,
        blank=True,
        null=True,
        help_text="Preview thumbnail image for the template"
    )
    
    # Relations
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates',
        help_text="User who created this template"
    )
    screens = models.ManyToManyField(
        'signage.Screen',
        blank=True,
        related_name='templates',
        help_text="Screens that have this template assigned"
    )
    assigned_schedules = models.ManyToManyField(
        'signage.Schedule',
        blank=True,
        related_name='templates',
        help_text="Schedules assigned to this template"
    )
    
    # Status & Control
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the template is currently active and available for use"
    )
    is_sample = models.BooleanField(
        default=False,
        db_index=True,
        help_text="If true, visible to all Visitor users for exploration (read-only in app)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this template was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this template was last updated"
    )
    version = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Template version number"
    )
    
    # Dynamic Configuration
    config_json = models.JSONField(
        default=default_json_dict,
        help_text="Template configuration in JSON format (required)"
    )
    meta_data = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Additional metadata in JSON format (optional)"
    )
    
    class Meta:
        db_table = 'templates_template'
        verbose_name = 'Template'
        verbose_name_plural = 'Templates'
        ordering = ['-created_at', 'name']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['created_by', 'is_active']),
            models.Index(fields=['orientation', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_layers(self):
        """
        Get all Layer objects associated with this template.
        
        Returns:
            QuerySet: All Layer objects related to this template
        """
        # This will work once the Layer model is created with a ForeignKey to Template
        try:
            return self.layers.all()
        except AttributeError:
            # Layer model doesn't exist yet, return empty queryset
            # Import here to avoid circular import (Layer is defined later in this file)
            from templates.models import Layer
            return Layer.objects.none()
    
    def get_widgets(self):
        """
        Get all Widget objects across all layers of this template.
        
        Returns:
            QuerySet: All Widget objects from all layers in this template
        """
        layers = self.get_layers()
        if not layers.exists():
            # Return empty queryset using Widget model
            # Import here to avoid circular import (Widget is defined later in this file)
            from templates.models import Widget
            return Widget.objects.none()
        
        # Get all widgets from all layers using layer IDs
        layer_ids = layers.values_list('id', flat=True)
        from templates.models import Widget
        return Widget.objects.filter(layer_id__in=layer_ids)
    
    def get_all_contents(self):
        """
        Get all Content objects across all widgets in all layers of this template.
        
        Returns:
            QuerySet: All Content objects from all widgets in all layers
        """
        widgets = self.get_widgets()
        if not widgets.exists():
            # Return empty queryset using Content model
            # Import here to avoid circular import (Content is defined later in this file)
            from templates.models import Content
            return Content.objects.none()
        
        # Get all contents from all widgets using widget IDs
        widget_ids = widgets.values_list('id', flat=True)
        from templates.models import Content
        return Content.objects.filter(widget_id__in=widget_ids)
    
    def activate_on_screen(self, screen, sync_content=True):
        """
        Activate this template on a screen.
        This is a convenience method that calls screen.activate_template().
        
        Args:
            screen: Screen instance
            sync_content: Whether to sync content after activation (default: True)
            
        Returns:
            bool: True if activation successful, False otherwise
        """
        return screen.activate_template(self, sync_content=sync_content)


class Layer(models.Model):
    """
    Digital Signage Layer model for managing template layers.
    
    Layers are positioned containers within a template that can hold widgets.
    Each layer has position, size, appearance properties, and can contain animations.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the layer"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the layer"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the layer"
    )
    
    # Position & Size
    x = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="X position (left) in pixels from template origin"
    )
    y = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Y position (top) in pixels from template origin"
    )
    width = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Layer width in pixels"
    )
    height = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Layer height in pixels"
    )
    z_index = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Z-index for display order (higher values appear on top)"
    )
    
    # Appearance & Animation
    background_color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Background color (hex code like #FFFFFF or color name)"
    )
    opacity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Layer opacity (0.0 = transparent, 1.0 = opaque)"
    )
    ANIMATION_TYPE_CHOICES = [
        ('none', 'None'),
        ('fade', 'Fade'),
        ('slide', 'Slide'),
    ]
    animation_type = models.CharField(
        max_length=20,
        choices=ANIMATION_TYPE_CHOICES,
        default='none',
        help_text="Type of animation to apply to the layer"
    )
    animation_duration = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Animation duration in seconds"
    )
    
    # Relations
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='layers',
        help_text="Template that this layer belongs to"
    )
    
    # Status & Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the layer is currently active and visible"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this layer was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this layer was last updated"
    )
    
    class Meta:
        db_table = 'templates_layer'
        verbose_name = 'Layer'
        verbose_name_plural = 'Layers'
        ordering = ['template', 'z_index', 'name']
        indexes = [
            models.Index(fields=['template', 'z_index']),
            models.Index(fields=['template', 'is_active']),
            models.Index(fields=['is_active', 'z_index']),
        ]
    
    def __str__(self):
        """Return string representation: '{template name} - {layer name}'"""
        return f"{self.template.name} - {self.name}"
    
    def get_widgets(self):
        """
        Get all Widget objects associated with this layer.
        
        Returns:
            QuerySet: All Widget objects related to this layer
        """
        return self.widgets.all()
    
    def get_active_widgets(self):
        """Get only active widgets for this layer, ordered by z_index"""
        return self.widgets.filter(is_active=True).order_by('z_index', 'name')


class Widget(models.Model):
    """
    Digital Signage Widget model for managing content widgets within layers.
    
    Widgets are content elements (text, images, videos, etc.) that are positioned
    within layers. Each widget has its own position, size, and content configuration.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the widget"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the widget"
    )
    
    # Content Type & Configuration
    WIDGET_TYPE_CHOICES = [
        ('text', 'Text'),
        ('marquee', 'Marquee'),
        ('weather', 'Weather'),
        ('qr_action', 'QR Action'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('album', 'Album Playlist'),
        ('clock', 'Clock'),
        ('date', 'Date'),
        ('weekday', 'Weekday'),
        ('countdown', 'Countdown'),
        ('webview', 'Web View'),
        ('chart', 'Chart'),
    ]
    type = models.CharField(
        max_length=20,
        choices=WIDGET_TYPE_CHOICES,
        help_text="Type of widget content"
    )
    content_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL or file path for image/video/webview content"
    )
    content_json = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Dynamic or structured data for widget content"
    )
    font_size = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Font size in pixels (used for text widgets)"
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Color (hex code or color name) for text or background"
    )
    ALIGNMENT_CHOICES = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ]
    alignment = models.CharField(
        max_length=10,
        choices=ALIGNMENT_CHOICES,
        blank=True,
        null=True,
        help_text="Text alignment (used for text widgets)"
    )
    autoplay = models.BooleanField(
        default=False,
        help_text="Whether to autoplay video or animated widgets"
    )
    
    # Position & Size
    x = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="X position (left) in pixels from layer origin"
    )
    y = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Y position (top) in pixels from layer origin"
    )
    width = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Widget width in pixels"
    )
    height = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Widget height in pixels"
    )
    z_index = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Z-index for display order within layer (higher values appear on top)"
    )
    
    # Relations
    layer = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name='widgets',
        help_text="Layer that this widget belongs to"
    )
    
    # Status & Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the widget is currently active and visible"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this widget was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this widget was last updated"
    )
    
    class Meta:
        db_table = 'templates_widget'
        verbose_name = 'Widget'
        verbose_name_plural = 'Widgets'
        ordering = ['layer', 'z_index', 'name']
        indexes = [
            models.Index(fields=['layer', 'z_index']),
            models.Index(fields=['layer', 'is_active']),
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['is_active', 'z_index']),
        ]
    
    def __str__(self):
        """Return string representation: '{layer name} - {widget name}'"""
        return f"{self.layer.name} - {self.name}"
    
    def get_active_contents(self):
        """Get only active contents for this widget, ordered by order field"""
        return self.contents.filter(is_active=True).order_by('order')
    
    def get_contents_count(self):
        """Get total count of contents for this widget"""
        return self.contents.count()


class QRActionLink(models.Model):
    """Stable short-link record for QR Action widgets."""

    ERROR_CORRECTION_CHOICES = [
        ('L', 'Low'),
        ('M', 'Medium'),
        ('Q', 'Quartile'),
        ('H', 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    widget = models.OneToOneField(
        Widget,
        on_delete=models.CASCADE,
        related_name='qr_action_link',
    )
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    default_url = models.URLField(max_length=1000)
    campaign_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True)
    error_correction_level = models.CharField(
        max_length=1,
        choices=ERROR_CORRECTION_CHOICES,
        default='H',
    )
    settings_json = models.JSONField(default=default_json_dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates_qr_action_link'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['campaign_id', 'created_at']),
        ]

    def __str__(self):
        return f"{self.slug} ({self.widget_id})"

    def resolve_destination(self, now=None):
        check_time = now or timezone.localtime()
        for rule in self.rules.filter(is_active=True).order_by('priority', 'created_at'):
            if rule.matches(check_time):
                return rule.target_url, rule
        return self.default_url, None


class QRActionRule(models.Model):
    """Time-window based destination rule for a QR Action link."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.ForeignKey(
        QRActionLink,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    name = models.CharField(max_length=120, blank=True, null=True)
    priority = models.PositiveIntegerField(default=100)
    target_url = models.URLField(max_length=1000)
    start_hour = models.PositiveSmallIntegerField(blank=True, null=True)
    end_hour = models.PositiveSmallIntegerField(blank=True, null=True)
    days_of_week = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    condition_json = models.JSONField(default=default_json_dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates_qr_action_rule'
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['link', 'is_active', 'priority']),
        ]

    def __str__(self):
        return f"{self.link.slug} rule #{self.priority}"

    def matches(self, at_time):
        hour = at_time.hour
        weekday = at_time.weekday()

        if self.days_of_week:
            try:
                allowed_days = {int(day) for day in self.days_of_week}
            except (TypeError, ValueError):
                return False
            if weekday not in allowed_days:
                return False

        if self.start_hour is None and self.end_hour is None:
            return True
        if self.start_hour is None:
            return hour < self.end_hour
        if self.end_hour is None:
            return hour >= self.start_hour
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        return hour >= self.start_hour or hour < self.end_hour


class QRScanEvent(models.Model):
    """Immutable scan event log for reporting and attribution."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.ForeignKey(
        QRActionLink,
        on_delete=models.CASCADE,
        related_name='scan_events',
    )
    matched_rule = models.ForeignKey(
        QRActionRule,
        on_delete=models.SET_NULL,
        related_name='scan_events',
        blank=True,
        null=True,
    )
    campaign_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    resolved_url = models.URLField(max_length=1000)
    request_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.TextField(blank=True, null=True)
    query_params = models.JSONField(default=default_json_dict, blank=True)
    source_screen = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'templates_qr_scan_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['link', 'created_at']),
            models.Index(fields=['campaign_id', 'created_at']),
            models.Index(fields=['created_at']),
        ]


class Content(models.Model):
    """
    Digital Signage Content model for managing media and content items within widgets.
    
    Content represents individual media items (images, videos, text, etc.) that can be
    displayed within a widget. Supports multiple content items per widget for slideshows
    or playlists. Tracks download status for caching on screens.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the content"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the content"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the content"
    )
    
    # Content Type & File/Data
    CONTENT_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('text', 'Text'),
        ('webview', 'Web View'),
        ('chart', 'Chart'),
        ('json', 'JSON Data'),
    ]
    type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        help_text="Type of content"
    )
    file_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text="URL or file path for local or remote files (image/video/webview)"
    )
    content_json = models.JSONField(
        default=default_json_dict,
        blank=True,
        help_text="Dynamic or structured data for content"
    )
    text_content = models.TextField(
        blank=True,
        null=True,
        help_text="Manual text content for text type (alternative to file upload)"
    )
    duration = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0)],
        help_text="Display duration in seconds (for slideshows or videos)"
    )
    autoplay = models.BooleanField(
        default=False,
        help_text="Whether to autoplay video or animated content"
    )
    order = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Order of content in a widget (for playlists or slideshows)"
    )
    
    # Relations
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name='contents',
        null=True,
        blank=True,
        help_text="Widget that this content belongs to (optional - allows standalone media library)"
    )
    
    # Status & Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the content is currently active and visible"
    )
    downloaded = models.BooleanField(
        default=False,
        help_text="Whether content is cached locally on Screen"
    )
    DOWNLOAD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    download_status = models.CharField(
        max_length=20,
        choices=DOWNLOAD_STATUS_CHOICES,
        default='pending',
        help_text="Status of content download to screen"
    )
    last_download_attempt = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time download was attempted"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of download retry attempts"
    )
    
    # Storage & Security Fields
    storage_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Internal storage path for the file (S3 key or local path)"
    )
    file_size = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        help_text="File size in bytes"
    )
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA-256 hash of file content for integrity verification"
    )
    hash_algorithm = models.CharField(
        max_length=20,
        default='sha256',
        help_text="Hash algorithm used for file_hash"
    )
    
    # Media Metadata
    image_width = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Image width in pixels (for image content)"
    )
    image_height = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Image height in pixels (for image content)"
    )
    video_duration = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0)],
        help_text="Video duration in seconds (for video content)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this content was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this content was last updated"
    )
    
    class Meta:
        db_table = 'templates_content'
        verbose_name = 'Content'
        verbose_name_plural = 'Contents'
        ordering = ['widget', 'order', 'name']
        indexes = [
            models.Index(fields=['widget', 'order']),
            models.Index(fields=['widget', 'is_active']),
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['download_status', 'downloaded']),
            models.Index(fields=['widget', 'download_status']),
        ]
    
    def __str__(self):
        """Return string representation: '{widget name} - {content name}'"""
        return f"{self.widget.name} - {self.name}"
    
    # Helper Methods for Download Status
    def mark_downloaded(self):
        """
        Mark content as successfully downloaded.
        Updates downloaded flag and download_status.
        """
        self.downloaded = True
        self.download_status = 'success'
        self.last_download_attempt = timezone.now()
        self.save(update_fields=['downloaded', 'download_status', 'last_download_attempt'])
    
    def mark_failed(self, error_message=None):
        """
        Mark content download as failed.
        Updates download_status, increments retry_count, and updates last_download_attempt.
        Emits notification if retry limit exceeded.
        """
        self.downloaded = False
        self.download_status = 'failed'
        self.retry_count += 1
        self.last_download_attempt = timezone.now()
        self.save(update_fields=['downloaded', 'download_status', 'retry_count', 'last_download_attempt'])
        
        # Emit notification if retry limit exceeded
        if self.retry_count >= 3:  # Max retries
            try:
                from notifications.signals import emit_content_sync_failed
                # Get screen from widget -> layer -> template -> screens
                if hasattr(self.widget, 'layer') and hasattr(self.widget.layer, 'template'):
                    template = self.widget.layer.template
                    # Try to get a screen (simplified - in production, track which screen failed)
                    screens = template.screens.all()[:1]
                    if screens:
                        emit_content_sync_failed(self, screens[0], error_message or "Max retries exceeded")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error emitting content sync failed notification: {str(e)}")
    
    def update_status(self, status, downloaded=None):
        """
        Update download status and optionally downloaded flag.
        
        Args:
            status: One of 'pending', 'success', 'failed'
            downloaded: Optional boolean to set downloaded flag
        """
        if status not in dict(self.DOWNLOAD_STATUS_CHOICES).keys():
            raise ValueError(f"Invalid status: {status}. Must be one of {list(dict(self.DOWNLOAD_STATUS_CHOICES).keys())}")
        
        self.download_status = status
        if downloaded is not None:
            self.downloaded = downloaded
        self.last_download_attempt = timezone.now()
        self.save(update_fields=['download_status', 'downloaded', 'last_download_attempt'])
    
    def reset_download_status(self):
        """
        Reset download status to pending.
        Useful when content is updated and needs to be re-downloaded.
        """
        self.downloaded = False
        self.download_status = 'pending'
        self.last_download_attempt = None
        self.save(update_fields=['downloaded', 'download_status', 'last_download_attempt'])
    
    # Property Methods
    @property
    def is_downloaded(self):
        """Check if content is successfully downloaded"""
        return self.downloaded and self.download_status == 'success'
    
    @property
    def needs_download(self):
        """Check if content needs to be downloaded"""
        return not self.downloaded or self.download_status in ['pending', 'failed']
    
    @property
    def file_extension(self):
        """Extract file extension from file_url if available"""
        if self.file_url:
            try:
                return os.path.splitext(self.file_url.split('?')[0])[1].lower()
            except (AttributeError, IndexError):
                return None
        return None
    
    @property
    def is_media_file(self):
        """Check if content is a media file (image or video)"""
        return self.type in ['image', 'video']
    
    @property
    def estimated_size_mb(self):
        """
        Estimate file size in MB based on type and duration.
        This is a rough estimate and can be overridden with actual file size.
        """
        if not self.is_media_file or not self.duration:
            return None
        
        # Rough estimates: 1MB per second for video, 0.1MB per image
        if self.type == 'video':
            return round(self.duration * 1.0, 2)
        elif self.type == 'image':
            return 0.1
        return None
    
    # Operational Methods for Content Delivery
    def _extract_media_metadata(self, file_obj):
        """
        Extract metadata from media files (image dimensions, video duration).
        
        Args:
            file_obj: File object to extract metadata from
        """
        try:
            if self.type == 'image':
                # Extract image dimensions
                from PIL import Image
                import io
                
                # Reset file pointer
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                
                # Read image
                image = Image.open(io.BytesIO(file_obj.read()))
                self.image_width = image.width
                self.image_height = image.height
                
                # Reset file pointer again
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                    
            elif self.type == 'video':
                # Extract video duration
                try:
                    import cv2
                    
                    # Reset file pointer
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                    
                    # Save to temporary file for OpenCV
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[1] if hasattr(file_obj, 'name') else '.mp4') as tmp_file:
                        tmp_file.write(file_obj.read())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Open video with OpenCV
                        cap = cv2.VideoCapture(tmp_path)
                        if cap.isOpened():
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                            if fps > 0:
                                self.video_duration = frame_count / fps
                        cap.release()
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    
                    # Reset file pointer
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                except ImportError:
                    # OpenCV not available, skip video duration extraction
                    pass
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to extract video duration: {str(e)}")
                    
        except ImportError:
            # PIL not available, skip image dimension extraction
            pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to extract media metadata: {str(e)}")
    
    def save_uploaded_file(self, file_obj, user=None):
        """
        Save uploaded file to storage backend using ContentStorageManager.
        
        Args:
            file_obj: Uploaded file object
            user: User who uploaded the file (for logging)
            
        Returns:
            dict: Metadata about saved file
            
        Raises:
            ValueError: If validation fails
            StorageError: If save fails
        """
        from .storage import ContentStorageManager, StorageError
        
        try:
            # Save file using ContentStorageManager
            storage_path, metadata = ContentStorageManager.save_content(self, file_obj, user)
            
            # Update content instance with storage information
            self.storage_path = storage_path
            self.file_url = metadata.get('file_url', '')
            self.file_size = metadata.get('file_size')
            self.file_hash = metadata.get('file_hash')
            self.hash_algorithm = metadata.get('hash_algorithm', 'sha256')
            
            # Store storage_path for later use
            self._storage_path = storage_path
            
            # Extract metadata (image dimensions, video duration)
            self._extract_media_metadata(file_obj)
            
            # Save model
            update_fields = ['storage_path', 'file_url', 'file_size', 'file_hash', 'hash_algorithm']
            if self.image_width:
                update_fields.append('image_width')
            if self.image_height:
                update_fields.append('image_height')
            if self.video_duration:
                update_fields.append('video_duration')
            self.save(update_fields=update_fields)
            
            return metadata
            
        except StorageError as e:
            raise ValueError(f"Failed to save file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error saving file: {str(e)}")
    
    def get_secure_url(self, expiration=None):
        """
        Get secure URL for content file.
        
        Args:
            expiration: URL expiration time in seconds (for S3 signed URLs)
            
        Returns:
            str: Secure URL
        """
        from .storage import ContentStorageManager
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            url = ContentStorageManager.get_content_url(self, expiration)
            if not url:
                # If get_content_url returns empty, fallback to file_url
                logger.warning(f"Content {self.id}: get_content_url returned empty, using file_url")
                return self.file_url or ''
            return url
        except Exception as e:
            # Log error but don't fail - use fallback
            logger.warning(f"Content {self.id}: Error getting secure URL: {str(e)}, using file_url as fallback")
            # Fallback to regular file_url
            return self.file_url or ''
    
    def verify_integrity(self, file_obj=None):
        """
        Verify content file integrity using hash.
        
        Args:
            file_obj: Optional file object to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from .storage import ContentStorageManager
        
        return ContentStorageManager.verify_content_integrity(self, file_obj)
    
    def download_to_screen(self, screen, max_retries=3, timeout=30):
        """
        Download content to a specific Screen instance.
        
        This method handles the actual download process:
        1. Validates content and screen
        2. Uses secure URL from storage (S3 signed URL or local URL)
        3. Sends download command to screen via WebSocket or HTTP
        4. Updates download status
        5. Handles exceptions and retries
        
        Args:
            screen: Screen instance to download content to
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Request timeout in seconds (default: 30)
            
        Returns:
            bool: True if download successful, False otherwise
            
        Raises:
            ValueError: If content type doesn't require file download
            ConnectionError: If network connection fails
        """
        # Validate content is active
        if not self.is_active:
            raise ValueError("Cannot download inactive content")
        
        # Validate screen is online
        if not screen.is_online:
            raise ValueError(f"Screen {screen.name} is not online")
        
        # Check if retry limit exceeded
        if self.retry_count >= max_retries:
            self.mark_failed()
            return False
        
        # For non-file content types, just mark as downloaded
        if self.type in ['text', 'json', 'chart']:
            # These don't require file download, just mark as ready
            self.mark_downloaded()
            return True
        
        # For file-based content, perform actual download
        if not self.file_url:
            raise ValueError(f"Content {self.name} requires file_url for download")
        
        try:
            # Get secure URL (signed URL for S3, regular URL for local)
            secure_url = self.get_secure_url()
            
            # Verify integrity if hash is available
            # Note: If integrity check fails, we log it but don't block download
            # The screen can verify the file hash after download
            if self.file_hash:
                try:
                    is_valid, error = self.verify_integrity()
                    if not is_valid:
                        # Log warning but don't fail download - screen will verify hash
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(
                            f"Content {self.id} integrity check failed: {error}. "
                            f"Download will proceed, screen will verify hash."
                        )
                        # Don't raise exception - let download proceed
                except Exception as integrity_error:
                    # If integrity check itself fails (e.g., path issues), log but continue
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Content {self.id} integrity check error: {str(integrity_error)}. "
                        f"Download will proceed."
                    )
                    # Don't raise exception - let download proceed
            
            # In production, this would send a command to the screen via WebSocket
            # For now, we simulate the download process
            # The actual file transfer would happen on the screen side
            
            # Create download command for screen
            from commands.models import Command
            from django.db import transaction
            
            # Use atomic transaction for command creation and status update
            with transaction.atomic():
                command = Command.objects.create(
                    screen=screen,
                    type='sync_content',
                    payload={
                        'content_id': str(self.id),
                        'content_url': secure_url,
                        'content_type': self.type,
                        'file_size': self.file_size,
                        'file_hash': self.file_hash,
                        'hash_algorithm': self.hash_algorithm,
                    },
                    priority=5
                )
            
            # Execute command (this will send via WebSocket or queue for polling)
            # Note: For sync_content, if WebSocket is not available, command is queued
            # and screen will fetch it via /iot/commands/pending/ endpoint
            try:
                success = command.execute()
                
                if success:
                    # Use atomic transaction for status update and log creation
                    with transaction.atomic():
                        # Command was queued successfully (either sent via WebSocket or queued for polling)
                        # The screen needs to confirm receipt. We'll mark as pending.
                        # The status will be updated when screen sends confirmation
                        self.download_status = 'pending'
                        self.last_download_attempt = timezone.now()
                        self.save(update_fields=['download_status', 'last_download_attempt'])
                        
                        # Create pending download log entry
                        from log.models import ContentDownloadLog
                        ContentDownloadLog.objects.create(
                            content=self,
                            screen=screen,
                            status='pending',
                            file_size=self.file_size,
                            downloaded_at=None  # Will be set when screen confirms
                        )
                    
                    # Note: Actual download confirmation should come from screen
                    # via status update or command response
                    return True
                else:
                    # Command failed to send - check if it's because screen is offline
                    # If screen is offline, keep as pending (screen will fetch when online)
                    if not screen.is_online:
                        # Screen is offline, keep command as pending
                        with transaction.atomic():
                            self.download_status = 'pending'
                            self.last_download_attempt = timezone.now()
                            self.save(update_fields=['download_status', 'last_download_attempt'])
                            
                            from log.models import ContentDownloadLog
                            ContentDownloadLog.objects.create(
                                content=self,
                                screen=screen,
                                status='pending',
                                file_size=self.file_size,
                                error_message="Screen is offline, command queued for when screen comes online"
                            )
                        return True  # Return True because command is queued, not failed
                    
                    # Command failed to send and screen is online - mark as failed
                    with transaction.atomic():
                        self.mark_failed("Failed to send download command to screen")
                        # Create download log entry atomically
                        from log.models import ContentDownloadLog
                        ContentDownloadLog.objects.create(
                            content=self,
                            screen=screen,
                            status='failed',
                            retry_count=self.retry_count,
                            error_message="Failed to send download command to screen"
                        )
                    return False
                
            except Exception as cmd_error:
                # Command execution failed - use atomic transaction
                error_msg = str(cmd_error)
                with transaction.atomic():
                    self.mark_failed()
                    # Create download log entry atomically
                    from log.models import ContentDownloadLog
                    ContentDownloadLog.objects.create(
                        content=self,
                        screen=screen,
                        status='failed',
                        retry_count=self.retry_count,
                        error_message=error_msg
                    )
                
                raise ConnectionError(f"Download command failed: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            # Network or HTTP error - use atomic transaction
            error_msg = str(e)
            with transaction.atomic():
                self.mark_failed()
                # Create download log entry atomically
                from log.models import ContentDownloadLog
                ContentDownloadLog.objects.create(
                    content=self,
                    screen=screen,
                    status='failed',
                    retry_count=self.retry_count,
                    error_message=error_msg
                )
            
            raise ConnectionError(f"Download failed: {error_msg}")
        except Exception as e:
            # Other errors - use atomic transaction
            error_msg = str(e)
            with transaction.atomic():
                self.mark_failed()
                # Create download log entry atomically
                from log.models import ContentDownloadLog
                ContentDownloadLog.objects.create(
                    content=self,
                    screen=screen,
                    status='failed',
                    retry_count=self.retry_count,
                    error_message=error_msg
                )
            
            raise Exception(f"Download error: {error_msg}")
    
    def retry_download(self, screen, max_retries=3):
        """
        Retry downloading content to a screen if previous attempt failed.
        
        Args:
            screen: Screen instance to download content to
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            bool: True if retry successful, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # DEBUG: Log retry attempt
        print(f"DEBUG [retry_download model]: Starting retry for content {self.id} ({self.name})")
        print(f"DEBUG [retry_download model]: Current download_status: {self.download_status}")
        print(f"DEBUG [retry_download model]: Current retry_count: {self.retry_count}, max_retries: {max_retries}")
        
        # Only retry if status is 'failed' or 'pending'
        if self.download_status not in ['failed', 'pending']:
            # Log why retry is not allowed
            logger.info(f"Retry download skipped for content {self.id}: download_status is '{self.download_status}' (must be 'failed' or 'pending')")
            print(f"DEBUG [retry_download model]: Retry skipped - invalid status: {self.download_status}")
            return False
        
        # Check retry limit
        if self.retry_count >= max_retries:
            print(f"DEBUG [retry_download model]: Retry limit exceeded: {self.retry_count} >= {max_retries}")
            self.update_status('failed')
            return False
        
        # CRITICAL: Reset download_status to 'pending' before retry
        # This ensures the content is ready for download
        print(f"DEBUG [retry_download model]: Resetting download_status to 'pending'")
        self.download_status = 'pending'
        # Don't increment retry_count here - download_to_screen will handle it
        self.save(update_fields=['download_status'])
        print(f"DEBUG [retry_download model]: download_status reset to: {self.download_status}")
        
        try:
            result = self.download_to_screen(screen, max_retries=max_retries)
            print(f"DEBUG [retry_download model]: download_to_screen returned: {result}")
            print(f"DEBUG [retry_download model]: Final download_status: {self.download_status}")
            return result
        except Exception as e:
            # Log error properly
            logger.error(f"Retry download failed for content {self.id} ({self.name}) to screen {screen.id} ({screen.name}): {str(e)}", exc_info=True)
            print(f"DEBUG [retry_download model]: Exception occurred: {str(e)}")
            # Mark as failed on exception
            self.mark_failed(str(e))
            return False
    
    def _get_screen_storage_path(self, screen):
        """
        Get storage path for content on a specific screen.
        
        This is a helper method that generates the storage path.
        In production, this would integrate with screen's storage system.
        
        Args:
            screen: Screen instance
            
        Returns:
            str: Storage path for the content
        """
        # Generate path: screens/{screen_id}/content/{content_id}/{filename}
        screen_id = str(screen.id)
        content_id = str(self.id)
        
        # Get filename from URL or use content name
        if self.file_url:
            filename = os.path.basename(self.file_url.split('?')[0])
            if not filename:
                # Generate filename from type and id
                ext = self.file_extension or self._get_default_extension()
                filename = f"{self.name}_{content_id[:8]}{ext}"
        else:
            ext = self._get_default_extension()
            filename = f"{self.name}_{content_id[:8]}{ext}"
        
        return os.path.join('screens', screen_id, 'content', content_id, filename)
    
    def _get_default_extension(self):
        """Get default file extension based on content type"""
        extensions = {
            'image': '.jpg',
            'video': '.mp4',
            'webview': '.html',
        }
        return extensions.get(self.type, '')
    
    def _save_file_to_screen(self, response, screen, storage_path):
        """
        Save downloaded file to screen storage.
        
        This is a placeholder method. In production, this would:
        1. Use screen's API to transfer file
        2. Use FTP/SFTP for file transfer
        3. Use screen's local storage API
        
        Args:
            response: requests.Response object
            screen: Screen instance
            storage_path: Path where file should be saved
            
        Returns:
            bool: True if file saved successfully
        """
        # Placeholder implementation
        # In production, this would use actual file transfer mechanism
        
        # For now, just validate that we can read the file
        try:
            # Check if response has content
            if response.headers.get('content-length'):
                content_length = int(response.headers['content-length'])
                max_file_size = getattr(settings, 'CONTENT_STORAGE', {}).get('MAX_FILE_SIZE', 5 * 1024 * 1024 * 1024)
                if content_length > max_file_size:
                    max_size_gb = max_file_size / (1024 * 1024 * 1024)
                    raise ValueError(f"File size exceeds maximum allowed size ({max_size_gb:.0f}GB)")
            
            # In production, save to screen's storage
            # For now, return True to indicate "would be saved"
            return True
        except Exception as e:
            print(f"Error saving file to screen: {str(e)}")
            return False
    
    def validate_content(self):
        """
        Validate content data based on type.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate file_url for file-based content
        if self.type in ['image', 'video', 'webview']:
            if not self.file_url and not self.storage_path:
                return False, f"{self.type} content requires file_url or storage_path"
            
            # Validate URL format if file_url is provided
            if self.file_url:
                try:
                    URLValidator()(self.file_url)
                except ValidationError:
                    return False, "Invalid file_url format"
        
        # Validate text content: either file_url or text_content must be provided
        if self.type == 'text':
            if not self.file_url and not self.storage_path and not self.text_content:
                return False, "Text content requires either file_url/storage_path or text_content"
        
        # Validate content_json for JSON content
        if self.type == 'json':
            if not self.content_json:
                return False, "JSON content requires content_json"
            try:
                json.dumps(self.content_json)  # Validate JSON is serializable
            except (TypeError, ValueError):
                return False, "Invalid JSON in content_json"
        
        # Validate duration for time-based content
        if self.duration is not None and self.duration <= 0:
            return False, "Duration must be positive"
        
        # Validate file_size if provided
        if self.file_size is not None and self.file_size <= 0:
            return False, "File size must be positive"
        
        # Validate hash if provided
        if self.file_hash:
            # Check hash length based on algorithm
            if self.hash_algorithm == 'sha256' and len(self.file_hash) != 64:
                return False, "Invalid SHA-256 hash length (must be 64 characters)"
            elif self.hash_algorithm == 'md5' and len(self.file_hash) != 32:
                return False, "Invalid MD5 hash length (must be 32 characters)"
        
        return True, None
    
    def clean(self):
        """Run validation on save"""
        super().clean()
        is_valid, error = self.validate_content()
        if not is_valid:
            raise ValidationError(error)


class Schedule(models.Model):
    """
    Digital Signage Schedule model for managing time-based template scheduling.
    
    Schedules define when and how templates should be displayed on screens.
    Supports one-time and recurring schedules with priority-based conflict resolution.
    """
    
    # Core Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the schedule"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the schedule"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the schedule"
    )
    
    # Relations
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Template to be displayed in this schedule"
    )
    screens = models.ManyToManyField(
        'signage.Screen',
        blank=True,
        related_name='schedules',
        help_text="Screens where this schedule should run"
    )
    
    # Scheduling
    start_time = models.DateTimeField(
        help_text="Start time for the schedule"
    )
    end_time = models.DateTimeField(
        help_text="End time for the schedule"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the schedule is currently active"
    )
    REPEAT_TYPE_CHOICES = [
        ('none', 'None (One-time)'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    repeat_type = models.CharField(
        max_length=20,
        choices=REPEAT_TYPE_CHOICES,
        default='none',
        help_text="How often the schedule should repeat"
    )
    priority = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Priority level (higher values override lower ones in conflicts)"
    )
    
    # Status & Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this schedule was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this schedule was last updated"
    )
    last_executed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time this schedule was executed"
    )
    is_currently_running = models.BooleanField(
        default=False,
        help_text="Whether this schedule is currently active and running"
    )
    
    class Meta:
        db_table = 'templates_schedule'
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        ordering = ['-priority', 'start_time', 'name']
        indexes = [
            models.Index(fields=['template', 'is_active']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['is_active', 'start_time', 'end_time']),
            models.Index(fields=['repeat_type', 'is_active']),
            models.Index(fields=['priority', 'is_active']),
            models.Index(fields=['is_currently_running', 'start_time']),
        ]
    
    def __str__(self):
        """Return string representation: '{template name} - {name} ({start_time} to {end_time})'"""
        return f"{self.template.name} - {self.name} ({self.start_time} to {self.end_time})"
    
    def clean(self):
        """Validate schedule inputs with security checks"""
        super().clean()
        
        # Validate end_time is after start_time
        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time.'
                })
        
        # Validate repeat_type
        if self.repeat_type not in dict(self.REPEAT_TYPE_CHOICES).keys():
            raise ValidationError({
                'repeat_type': f'Invalid repeat_type: {self.repeat_type}'
            })
        
        # Validate datetime ranges to prevent injection
        from .recurrence import SecureRecurrenceCalculator
        try:
            SecureRecurrenceCalculator._validate_datetime(self.start_time, "start_time")
            SecureRecurrenceCalculator._validate_datetime(self.end_time, "end_time")
        except ValidationError as e:
            raise ValidationError(str(e))
        
        # Validate priority
        if self.priority < 0:
            raise ValidationError({
                'priority': 'Priority must be non-negative'
            })
    
    def _calculate_priority(self):
        """
        Auto-generate priority from start_time.
        Newer schedules (later start_time) get higher priority.
        """
        if not self.start_time:
            return 0
        start = self.start_time
        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        return int(start.timestamp())
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.priority = self._calculate_priority()
        self.full_clean()
        super().save(*args, **kwargs)
    
    # Helper Methods
    def activate(self):
        """Activate the schedule"""
        self.is_active = True
        self.save(update_fields=['is_active'])
    
    def deactivate(self):
        """Deactivate the schedule"""
        self.is_active = False
        self.is_currently_running = False
        self.save(update_fields=['is_active', 'is_currently_running'])
    
    def is_conflicting(self, other_schedule, check_range_days=365):
        """
        Check if this schedule conflicts with another schedule using accurate recurrence.
        
        Two schedules conflict if:
        1. They share at least one screen
        2. Their time ranges overlap (considering recurrence patterns)
        3. Both are active
        
        Args:
            other_schedule: Another Schedule instance to check against
            check_range_days: Number of days in the future to check for conflicts (default: 365)
            
        Returns:
            bool: True if schedules conflict, False otherwise
        """
        # Check if both are active
        if not (self.is_active and other_schedule.is_active):
            return False
        
        # Check if they share any screens
        shared_screens = self.screens.filter(id__in=other_schedule.screens.values_list('id', flat=True))
        if not shared_screens.exists():
            return False
        
        # For one-time schedules, simple overlap check
        if self.repeat_type == 'none' and other_schedule.repeat_type == 'none':
            # Overlap occurs if: start1 < end2 AND start2 < end1
            return (self.start_time < other_schedule.end_time and 
                    other_schedule.start_time < self.end_time)
        
        # For recurring schedules, check for overlaps in the future
        from .recurrence import SecureRecurrenceCalculator
        
        try:
            now = timezone.now()
            check_range_end = now + timedelta(days=check_range_days)
            
            return SecureRecurrenceCalculator.check_overlap(
                start1=self.start_time,
                end1=self.end_time,
                start2=other_schedule.start_time,
                end2=other_schedule.end_time,
                repeat_type1=self.repeat_type,
                repeat_type2=other_schedule.repeat_type,
                check_range_start=now,
                check_range_end=check_range_end
            )
        except Exception as e:
            # Log error but return False to be safe
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking conflict between schedules {self.id} and {other_schedule.id}: {str(e)}")
            # Fallback to simple check
            return (self.start_time < other_schedule.end_time and 
                    other_schedule.start_time < self.end_time)
    
    def next_run(self, reference_time=None):
        """
        Calculate the next scheduled run time using accurate recurrence calculation.
        
        Args:
            reference_time: Optional reference time for calculation (defaults to now)
        
        Returns:
            datetime: Next scheduled run time, or None if no more occurrences
        """
        from .recurrence import SecureRecurrenceCalculator, RecurrenceError
        
        try:
            return SecureRecurrenceCalculator.calculate_next_run(
                start_time=self.start_time,
                end_time=self.end_time,
                repeat_type=self.repeat_type,
                last_executed_at=self.last_executed_at,
                reference_time=reference_time
            )
        except (RecurrenceError, ValidationError) as e:
            # Log error but don't crash - return None to indicate calculation failed
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating next run for schedule {self.id}: {str(e)}")
            return None
    
    def mark_executed(self):
        """Mark schedule as executed at current time"""
        self.last_executed_at = timezone.now()
        self.is_currently_running = True
        self.save(update_fields=['last_executed_at', 'is_currently_running'])
    
    def mark_completed(self):
        """Mark schedule as completed (no longer running)"""
        self.is_currently_running = False
        self.save(update_fields=['is_currently_running'])
    
    # Property Methods
    @property
    def duration(self):
        """Calculate duration of schedule in seconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    @property
    def is_past(self):
        """Check if schedule has passed (for one-time schedules)"""
        if self.repeat_type == 'none':
            return timezone.now() > self.end_time
        return False
    
    @property
    def is_running_now(self):
        """
        Check if schedule should be running right now using accurate recurrence calculation.
        """
        if not self.is_active:
            return False
        
        from .recurrence import SecureRecurrenceCalculator
        
        try:
            return SecureRecurrenceCalculator.is_running_now(
                start_time=self.start_time,
                end_time=self.end_time,
                repeat_type=self.repeat_type,
                reference_time=timezone.now()
            )
        except Exception as e:
            # Log error but return False to be safe
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking if running now for schedule {self.id}: {str(e)}")
            return False
    
    @property
    def screens_count(self):
        """Get count of screens assigned to this schedule"""
        return self.screens.count()
    
    def execute_on_screens(self, force=False):
        """
        Execute this schedule on all assigned screens.
        Activates the template on each screen and handles conflicts.
        
        Args:
            force: If True, execute even if schedule is not due (default: False)
            
        Returns:
            dict: Execution results with success/failure counts and details
        """
        if not self.is_active:
            return {
                'success': False,
                'message': 'Schedule is not active',
                'screens_processed': 0,
                'screens_succeeded': 0,
                'screens_failed': 0,
                'details': []
            }
        
        if not force and not self.is_running_now:
            return {
                'success': False,
                'message': 'Schedule is not due to run',
                'screens_processed': 0,
                'screens_succeeded': 0,
                'screens_failed': 0,
                'details': []
            }
        
        # Get all screens assigned to this schedule
        screens = self.screens.filter(is_online=True)
        
        if not screens.exists():
            return {
                'success': False,
                'message': 'No online screens assigned to this schedule',
                'screens_processed': 0,
                'screens_succeeded': 0,
                'screens_failed': 0,
                'details': []
            }
        
        # Mark schedule as executed
        self.mark_executed()
        
        # Execute on each screen
        results = {
            'success': True,
            'message': f'Schedule executed on {screens.count()} screen(s)',
            'screens_processed': screens.count(),
            'screens_succeeded': 0,
            'screens_failed': 0,
            'details': []
        }
        
        for screen in screens:
            try:
                # Check for conflicts with other schedules
                conflicting_schedules = self._get_conflicting_schedules_for_screen(screen)
                
                # Resolve conflicts based on priority
                should_execute = True
                if conflicting_schedules:
                    highest_priority = max(
                        [self.priority] + [s.priority for s in conflicting_schedules]
                    )
                    if self.priority < highest_priority:
                        should_execute = False
                        results['details'].append({
                            'screen_id': str(screen.id),
                            'screen_name': screen.name,
                            'status': 'skipped',
                            'reason': f'Conflicting schedule with higher priority (priority: {highest_priority})'
                        })
                        continue
                
                # Activate template on screen
                success = self.template.activate_on_screen(screen, sync_content=True)
                
                if success:
                    results['screens_succeeded'] += 1
                    results['details'].append({
                        'screen_id': str(screen.id),
                        'screen_name': screen.name,
                        'status': 'success',
                        'template_id': str(self.template.id),
                        'template_name': self.template.name
                    })
                else:
                    results['screens_failed'] += 1
                    results['details'].append({
                        'screen_id': str(screen.id),
                        'screen_name': screen.name,
                        'status': 'failed',
                        'reason': 'Template activation failed'
                    })
                    
            except Exception as e:
                results['screens_failed'] += 1
                results['details'].append({
                    'screen_id': str(screen.id),
                    'screen_name': screen.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Mark schedule as completed if all screens processed
        if results['screens_processed'] == (results['screens_succeeded'] + results['screens_failed']):
            self.mark_completed()
        
        return results
    
    def _get_conflicting_schedules_for_screen(self, screen):
        """
        Get all schedules that conflict with this schedule for a specific screen.
        
        Args:
            screen: Screen instance
            
        Returns:
            list: List of conflicting Schedule instances
        """
        # Get all other active schedules that include this screen
        other_schedules = Schedule.objects.filter(
            screens=screen,
            is_active=True
        ).exclude(id=self.id)
        
        conflicting = []
        for schedule in other_schedules:
            if self.is_conflicting(schedule):
                conflicting.append(schedule)
        
        return conflicting
    
    def resolve_conflicts(self):
        """
        Resolve conflicts with other schedules based on priority.
        Deactivates lower priority conflicting schedules.
        
        Returns:
            dict: Conflict resolution results
        """
        if not self.is_active:
            return {
                'resolved': False,
                'message': 'Schedule is not active',
                'deactivated_schedules': []
            }
        
        deactivated = []
        
        # Get all conflicting schedules
        all_schedules = Schedule.objects.filter(is_active=True).exclude(id=self.id)
        for other_schedule in all_schedules:
            if self.is_conflicting(other_schedule):
                # If this schedule has higher or equal priority, deactivate the other
                if self.priority >= other_schedule.priority:
                    other_schedule.deactivate()
                    deactivated.append({
                        'id': str(other_schedule.id),
                        'name': other_schedule.name,
                        'priority': other_schedule.priority
                    })
        
        return {
            'resolved': True,
            'message': f'Resolved conflicts: deactivated {len(deactivated)} schedule(s)',
            'deactivated_schedules': deactivated
        }
