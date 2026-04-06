from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from django.db.models import Count
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import HttpResponseNotFound
from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.db.models import Q, Sum
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


def _qr_action_tables_exist():
    """True when QR action tables exist (migrate templates app through 0007+)."""
    try:
        with connection.cursor() as cursor:
            names = connection.introspection.table_names(cursor)
        return 'templates_qr_action_link' in names
    except Exception:
        return False


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
from .serializers import (
    TemplateSerializer, TemplateListSerializer, LayerSerializer,
    WidgetSerializer, ContentSerializer, ScheduleSerializer,
    ScheduleListSerializer, TemplateActivationSerializer,
    ScheduleExecutionSerializer, QRActionLinkSerializer,
    QRActionRuleSerializer, QRScanEventSerializer
)
from accounts.permissions import RolePermissions
from accounts.sidebar_config import has_permission
from log.models import ContentDownloadLog
from core.audit import AuditLogger
from core.api_errors import error_response


class TemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Template model.
    Provides CRUD operations with role-based permissions.
    """
    queryset = Template.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return TemplateListSerializer
        return TemplateSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        return self.request.user.get_accessible_templates_queryset()
    
    def create(self, request, *args, **kwargs):
        """Handle template creation with better error messages"""
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            template = serializer.instance
            
            # Log audit event
            try:
                AuditLogger.log_action(
                    action_type='create',
                    user=request.user,
                    resource=template,
                    description=f"Created template '{template.name}'",
                    changes={'before': None, 'after': {'name': template.name, 'width': template.width, 'height': template.height}},
                    request=request,
                )
            except Exception as audit_error:
                logger.error(f"Failed to log template creation audit: {audit_error}", exc_info=True)
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except PermissionDenied:
            raise
        except serializers.ValidationError as e:
            # Return detailed validation errors
            logger.warning(
                f"Template creation validation failed for user {request.user.id}: {e.detail}",
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'organization': getattr(request.user, 'organization', None) if request.user.is_authenticated else None,
                    'action_type': 'create_template',
                    'endpoint': request.path,
                }
            )
            return Response({
                'status': 'error',
                'errors': e.detail,
                'message': 'Template creation failed. Please check the provided data.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(
                f"Error creating template: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'organization': getattr(request.user, 'organization', None) if request.user.is_authenticated else None,
                    'action_type': 'create_template',
                    'endpoint': request.path,
                }
            )
            return Response({
                'status': 'error',
                'message': 'An error occurred while creating the template. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        if not has_permission(self.request.user, 'create_templates'):
            raise PermissionDenied("You do not have permission to create templates")
        template = serializer.save(created_by=self.request.user)
        
        # CRITICAL: Sync widgets from config_json to database AFTER save
        # This ensures widgets exist as database records for the Player to render
        self._sync_widgets_from_config(template, self.request.user)
    
    def perform_update(self, serializer):
        """Check permissions before update"""
        template = self.get_object()
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to edit templates")
        
        # Check if user can edit this template
        if not RolePermissions.can_edit_resource(user, template):
            raise PermissionDenied("You do not have permission to edit this template")
        
        # Store before state for audit log
        before_state = {
            'name': template.name,
            'width': template.width,
            'height': template.height,
            'is_active': template.is_active,
        }
        
        # Refresh template from database to get latest config_json
        template.refresh_from_db()
        
        # Save the template update
        serializer.save()
        
        # CRITICAL: Refresh again to get saved config_json
        template.refresh_from_db()
        
        # Sync widgets from config_json to database AFTER save
        # This ensures widgets exist as database records for the Player to render
        self._sync_widgets_from_config(template, user)
        
        # Log audit event
        try:
            after_state = {
                'name': template.name,
                'width': template.width,
                'height': template.height,
                'is_active': template.is_active,
            }
            AuditLogger.log_action(
                action_type='update',
                user=user,
                resource=template,
                description=f"Updated template '{template.name}'",
                changes={'before': before_state, 'after': after_state},
                request=self.request,
            )
        except Exception as audit_error:
            logger.error(f"Failed to log template update audit: {audit_error}", exc_info=True)
    
    def _sync_widgets_from_config(self, template, user):
        """
        Sync widgets from config_json to database Widget records.
        This ensures widgets exist as database records for content creation.
        CRITICAL: This function must run on every template save to sync config_json to database.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not template.config_json or not isinstance(template.config_json, dict):
            logger.info(f"[SYNC] Template {template.id} has no config_json, skipping widget sync")
            return
        
        widgets_data = template.config_json.get('widgets', [])
        if not widgets_data or not isinstance(widgets_data, list):
            logger.info(f"[SYNC] Template {template.id} has no widgets in config_json, skipping widget sync")
            return
        
        logger.info(f"[SYNC] Syncing {len(widgets_data)} widgets for Template {template.id} ({template.name})")
        
        # Get or create a default layer for this template
        from .models import Layer, Widget, Content, QRActionLink, QRActionRule
        default_layer, layer_created = Layer.objects.get_or_create(
            template=template,
            defaults={
                'name': 'Default Layer',
                'description': 'Default layer for template widgets',
                'x': 0,
                'y': 0,
                'width': template.width or 1920,
                'height': template.height or 1080,
                'z_index': 0,
                'is_active': True,
            }
        )
        
        if layer_created:
            logger.info(f"[SYNC] Created default layer {default_layer.id} for template {template.id}")
        else:
            # Update layer dimensions to match template if needed
            if default_layer.width != template.width or default_layer.height != template.height:
                default_layer.width = template.width or 1920
                default_layer.height = template.height or 1080
                default_layer.save(update_fields=['width', 'height'])
                logger.info(f"[SYNC] Updated default layer dimensions to {default_layer.width}x{default_layer.height}")
        
        # Check permissions for the layer
        if not RolePermissions.can_edit_resource(user, template):
            logger.warning(f"[SYNC] User {user.id} cannot edit template {template.id}, skipping widget sync")
            return
        
        # Process each widget from config_json
        synced_count = 0
        updated_count = 0
        created_count = 0
        
        for widget_data in widgets_data:
            widget_id_str = widget_data.get('id')
            if not widget_id_str:
                continue

            widget_type = widget_data.get('type', 'text')
            content_value = widget_data.get('content', '')
            if widget_type == 'weather':
                style_payload = widget_data.get('style', {}) if isinstance(widget_data.get('style', {}), dict) else {}
                # Keep weather widgets JSON-driven; map plain content text as a location fallback.
                if content_value and not style_payload.get('location'):
                    style_payload['location'] = str(content_value).strip()
                widget_data['style'] = style_payload
            if widget_type == 'qr_action':
                style_payload = widget_data.get('style', {}) if isinstance(widget_data.get('style', {}), dict) else {}
                if content_value and not style_payload.get('defaultUrl'):
                    style_payload['defaultUrl'] = str(content_value).strip()
                widget_data['style'] = style_payload
            url_widget_types = {'image', 'video', 'webview'}
            content_url_value = (content_value or None) if widget_type in url_widget_types else None
            
            # Try to parse as UUID (backend format)
            try:
                import uuid
                widget_uuid = uuid.UUID(widget_id_str)
            except (ValueError, TypeError):
                # Not a valid UUID - generate a new one
                widget_uuid = uuid.uuid4()
            
            # Parse position values (handle percentage strings)
            widget_x = self._parse_position(widget_data.get('x', '0'), template.width)
            widget_y = self._parse_position(widget_data.get('y', '0'), template.height)
            widget_width = self._parse_position(widget_data.get('width', '100'), template.width)
            widget_height = self._parse_position(widget_data.get('height', '100'), template.height)
            
            # Check if widget already exists
            widget, created = Widget.objects.get_or_create(
                id=widget_uuid,
                defaults={
                    'name': widget_data.get('name', f"{widget_data.get('type', 'widget')} Widget"),
                    'type': widget_type,
                    'layer': default_layer,
                    'x': widget_x,
                    'y': widget_y,
                    'width': widget_width,
                    'height': widget_height,
                    'z_index': widget_data.get('zIndex', widget_data.get('z_index', 0)),
                    'is_active': widget_data.get('visible', True) if 'visible' in widget_data else True,
                    'content_url': content_url_value,
                    'content_json': widget_data.get('style', {}),
                }
            )
            
            # Update existing widget if needed
            if not created:
                widget.name = widget_data.get('name', widget.name)
                widget.type = widget_type
                widget.x = widget_x
                widget.y = widget_y
                widget.width = widget_width
                widget.height = widget_height
                widget.z_index = widget_data.get('zIndex', widget_data.get('z_index', widget.z_index))
                widget.is_active = widget_data.get('visible', widget.is_active) if 'visible' in widget_data else widget.is_active
                widget.content_url = content_url_value
                if 'style' in widget_data:
                    widget.content_json = widget_data.get('style', {})
                # Ensure widget is assigned to default layer if not already assigned
                if not widget.layer or widget.layer.template != template:
                    widget.layer = default_layer
                widget.save()
                updated_count += 1
                logger.debug(f"[SYNC] Updated widget {widget.id} ({widget.name})")
            else:
                created_count += 1
                logger.debug(f"[SYNC] Created widget {widget.id} ({widget.name})")
            
            # Link Content records to this widget.
            # Supports both legacy single `content_id` and playlist-style `content_ids`.
            content_id = widget_data.get('content_id')
            content_ids = widget_data.get('content_ids')
            if not isinstance(content_ids, list):
                content_ids = []
            if content_id and content_id not in content_ids:
                content_ids.append(content_id)

            # Optional playlist item overrides:
            # - widget.playlist_items: [{content_id, durationSec, transition}]
            # - widget.style.playlist: [{content_id, durationSec, transition}]
            playlist_items = widget_data.get('playlist_items')
            if not isinstance(playlist_items, list):
                style_payload = widget_data.get('style', {}) if isinstance(widget_data.get('style', {}), dict) else {}
                playlist_items = style_payload.get('playlist', []) if isinstance(style_payload.get('playlist'), list) else []
            playlist_by_id = {}
            for item in playlist_items:
                if not isinstance(item, dict):
                    continue
                item_content_id = str(item.get('content_id') or '').strip()
                if item_content_id:
                    playlist_by_id[item_content_id] = item
                    if item_content_id not in content_ids:
                        content_ids.append(item_content_id)

            if content_ids:
                for index, linked_content_id in enumerate(content_ids):
                    try:
                        import uuid
                        content_uuid = uuid.UUID(linked_content_id) if isinstance(linked_content_id, str) else linked_content_id
                        content = Content.objects.filter(id=content_uuid).first()
                        if not content:
                            logger.warning(f"[SYNC] Content {linked_content_id} not found, cannot link to widget {widget.id}")
                            continue

                        playlist_meta = playlist_by_id.get(str(content.id), {})
                        content_order = int(playlist_meta.get('order', index))
                        duration_override = playlist_meta.get('durationSec')
                        transition_override = playlist_meta.get('transition')
                        content_json_patch = content.content_json if isinstance(content.content_json, dict) else {}
                        content_json_updated = False

                        if duration_override is not None:
                            try:
                                content.duration = float(duration_override)
                            except (TypeError, ValueError):
                                pass
                        if transition_override:
                            content_json_patch['transition'] = transition_override
                            content_json_updated = True

                        content.widget = widget
                        content.order = max(0, content_order)
                        update_fields = ['widget', 'order']
                        if duration_override is not None:
                            update_fields.append('duration')
                        if content_json_updated:
                            content.content_json = content_json_patch
                            update_fields.append('content_json')
                        content.save(update_fields=update_fields)
                        logger.debug(f"[SYNC] Linked content {content.id} to widget {widget.id} (order={content.order})")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"[SYNC] Invalid content_id {linked_content_id} for widget {widget.id}: {e}")

            # Keep text widgets in sync with a real Content record so Player can render text.
            if widget_type in {'text', 'marquee'}:
                style_data = widget_data.get('style', {}) if isinstance(widget_data.get('style', {}), dict) else {}
                style_text_value = style_data.get('text') or style_data.get('content') or ''
                text_value = (content_value or style_text_value or '').strip()
                if text_value:
                    text_content = Content.objects.filter(
                        widget=widget,
                        type='text',
                    ).order_by('order', 'created_at').first()

                    if text_content:
                        text_content.text_content = text_value
                        text_content.is_active = True
                        text_content.order = 0
                        text_content.save(update_fields=['text_content', 'is_active', 'order', 'updated_at'])
                    else:
                        Content.objects.create(
                            name=f"{widget.name} - Text",
                            type='text',
                            text_content=text_value,
                            widget=widget,
                            order=0,
                            is_active=True,
                        )

                    # Mirror text in widget JSON as extra fallback for clients.
                    if not isinstance(widget.content_json, dict):
                        widget.content_json = {}
                    if widget.content_json.get('text') != text_value:
                        widget.content_json['text'] = text_value
                        widget.save(update_fields=['content_json', 'updated_at'])
                elif widget_type == 'marquee' and isinstance(widget.content_json, dict):
                    # Keep marquee text fallback stable if db content exists but editor content is temporarily empty.
                    existing_text = (widget.content_json.get('text') or '').strip()
                    if not existing_text:
                        existing_item = Content.objects.filter(
                            widget=widget,
                            type='text',
                            is_active=True,
                        ).order_by('order', 'created_at').first()
                        recovered_text = (getattr(existing_item, 'text_content', '') or '').strip()
                        if recovered_text:
                            widget.content_json['text'] = recovered_text
                            widget.save(update_fields=['content_json', 'updated_at'])
            
            # CRITICAL: If widget has content_url but no Content record, create one
            # This ensures widgets with direct URLs (from config_json.content) have Content records
            widget_content_url = content_url_value or widget.content_url
            if widget_type in url_widget_types and widget_content_url and widget.contents.count() == 0:
                # Check if content already exists for this URL
                existing_content = Content.objects.filter(
                    widget=widget,
                    file_url=widget_content_url
                ).first()
                
                if not existing_content:
                    # Create Content record from widget's content_url
                    content_type_map = {
                        'image': 'image',
                        'video': 'video',
                        'text': 'text',
                        'marquee': 'text',
                        'clock': 'clock',
                        'date': 'text',
                        'weekday': 'text',
                        'webview': 'webview',
                        'chart': 'chart',
                        'qr_action': 'json',
                        'countdown': 'json',
                    }
                    content_type = content_type_map.get(widget_type, 'image')
                    
                    new_content = Content.objects.create(
                        name=f"{widget.name} - Content",
                        type=content_type,
                        file_url=widget_content_url,
                        widget=widget,
                        order=0,
                        is_active=True,
                    )
                    logger.info(f"[SYNC] Created Content {new_content.id} from widget {widget.id} content_url")
                else:
                    logger.debug(f"[SYNC] Content already exists for widget {widget.id} with URL {widget_content_url}")

            if widget_type == 'qr_action':
                style_data = widget_data.get('style', {}) if isinstance(widget_data.get('style', {}), dict) else {}
                default_url = (style_data.get('defaultUrl') or content_value or '').strip()
                if default_url and not _qr_action_tables_exist():
                    logger.warning(
                        "[SYNC] Missing DB table templates_qr_action_link; run "
                        "`python manage.py migrate templates`. Skipping QR sync for widget %s",
                        widget.id,
                    )
                elif default_url:
                    slug = str(style_data.get('slug') or f"w{str(widget.id).replace('-', '')[:12]}")
                    qr_link, _ = QRActionLink.objects.update_or_create(
                        widget=widget,
                        defaults={
                            'slug': slug,
                            'default_url': default_url,
                            'campaign_id': style_data.get('campaignId') or None,
                            'is_active': bool(style_data.get('isActive', True)),
                            'error_correction_level': style_data.get('errorCorrectionLevel', 'H'),
                            'settings_json': {
                                'ctaText': style_data.get('ctaText', ''),
                                'logoUrl': style_data.get('logoUrl', ''),
                                'foregroundColor': style_data.get('foregroundColor', '#000000'),
                                'backgroundColor': style_data.get('backgroundColor', '#ffffff'),
                                'quietZone': style_data.get('quietZone', 4),
                            },
                        },
                    )
                    rules = style_data.get('rules', []) if isinstance(style_data.get('rules', []), list) else []
                    qr_link.rules.all().delete()
                    for idx, rule in enumerate(rules):
                        if not isinstance(rule, dict):
                            continue
                        target_url = str(rule.get('targetUrl') or '').strip()
                        if not target_url:
                            continue
                        QRActionRule.objects.create(
                            link=qr_link,
                            name=rule.get('name') or f'Rule {idx + 1}',
                            priority=int(rule.get('priority', idx + 1)),
                            target_url=target_url,
                            start_hour=rule.get('startHour'),
                            end_hour=rule.get('endHour'),
                            days_of_week=rule.get('daysOfWeek') or [],
                            is_active=bool(rule.get('isActive', True)),
                            condition_json=rule.get('conditionJson') or {},
                        )
                    widget_data['style']['slug'] = qr_link.slug
                    widget_data['style']['redirectPath'] = f"/qr/{qr_link.slug}/"
                    widget_data['style']['displayUrl'] = default_url
                    widget.content_json = widget_data['style']
                    widget.save(update_fields=['content_json', 'updated_at'])
            
            # Update config_json with the actual widget UUID
            widget_data['id'] = str(widget.id)
            synced_count += 1
        
        logger.info(f"[SYNC] Completed sync for Template {template.id}: {synced_count} widgets synced ({created_count} created, {updated_count} updated)")
        
        # Save updated config_json back to template with backend widget IDs
        template.config_json['widgets'] = widgets_data
        template.save(update_fields=['config_json'])
    
    def _parse_position(self, value, canvas_size):
        """Parse position value (percentage or pixel) to pixels"""
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            if value.endswith('%'):
                percentage = float(value.rstrip('%'))
                return int((percentage / 100) * canvas_size)
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        return 0
    
    def perform_destroy(self, instance):
        """Check permissions before delete"""
        user = self.request.user

        if not has_permission(user, 'delete_templates'):
            raise PermissionDenied("You do not have permission to delete templates")
        
        # Only SuperAdmin, Admin, or creator can delete
        if not (user.has_full_access() or instance.created_by == user):
            raise PermissionDenied("You do not have permission to delete this template")
        
        # Store template info before deletion for audit log
        template_name = instance.name
        template_id = instance.id
        
        instance.delete()
        
        # Log audit event
        try:
            AuditLogger.log_action(
                action_type='delete',
                user=user,
                resource_type='Template',
                resource_name=template_name,
                description=f"Deleted template '{template_name}'",
                changes={'before': {'id': str(template_id), 'name': template_name}, 'after': None},
                request=self.request,
            )
        except Exception as audit_error:
            logger.error(f"Failed to log template deletion audit: {audit_error}", exc_info=True)
    
    @action(detail=True, methods=['post'])
    def activate_on_screen(self, request, id=None):
        """
        POST /api/templates/{id}/activate_on_screen/
        Activate this template on a specific screen.
        """
        template = self.get_object()
        serializer = TemplateActivationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Template activation validation failed')
        
        # Check permissions
        user = request.user
        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to activate this template")
        if not RolePermissions.can_edit_resource(user, template):
            raise PermissionDenied("You do not have permission to activate this template")
        
        from signage.models import Screen
        try:
            screen = Screen.objects.get(id=serializer.validated_data['screen_id'])
        except Screen.DoesNotExist:
            return Response(
                {'error': 'Screen not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user can access the screen
        if not RolePermissions.can_view_resource(user, screen):
            raise PermissionDenied("You do not have permission to access this screen")
        
        sync_content = serializer.validated_data.get('sync_content', True)
        
        logger.debug(
            "[activate_on_screen] activating template=%s screen=%s sync_content=%s",
            template.id,
            screen.id,
            sync_content,
        )
        
        success = template.activate_on_screen(screen, sync_content=sync_content)
        
        if success:
            # CRITICAL: Refresh screen from database to ensure active_template is committed
            # This ensures the player_template_endpoint will see the updated active_template
            screen.refresh_from_db()
            
            # CRITICAL: Clear any template cache for this screen
            # This ensures the player fetches the latest template data
            try:
                from django.core.cache import cache
                cache_key = f"screen_template_{screen.id}"
                cache.delete(cache_key)
                logger.debug("[activate_on_screen] cleared screen template cache for screen=%s", screen.id)
            except Exception as cache_error:
                logger.warning("[activate_on_screen] failed to clear cache: %s", cache_error)
            
            # Import ScreenSerializer to return full screen data
            from signage.serializers import ScreenSerializer
            
            screen_serializer = ScreenSerializer(screen, context={'request': request})
            screen_data = screen_serializer.data
            
            # Provide detailed response including updated screen data
            response_data = {
                'status': 'success',
                'message': f'Template "{template.name}" activated on screen "{screen.name}"',
                'template_id': str(template.id),
                'template_name': template.name,
                'screen_id': str(screen.id),
                'screen_online': screen.is_online,
                'content_sync': sync_content,
                # Include full updated screen data for frontend to update store immediately
                'screen': screen_data,
            }
            
            # Add warning if screen is offline and content sync was requested
            if not screen.is_online and sync_content:
                response_data['warning'] = 'Screen is offline. Content will be synced when screen comes online.'

            # Queue immediate commands for the player so it refreshes without waiting for next poll
            try:
                # High priority refresh to force template fetch
                screen.queue_command(
                    command_type='refresh',
                    payload={
                        'reason': 'template_activated',
                        'template_id': str(template.id)
                    },
                    priority=10
                )

                # Optional content sync command if requested
                if sync_content:
                    screen.queue_command(
                        command_type='sync_content',
                        payload={
                            'content_ids': []  # empty list => sync all
                        },
                        priority=5
                    )
                response_data['commands_queued'] = True
            except Exception as queue_error:
                # Don't fail activation if command queueing has an issue
                logger.warning("[activate_on_screen] failed to queue commands for screen=%s: %s", screen.id, queue_error)
                response_data['commands_queued'] = False
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to activate template. Template may not be active.'
            }, status=status.HTTP_400_BAD_REQUEST)


class LayerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Layer model.
    Provides CRUD operations with role-based permissions.
    """
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Filter queryset based on user permissions and template query parameter"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by template query parameter if provided
        template_id = self.request.query_params.get('template')
        if template_id:
            try:
                template = Template.objects.get(id=template_id)
                # Check if user has access to this template
                if user.has_full_access() or RolePermissions.can_view_resource(user, template):
                    return queryset.filter(template=template)
                else:
                    # User doesn't have access to this template
                    return queryset.none()
            except Template.DoesNotExist:
                # Template not found
                return queryset.none()
        
        # If no template filter, filter by template permissions
        accessible_templates = user.get_accessible_templates_queryset()
        return queryset.filter(template__in=accessible_templates)
    
    def perform_create(self, serializer):
        """Check permissions for template"""
        template = serializer.validated_data.get('template')
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to create layers for this template")
        
        if not RolePermissions.can_edit_resource(user, template):
            raise PermissionDenied("You do not have permission to create layers for this template")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Check permissions before update"""
        layer = self.get_object()
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to edit this layer")
        
        if not RolePermissions.can_edit_resource(user, layer.template):
            raise PermissionDenied("You do not have permission to edit this layer")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Check permissions before delete"""
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to delete this layer")
        
        if not RolePermissions.can_edit_resource(user, instance.template):
            raise PermissionDenied("You do not have permission to delete this layer")
        
        instance.delete()


class WidgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Widget model.
    Provides CRUD operations with role-based permissions.
    """
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Filter queryset based on user permissions and layer query parameter"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by layer query parameter if provided
        layer_id = self.request.query_params.get('layer')
        if layer_id:
            try:
                layer = Layer.objects.get(id=layer_id)
                # Check if user has access to this layer's template
                if user.has_full_access() or RolePermissions.can_view_resource(user, layer.template):
                    return queryset.filter(layer=layer)
                else:
                    # User doesn't have access to this layer
                    return queryset.none()
            except Layer.DoesNotExist:
                # Layer not found
                return queryset.none()
        
        # If no layer filter, filter by layer permissions (which filter by template)
        if user.has_full_access():
            return queryset
        
        accessible_templates = user.get_accessible_templates_queryset()
        # Get layers for accessible templates
        accessible_layers = Layer.objects.filter(template__in=accessible_templates)
        
        return queryset.filter(layer__in=accessible_layers)
    
    def perform_create(self, serializer):
        """Check permissions for layer"""
        layer = serializer.validated_data.get('layer')
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to create widgets for this layer")
        
        if not RolePermissions.can_edit_resource(user, layer.template):
            raise PermissionDenied("You do not have permission to create widgets for this layer")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Check permissions before update"""
        widget = self.get_object()
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to edit this widget")
        
        if not RolePermissions.can_edit_resource(user, widget.layer.template):
            raise PermissionDenied("You do not have permission to edit this widget")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Check permissions before delete"""
        user = self.request.user

        if not has_permission(user, 'edit_templates'):
            raise PermissionDenied("You do not have permission to delete this widget")
        
        if not RolePermissions.can_edit_resource(user, instance.layer.template):
            raise PermissionDenied("You do not have permission to delete this widget")
        
        instance.delete()


class ContentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Content model.
    Provides CRUD operations with role-based permissions.
    """
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_context(self):
        """Add request context to serializer for absolute URL generation"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def update(self, request, *args, **kwargs):
        """Handle content update with better error handling"""
        try:
            return super().update(request, *args, **kwargs)
        except PermissionDenied:
            raise
        except serializers.ValidationError as e:
            logger.error(f"Validation error updating content: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'errors': e.detail,
                'message': 'Content update failed validation. Please check the provided data.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating content: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Failed to update content: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_queryset(self):
        """Filter queryset based on user permissions - returns all content for user/org"""
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by user/organization ownership
        if not user.has_full_access():
            # Get accessible templates for widget-based content
            accessible_templates = user.get_accessible_templates_queryset()

            from .models import Layer, Widget
            accessible_layers = Layer.objects.filter(template__in=accessible_templates)
            accessible_widgets = Widget.objects.filter(layer__in=accessible_layers)

            queryset = queryset.filter(
                Q(widget__in=accessible_widgets) | Q(widget__isnull=True)
            )

        # List-only: Media Library / Upload UI should show only standalone uploads (widget is null).
        # Widget-bound rows created by template sync stay out unless ?widget=<id> is used.
        if getattr(self, 'action', None) == 'list':
            widget_id = self.request.query_params.get('widget')
            if widget_id:
                queryset = queryset.filter(widget_id=widget_id)
            else:
                lib = (self.request.query_params.get('library_only') or '').strip().lower()
                if lib in ('1', 'true', 'yes', 'on'):
                    queryset = queryset.filter(widget__isnull=True)

        return queryset

    @action(detail=False, methods=['get'])
    def storage_stats(self, request):
        """
        Return aggregated storage usage and configured limit for dashboard.
        """
        scoped_queryset = self.get_queryset()
        aggregate = scoped_queryset.aggregate(total_used_bytes=Sum('file_size'))
        used_bytes = aggregate.get('total_used_bytes') or 0
        max_file_size_bytes = getattr(settings, 'CONTENT_STORAGE', {}).get('MAX_FILE_SIZE', 5 * 1024 * 1024 * 1024)

        used_percentage = 0
        if max_file_size_bytes > 0:
            used_percentage = round((used_bytes / max_file_size_bytes) * 100, 2)

        return Response({
            'used_bytes': used_bytes,
            'limit_bytes': max_file_size_bytes,
            'used_percentage': min(100, used_percentage),
            'content_count': scoped_queryset.count(),
        }, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        """Check permissions for widget (optional - allows standalone media library)"""
        widget = serializer.validated_data.get('widget')
        user = self.request.user
        
        # Widget is now optional - allow standalone media library uploads
        if widget:
            try:
                if not widget.layer:
                    raise PermissionDenied("Widget must have a layer assigned")
                
                if not widget.layer.template:
                    raise PermissionDenied("Widget layer must have a template assigned")
                
                if not RolePermissions.can_edit_resource(user, widget.layer.template):
                    raise PermissionDenied("You do not have permission to create content for this widget")
            except AttributeError as e:
                logger.error(f"Error accessing widget relationships during content creation: {str(e)}", exc_info=True)
                raise PermissionDenied("Error checking permissions. Widget may have invalid relationships.")
        
        # Allow creating content without widget (standalone media library)
        serializer.save()
    
    def perform_update(self, serializer):
        """Check permissions before update (widget is now optional)"""
        content = self.get_object()
        user = self.request.user
        
        # Check if content has widget - if not, allow update (standalone media library)
        try:
            widget = content.widget
            if widget:
                # Content has widget - check widget permissions
                layer = widget.layer
                if not layer:
                    logger.error(f"Widget {widget.id} has no layer assigned")
                    raise PermissionDenied("Content widget must have a layer assigned")
                
                template = layer.template
                if not template:
                    logger.error(f"Layer {layer.id} has no template assigned")
                    raise PermissionDenied("Content widget layer must have a template assigned")
                
                # Check permissions
                if not RolePermissions.can_edit_resource(user, template):
                    raise PermissionDenied("You do not have permission to edit this content")
            # If no widget, allow update (standalone media library)
            
        except AttributeError as e:
            logger.error(f"Error accessing content relationships during update: {str(e)}", exc_info=True)
            logger.error(f"Content ID: {content.id}, Widget: {getattr(content, 'widget', None)}, "
                        f"Layer: {getattr(getattr(content, 'widget', None), 'layer', None) if content.widget else None}")
            raise PermissionDenied("Error checking permissions. Content may have invalid relationships. Please contact support.")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during content update permission check: {str(e)}", exc_info=True)
            raise PermissionDenied(f"Error updating content: {str(e)}")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Check permissions before delete (widget is optional)."""
        user = self.request.user

        # Content can be standalone (widget=None) when uploaded from media library.
        # Only enforce template-scoped permission checks when a widget chain exists.
        widget = getattr(instance, 'widget', None)
        if widget:
            layer = getattr(widget, 'layer', None)
            template = getattr(layer, 'template', None) if layer else None

            if not template:
                logger.error(
                    "Invalid content relationships during delete: content=%s widget=%s layer=%s",
                    instance.id,
                    getattr(widget, 'id', None),
                    getattr(layer, 'id', None) if layer else None,
                )
                raise PermissionDenied("Content widget must belong to a valid template")

            if not RolePermissions.can_edit_resource(user, template):
                raise PermissionDenied("You do not have permission to delete this content")
        
        # Store content info before deletion for audit log
        content_name = instance.name
        content_id = instance.id
        content_type = instance.type
        
        instance.delete()
        
        # Log audit event
        try:
            AuditLogger.log_action(
                action_type='delete',
                user=user,
                resource_type='Content',
                resource_name=content_name,
                description=f"Deleted content '{content_name}' (type: {content_type})",
                changes={'before': {'id': str(content_id), 'name': content_name, 'type': content_type}, 'after': None},
                request=self.request,
            )
        except Exception as audit_error:
            logger.error(f"Failed to log content deletion audit: {audit_error}", exc_info=True)
    
    @action(detail=True, methods=['post'])
    def download_to_screen(self, request, id=None):
        """
        POST /api/contents/{id}/download_to_screen/
        Download content to a specific screen.
        """
        content = self.get_object()
        screen_id = request.data.get('screen_id')
        
        if not screen_id:
            return Response(
                {'error': 'screen_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        user = request.user
        if not RolePermissions.can_edit_resource(user, content.widget.layer.template):
            raise PermissionDenied("You do not have permission to download this content")
        
        from signage.models import Screen
        try:
            screen = Screen.objects.get(id=screen_id)
        except Screen.DoesNotExist:
            return Response(
                {'error': 'Screen not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user can access the screen
        if not RolePermissions.can_view_resource(user, screen):
            raise PermissionDenied("You do not have permission to access this screen")
        
        try:
            success = content.download_to_screen(screen)
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Content "{content.name}" downloaded to screen "{screen.name}"',
                    'content_id': str(content.id),
                    'screen_id': str(screen.id)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Download failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def retry_download(self, request, id=None):
        """
        POST /api/contents/{id}/retry_download/
        Retry downloading content to a screen.
        
        Request body (optional):
        - screen_id: UUID of screen to retry download to (if not provided, retries to all screens using this content)
        - max_retries: Maximum number of retry attempts (default: 3)
        """
        content = self.get_object()
        user = request.user
        
        logger.info(f"Retry download request for content {content.id} by user {user.id if hasattr(user, 'id') else 'anonymous'}")
        
        logger.debug(
            "[retry_download] method=%s data_type=%s content_id=%s status=%s retries=%s",
            request.method,
            type(request.data),
            content.id,
            content.download_status,
            content.retry_count,
        )
        
        # Handle empty request body - allow retry without screen_id (will retry to all screens)
        # This is valid - screen_id is optional
        if not request.data:
            logger.debug("[retry_download] empty payload; retry all screens")
            # Set empty dict to avoid errors
            request._full_data = {}
        
        # Check permissions - verify user has access to this content
        try:
            from .storage import ContentStorageManager
            if not ContentStorageManager.verify_user_access(content, user):
                logger.warning(f"User {user.id if hasattr(user, 'id') else 'anonymous'} denied access to content {content.id}")
                raise PermissionDenied("You do not have permission to retry download for this content")
        except PermissionDenied:
            raise
        except (AttributeError, Exception) as e:
            logger.error(f"Error checking permissions for retry download: {e}", exc_info=True)
            raise PermissionDenied("You do not have permission to retry download for this content")
        
        # Try to get screen_id from request.data (handle different data formats)
        screen_id = None
        max_retries = 3
        
        if request.data:
            if isinstance(request.data, dict):
                screen_id = request.data.get('screen_id')
                max_retries = request.data.get('max_retries', 3)
            elif hasattr(request.data, 'get'):
                screen_id = request.data.get('screen_id')
                max_retries = request.data.get('max_retries', 3)
            else:
                # Try to access as attribute
                screen_id = getattr(request.data, 'screen_id', None)
                max_retries = getattr(request.data, 'max_retries', 3)
        
        logger.debug(f"Received screen_id: {screen_id} (type: {type(screen_id)})")
        logger.debug(f"Received max_retries: {max_retries} (type: {type(max_retries)})")
        logger.debug("[retry_download] extracted screen_id=%s max_retries=%s", screen_id, max_retries)
        
        # Handle empty string or None
        if screen_id == '' or screen_id is None:
            screen_id = None
            logger.info("No screen_id provided, will retry to all screens using this content")
        
        # Validate max_retries
        try:
            max_retries = int(max_retries)
            if max_retries < 1:
                max_retries = 3
        except (ValueError, TypeError):
            max_retries = 3
        
        # If screen_id is provided, retry to that specific screen
        if screen_id:
            # Validate screen_id format (should be UUID)
            try:
                import uuid
                # Convert to string and validate UUID format
                screen_id_str = str(screen_id).strip()
                logger.debug("[retry_download] validating screen_id=%s", screen_id_str)
                uuid.UUID(screen_id_str)
                screen_id = screen_id_str  # Use cleaned string
            except (ValueError, AttributeError) as e:
                logger.debug("[retry_download] invalid screen_id format=%s error=%s", screen_id, e)
                return Response(
                    {'error': f'Invalid screen_id format: {screen_id}. Must be a valid UUID.', 'received': str(screen_id)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from signage.models import Screen
            try:
                screen = Screen.objects.get(id=screen_id)
            except Screen.DoesNotExist:
                return Response(
                    {'error': f'Screen not found with id: {screen_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"Error fetching screen {screen_id}: {str(e)}")
                return Response(
                    {'error': f'Error fetching screen: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Check if user can access the screen
            if not RolePermissions.can_view_resource(user, screen):
                raise PermissionDenied("You do not have permission to access this screen")
            
            # Check if screen is online
            if not screen.is_online:
                return Response({
                    'status': 'error',
                    'message': f'Screen "{screen.name}" is not online. Cannot download content to offline screen.',
                    'content_id': str(content.id),
                    'screen_id': str(screen.id),
                    'screen_online': screen.is_online
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if content has file_url (required for download)
            if not content.file_url and content.type in ['image', 'video', 'webview']:
                return Response({
                    'status': 'error',
                    'message': f'Content "{content.name}" has no file URL. Please upload a file first.',
                    'content_id': str(content.id),
                    'screen_id': str(screen.id),
                    'content_type': content.type
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if content is active
            if not content.is_active:
                return Response({
                    'status': 'error',
                    'message': f'Content "{content.name}" is not active. Cannot download inactive content.',
                    'content_id': str(content.id),
                    'screen_id': str(screen.id),
                    'is_active': content.is_active
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                logger.info(f"Attempting retry download for content {content.id} to screen {screen.id}")
                logger.debug(f"Content status: {content.download_status}, retry_count: {content.retry_count}, max_retries: {max_retries}")
                
                # Check if content can be retried
                if content.download_status not in ['failed', 'pending']:
                    error_msg = f'Cannot retry download: content status is "{content.download_status}" (must be "failed" or "pending")'
                    logger.warning(f"Retry download blocked: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg,
                        'content_id': str(content.id),
                        'screen_id': str(screen.id),
                        'download_status': content.download_status
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check retry count
                if content.retry_count >= max_retries:
                    error_msg = f'Maximum retry attempts ({max_retries}) exceeded. Current retry count: {content.retry_count}'
                    logger.warning(f"Retry download blocked: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg,
                        'content_id': str(content.id),
                        'screen_id': str(screen.id),
                        'retry_count': content.retry_count,
                        'max_retries': max_retries
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                logger.info(f"Calling content.retry_download() for content {content.id} to screen {screen.id}")
                success = content.retry_download(screen, max_retries=max_retries)
                logger.info(f"Retry download result: {success} for content {content.id} to screen {screen.id}")
                
                # Refresh content from DB to get updated status
                content.refresh_from_db()
                
                logger.debug(
                    "[retry_download] post-retry content_id=%s status=%s retries=%s",
                    content.id,
                    content.download_status,
                    content.retry_count,
                )
                
                if success:
                    # Import ContentSerializer to return full updated content data
                    from .serializers import ContentSerializer
                    
                    # Serialize updated content for frontend
                    content_serializer = ContentSerializer(content, context={'request': request})
                    content_data = content_serializer.data
                    
                    logger.debug(
                        "[retry_download] serialized content response content_id=%s status=%s",
                        content.id,
                        content_data.get('download_status'),
                    )
                    
                    return Response({
                        'status': 'success',
                        'message': f'Content "{content.name}" retry download successful to screen "{screen.name}"',
                        'content_id': str(content.id),
                        'screen_id': str(screen.id),
                        'download_status': content.download_status,
                        'retry_count': content.retry_count,
                        # Include full updated content data for frontend to update store immediately
                        'content': content_data
                    }, status=status.HTTP_200_OK)
                else:
                    # Get more details about why it failed
                    error_msg = 'Retry download failed'
                    if content.download_status == 'success':
                        error_msg = 'Content is already successfully downloaded'
                    elif content.retry_count >= max_retries:
                        error_msg = f'Maximum retry attempts ({max_retries}) exceeded'
                    else:
                        error_msg = f'Retry download failed (retry count: {content.retry_count}/{max_retries})'
                    
                    logger.warning(f"Retry download returned False for content {content.id} to screen {screen.id}: {error_msg}")
                    return Response({
                        'status': 'error',
                        'message': error_msg,
                        'content_id': str(content.id),
                        'screen_id': str(screen.id),
                        'download_status': content.download_status,
                        'retry_count': content.retry_count
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                # Handle validation errors from download_to_screen
                error_msg = str(e)
                logger.warning(f"Validation error during retry download for content {content.id} to screen {screen.id}: {error_msg}")
                return Response({
                    'status': 'error',
                    'message': error_msg,
                    'content_id': str(content.id),
                    'screen_id': str(screen.id),
                    'error_type': 'ValidationError'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                error_msg = f'Retry download failed: {str(e)}'
                logger.error(f"Error during retry download for content {content.id} to screen {screen.id}: {error_msg}", exc_info=True)
                return Response({
                    'status': 'error',
                    'message': error_msg,
                    'content_id': str(content.id),
                    'screen_id': str(screen.id),
                    'error_type': type(e).__name__
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # No screen_id provided - retry to all screens that use this content
            try:
                # Get all screens that have this content's template active
                widget = content.widget
                if not widget:
                    return Response({
                        'error': 'Content has no widget assigned'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                layer = widget.layer
                if not layer:
                    return Response({
                        'error': 'Content widget has no layer assigned'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                template = layer.template
                if not template:
                    return Response({
                        'error': 'Content layer has no template assigned'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get all screens with this template
                from signage.models import Screen
                screens = Screen.objects.filter(active_template=template, is_online=True)
                
                if not screens.exists():
                    return Response({
                        'status': 'error',
                        'message': 'No online screens found with this template',
                        'content_id': str(content.id)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Retry download to all screens
                results = []
                for screen in screens:
                    try:
                        success = content.retry_download(screen, max_retries=max_retries)
                        results.append({
                            'screen_id': str(screen.id),
                            'screen_name': screen.name,
                            'success': success,
                            'download_status': content.download_status
                        })
                    except Exception as e:
                        logger.error(f"Error retrying download to screen {screen.id}: {str(e)}")
                        results.append({
                            'screen_id': str(screen.id),
                            'screen_name': screen.name,
                            'success': False,
                            'error': str(e)
                        })
                
                success_count = sum(1 for r in results if r.get('success'))
                
                return Response({
                    'status': 'success' if success_count > 0 else 'partial',
                    'message': f'Retry download completed: {success_count}/{len(results)} screens successful',
                    'content_id': str(content.id),
                    'results': results
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error during bulk retry download: {str(e)}", exc_info=True)
                return Response({
                    'status': 'error',
                    'message': f'Retry download failed: {str(e)}',
                    'content_id': str(content.id)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, id=None):
        """
        POST /api/contents/{id}/upload/
        Upload a file for content.
        Requires multipart/form-data with 'file' field.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Upload request received for content ID: {id}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Request FILES keys: {list(request.FILES.keys()) if request.FILES else 'EMPTY'}")
        logger.info(f"Request POST keys: {list(request.POST.keys()) if request.POST else 'EMPTY'}")
        
        content = self.get_object()
        user = request.user
        
        logger.info(f"Content found: {content.id} ({content.name}), Type: {content.type}")
        logger.info(f"User: {user.id if hasattr(user, 'id') else 'Anonymous'} ({user.username if hasattr(user, 'username') else 'N/A'})")
        
        # Check permissions with proper null checks (widget is now optional)
        try:
            widget = content.widget
            if widget:
                # Content has widget - check widget permissions
                layer = widget.layer
                if not layer:
                    logger.error(f"Widget {widget.id} has no layer assigned")
                    return Response(
                        {'error': 'Content widget must have a layer assigned'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                template = layer.template
                if not template:
                    logger.error(f"Layer {layer.id} has no template assigned")
                    return Response(
                        {'error': 'Content widget layer must have a template assigned'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check permissions
                if not RolePermissions.can_edit_resource(user, template):
                    raise PermissionDenied("You do not have permission to upload content for this widget")
            # If no widget, allow upload (standalone media library)
                
        except AttributeError as e:
            logger.error(f"Error accessing content relationships during upload: {str(e)}", exc_info=True)
            logger.error(f"Content ID: {content.id}, Widget: {getattr(content, 'widget', None)}, "
                        f"Layer: {getattr(getattr(content, 'widget', None), 'layer', None) if content.widget else None}")
            return Response(
                {'error': 'Error checking permissions. Content may have invalid relationships. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except PermissionDenied:
            raise
        
        # Check if file is provided
        if 'file' not in request.FILES:
            logger.error(f"Upload failed: No 'file' field in request.FILES. Available keys: {list(request.FILES.keys())}")
            logger.error(f"Request content type: {request.content_type}")
            logger.error(f"Request method: {request.method}")
            
            # Check if request body exists
            if hasattr(request, 'body'):
                logger.debug(f"Request body length: {len(request.body) if request.body else 0}")
            
            return Response(
                {
                    'error': 'File is required',
                    'message': 'Use multipart/form-data with "file" field.',
                    'received_fields': list(request.FILES.keys()) if request.FILES else [],
                    'content_type': request.content_type
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.FILES['file']
        
        logger.info(f"File received: {file_obj.name}, Size: {file_obj.size} bytes, Type: {file_obj.content_type}")
        
        try:
            # Validate content before saving (comprehensive validation is done in storage.py)
            # Additional pre-save checks can be added here if needed
            
            logger.info(f"Starting file save process for content {content.id}")
            
            # Save uploaded file (includes comprehensive validation)
            metadata = content.save_uploaded_file(file_obj, user)
            
            logger.info(f"File saved successfully. Metadata: {metadata}")
            
            # After successful upload, sync content to all screens that use this template
            # and ensure template is active
            sync_results = []
            template_info = None
            try:
                # Get template from content relationships
                widget = content.widget
                if widget:
                    layer = widget.layer
                    if layer:
                        template = layer.template
                        if template:
                            template_info = {
                                'template_id': str(template.id),
                                'template_name': template.name
                            }
                            
                            # Get all screens that have this template assigned
                            screens = template.screens.all()
                            
                            if screens.count() == 0:
                                logger.warning(f"Template {template.id} has no screens assigned. Content uploaded but not synced.")
                            else:
                                logger.info(f"Syncing content {content.id} to {screens.count()} screens for template {template.id}")
                                
                                # Sync content to all online screens
                                for screen in screens:
                                    if screen.is_online:
                                        try:
                                            logger.info(f"Syncing content {content.id} to screen {screen.id}")
                                            success = content.download_to_screen(screen)
                                            sync_results.append({
                                                'screen_id': str(screen.id),
                                                'screen_name': screen.name,
                                                'success': success
                                            })
                                            if success:
                                                logger.info(f"Content {content.id} synced successfully to screen {screen.id}")
                                            else:
                                                logger.warning(f"Content {content.id} sync failed to screen {screen.id}")
                                        except Exception as e:
                                            logger.error(f"Error syncing content {content.id} to screen {screen.id}: {str(e)}")
                                            sync_results.append({
                                                'screen_id': str(screen.id),
                                                'screen_name': screen.name,
                                                'success': False,
                                                'error': str(e)
                                            })
                                    else:
                                        logger.info(f"Screen {screen.id} is offline, skipping sync (will sync when online)")
                                        sync_results.append({
                                            'screen_id': str(screen.id),
                                            'screen_name': screen.name,
                                            'success': False,
                                            'error': 'Screen is offline'
                                        })
            except Exception as e:
                logger.error(f"Error during content sync after upload: {str(e)}", exc_info=True)
                # Don't fail the upload if sync fails
            
            # Note: We don't log uploads to ContentDownloadLog as that's for screen-specific downloads
            # Uploads are logged via the content's created_at/updated_at timestamps
            
            # Build absolute URL for file_url
            absolute_file_url = content.file_url
            if content.file_url:
                if content.file_url.startswith('http'):
                    absolute_file_url = content.file_url
                else:
                    absolute_file_url = request.build_absolute_uri(content.file_url)
            
            response_data = {
                'status': 'success',
                'message': f'File uploaded successfully for content "{content.name}"',
                'content_id': str(content.id),
                'file_url': content.file_url,
                'absolute_file_url': absolute_file_url,
                'file_size': content.file_size,
                'file_hash': content.file_hash,
                'storage_path': content.storage_path,
                'sync_results': sync_results
            }
            
            if template_info:
                response_data['template'] = template_info
            
            if sync_results:
                success_count = sum(1 for r in sync_results if r.get('success'))
                response_data['sync_summary'] = {
                    'total_screens': len(sync_results),
                    'successful_syncs': success_count,
                    'failed_syncs': len(sync_results) - success_count
                }
            else:
                if template_info:
                    response_data['warning'] = f'Template "{template_info["template_name"]}" has no screens assigned. Please assign template to a screen to display content.'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error during content upload: {error_msg}", exc_info=True)
            
            # Extract detailed error information
            error_details = {
                'status': 'error',
                'error': 'Validation failed',
                'message': error_msg,
                'content_id': str(content.id),
                'file_name': file_obj.name if file_obj else None
            }
            
            # Add specific error type if available
            if 'MIME type' in error_msg or 'fake' in error_msg.lower():
                error_details['error_type'] = 'MIME_TYPE_MISMATCH'
                error_details['message'] = (
                    f"The file '{file_obj.name if file_obj else 'unknown'}' has been rejected for security reasons. "
                    f"{error_msg}"
                )
            elif 'resolution' in error_msg.lower() or '4K' in error_msg:
                error_details['error_type'] = 'RESOLUTION_EXCEEDED'
            elif 'size' in error_msg.lower() or 'MB' in error_msg:
                error_details['error_type'] = 'FILE_SIZE_EXCEEDED'
            elif 'Security' in error_msg or 'security' in error_msg.lower():
                error_details['error_type'] = 'SECURITY_VIOLATION'
                error_details['message'] = (
                    f"The file '{file_obj.name if file_obj else 'unknown'}' has been rejected for security reasons. "
                    f"{error_msg}"
                )
            
            return Response(error_details, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Unexpected error during content upload ({error_type}): {error_msg}", exc_info=True)
            return Response({
                'status': 'error',
                'error': 'Upload failed',
                'message': error_msg,
                'error_type': error_type,
                'content_id': str(content.id),
                'file_name': file_obj.name if file_obj else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def preview(self, request, id=None):
        """
        GET /api/contents/{id}/preview/
        Get preview URL for content file.
        Returns media URL for local storage or signed URL for S3.
        """
        content = self.get_object()
        user = request.user
        
        # Check permissions
        try:
            template = content.widget.layer.template
            if not RolePermissions.can_view_resource(user, template):
                raise PermissionDenied("You do not have permission to preview this content")
        except (AttributeError, Exception) as e:
            logger.error(f"Error checking permissions for content preview: {e}")
            raise PermissionDenied("You do not have permission to preview this content")
        
        if not content.file_url and not content.storage_path:
            return Response(
                {'error': 'Content has no file to preview'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Get preview URL (no expiration for preview, or use short expiration)
            preview_url = content.get_secure_url(expiration=3600)  # 1 hour for preview
            
            return Response({
                'status': 'success',
                'content_id': str(content.id),
                'preview_url': preview_url,
                'content_type': content.type,
                'file_size': content.file_size,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating preview URL: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Failed to generate preview URL: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, id=None):
        """
        GET /api/contents/{id}/download/
        Get secure download URL for content file.
        Returns signed URL for S3 or media URL for local storage.
        """
        content = self.get_object()
        user = request.user
        
        # Check permissions - verify user has access to this content
        try:
            from .storage import ContentStorageManager
            if not ContentStorageManager.verify_user_access(content, user):
                raise PermissionDenied("You do not have permission to download this content")
        except PermissionDenied:
            raise
        except (AttributeError, Exception) as e:
            logger.error(f"Error checking permissions for content download: {e}")
            raise PermissionDenied("You do not have permission to download this content")
        
        if not content.file_url and not content.storage_path:
            return Response(
                {'error': 'Content has no file to download'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Get expiration from query params (optional)
            expiration = request.query_params.get('expiration', None)
            expiration = int(expiration) if expiration else None
            
            # Get secure URL
            secure_url = content.get_secure_url(expiration)
            
            # Log download access
            from log.models import ContentDownloadLog
            ContentDownloadLog.objects.create(
                content=content,
                status='success',
                file_size=content.file_size,
                downloaded_at=timezone.now()
            )
            
            return Response({
                'status': 'success',
                'content_id': str(content.id),
                'download_url': secure_url,
                'expiration': expiration or getattr(settings, 'CONTENT_STORAGE', {}).get('SIGNED_URL_EXPIRATION', 3600),
                'file_size': content.file_size,
                'file_hash': content.file_hash,
                'hash_algorithm': content.hash_algorithm
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to generate download URL: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def verify_integrity(self, request, id=None):
        """
        POST /api/contents/{id}/verify_integrity/
        Verify content file integrity using hash.
        """
        content = self.get_object()
        user = request.user
        
        # Check permissions
        if not RolePermissions.can_view_resource(user, content.widget.layer.template):
            raise PermissionDenied("You do not have permission to verify this content")
        
        if not content.file_hash:
            return Response({
                'status': 'warning',
                'message': 'Content has no hash for integrity verification'
            }, status=status.HTTP_200_OK)
        
        try:
            is_valid, error = content.verify_integrity()
            
            if is_valid:
                return Response({
                    'status': 'success',
                    'message': 'Content integrity verified successfully',
                    'content_id': str(content.id),
                    'file_hash': content.file_hash,
                    'hash_algorithm': content.hash_algorithm
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': f'Content integrity check failed: {error}',
                    'content_id': str(content.id)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Integrity verification failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Schedule model.
    Provides CRUD operations with role-based permissions and schedule execution.
    """
    queryset = Schedule.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ScheduleListSerializer
        return ScheduleSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # SuperAdmin and Admin can see all schedules
        if user.has_full_access():
            return queryset
        
        # Manager / Employee: org or own templates; Visitor: same template scope as Template list (sample + org read-only)
        if user.can_manage_own_resources():
            org_users = user.get_organization_users()
            accessible_templates = Template.objects.filter(
                Q(created_by=user) | Q(created_by__in=org_users)
            )
        elif user.is_visitor():
            accessible_templates = user.get_accessible_templates_queryset()
        else:
            accessible_templates = Template.objects.filter(created_by=user)
        
        return queryset.filter(template__in=accessible_templates)
    
    def perform_create(self, serializer):
        """Check permissions for template"""
        template = serializer.validated_data.get('template')
        user = self.request.user
        
        # Only SuperAdmin, Admin, Operator, Manager can create schedules
        if not user.can_manage_own_resources():
            raise PermissionDenied("You do not have permission to create schedules")
        
        if not RolePermissions.can_edit_resource(user, template):
            raise PermissionDenied("You do not have permission to create schedules for this template")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Check permissions before update"""
        schedule = self.get_object()
        user = self.request.user
        
        # Only SuperAdmin, Admin, Operator, Manager can update schedules
        if not user.can_manage_own_resources():
            raise PermissionDenied("You do not have permission to update schedules")
        
        if not RolePermissions.can_edit_resource(user, schedule.template):
            raise PermissionDenied("You do not have permission to edit this schedule")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Check permissions before delete"""
        user = self.request.user
        
        # Only SuperAdmin, Admin, Operator, Manager can delete schedules
        if not user.can_manage_own_resources():
            raise PermissionDenied("You do not have permission to delete schedules")
        
        if not RolePermissions.can_edit_resource(user, instance.template):
            raise PermissionDenied("You do not have permission to delete this schedule")
        
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def execute(self, request, id=None):
        """
        POST /api/schedules/{id}/execute/
        Execute a schedule on its assigned screens.
        """
        schedule = self.get_object()
        serializer = ScheduleExecutionSerializer(data=request.data, instance=schedule)
        
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Schedule execution validation failed')
        
        # Check permissions
        user = request.user
        if not user.can_execute_commands():
            raise PermissionDenied("You do not have permission to execute schedules")
        
        if not RolePermissions.can_edit_resource(user, schedule.template):
            raise PermissionDenied("You do not have permission to execute this schedule")
        
        force = serializer.validated_data.get('force', False)
        
        # Check if schedule should run
        if not force and not schedule.is_running_now:
            return Response({
                'status': 'error',
                'message': 'Schedule is not due to run. Use force=true to execute anyway.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute schedule
        result = schedule.execute_on_screens()
        
        return Response({
            'status': 'success',
            'message': f'Schedule "{schedule.name}" executed',
            'schedule_id': str(schedule.id),
            'execution_result': result
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def due_schedules(self, request):
        """
        GET /api/schedules/due_schedules/
        Get all schedules that are due to run now.
        """
        user = request.user
        
        # Get accessible schedules
        queryset = self.get_queryset()
        
        # Filter for schedules that are running now
        due_schedules = []
        for schedule in queryset:
            if schedule.is_running_now:
                due_schedules.append(schedule)
        
        serializer = self.get_serializer(due_schedules, many=True)
        return Response({
            'count': len(due_schedules),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def conflicting(self, request):
        """
        GET /api/schedules/conflicting/
        Get all schedule conflicts.
        """
        user = request.user
        
        if not user.has_full_access():
            raise PermissionDenied("Only administrators can view schedule conflicts")
        
        queryset = self.get_queryset().filter(is_active=True)
        conflicts = []
        
        schedules = list(queryset)
        for i, schedule1 in enumerate(schedules):
            for schedule2 in schedules[i+1:]:
                if schedule1.is_conflicting(schedule2):
                    conflicts.append({
                        'schedule1': {
                            'id': str(schedule1.id),
                            'name': schedule1.name,
                            'priority': schedule1.priority
                        },
                        'schedule2': {
                            'id': str(schedule2.id),
                            'name': schedule2.name,
                            'priority': schedule2.priority
                        },
                        'resolution': 'schedule1' if schedule1.priority >= schedule2.priority else 'schedule2'
                    })
        
        return Response({
            'count': len(conflicts),
            'conflicts': conflicts
        }, status=status.HTTP_200_OK)


class QRActionLinkViewSet(viewsets.ModelViewSet):
    queryset = QRActionLink.objects.select_related('widget', 'widget__layer', 'widget__layer__template')
    serializer_class = QRActionLinkSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.has_full_access():
            return queryset
        if user.can_manage_own_resources():
            org_users = user.get_organization_users()
            accessible_templates = Template.objects.filter(
                Q(created_by=user) | Q(created_by__in=org_users)
            )
        else:
            accessible_templates = Template.objects.filter(created_by=user)
        return queryset.filter(widget__layer__template__in=accessible_templates)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        link_id = request.query_params.get('link_id')
        campaign_id = request.query_params.get('campaign_id')
        queryset = QRScanEvent.objects.all()
        if link_id:
            queryset = queryset.filter(link_id=link_id)
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)

        daily_rows = (
            queryset.extra(select={'day': "date(created_at)"})
            .values('day')
            .annotate(scans=Count('id'))
            .order_by('-day')[:30]
        )
        return Response({
            'total_scans': queryset.count(),
            'daily': list(daily_rows),
        }, status=status.HTTP_200_OK)


class QRActionRuleViewSet(viewsets.ModelViewSet):
    queryset = QRActionRule.objects.select_related('link', 'link__widget', 'link__widget__layer', 'link__widget__layer__template')
    serializer_class = QRActionRuleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.has_full_access():
            return queryset
        if user.can_manage_own_resources():
            org_users = user.get_organization_users()
            accessible_templates = Template.objects.filter(
                Q(created_by=user) | Q(created_by__in=org_users)
            )
        else:
            accessible_templates = Template.objects.filter(created_by=user)
        return queryset.filter(link__widget__layer__template__in=accessible_templates)


class QRScanEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QRScanEvent.objects.select_related('link', 'matched_rule')
    serializer_class = QRScanEventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.has_full_access():
            return queryset
        if user.can_manage_own_resources():
            org_users = user.get_organization_users()
            accessible_templates = Template.objects.filter(
                Q(created_by=user) | Q(created_by__in=org_users)
            )
        else:
            accessible_templates = Template.objects.filter(created_by=user)
        return queryset.filter(link__widget__layer__template__in=accessible_templates)


def _extract_request_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def qr_action_redirect(request, slug):
    link = QRActionLink.objects.filter(slug=slug, is_active=True).first()
    if not link:
        return HttpResponseNotFound('QR link not found')

    resolved_url, matched_rule = link.resolve_destination()
    QRScanEvent.objects.create(
        link=link,
        matched_rule=matched_rule,
        campaign_id=link.campaign_id,
        resolved_url=resolved_url,
        request_ip=_extract_request_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        referrer=request.META.get('HTTP_REFERER'),
        query_params=dict(request.GET.items()),
        source_screen=request.GET.get('screen'),
    )
    return redirect(resolved_url)
