from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotModified
from datetime import timedelta
import secrets
import uuid

from .models import Screen, PairingSession
from .serializers import (
    ScreenSerializer, HeartbeatSerializer, CommandSerializer,
    CommandPullSerializer, CommandResponseSerializer, ContentSyncSerializer,
    TemplateSerializer, PlayerTemplateSerializer,
    PairingSessionSerializer, PairingBindSerializer, PairingStatusSerializer
)
from .device_auth import authenticate_device_request
from commands.models import Command
from templates.models import Template, Content
from log.models import CommandExecutionLog, ScreenStatusLog, ContentDownloadLog
from core.audit import AuditLogger
from core.api_errors import error_response
from saas_platform.plan_policy import assert_can_create_screen
import logging

logger = logging.getLogger(__name__)


class ScreenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Screen model.
    Provides standard CRUD operations for screens.
    """
    queryset = Screen.objects.all()
    serializer_class = ScreenSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_developer() or user.is_manager():
            return queryset

        # Visitor: browse all screens read-only; writes blocked in create/update/destroy
        if user.is_visitor():
            return queryset

        queryset = queryset.filter(owner=user)
        
        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.is_visitor():
            raise PermissionDenied('Visitors cannot create screens.')
        assert_can_create_screen(request.user)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.is_visitor():
            raise PermissionDenied('Visitors cannot edit screens.')
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.is_visitor():
            raise PermissionDenied('Visitors cannot edit screens.')
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_visitor():
            raise PermissionDenied('Visitors cannot delete screens.')
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='revoke-token', permission_classes=[IsAuthenticated])
    def revoke_token(self, request, id=None):
        """
        POST /api/screens/{id}/revoke-token/

        Revoke the device token for this screen, forcing the TV back to pairing.
        Only the screen owner (or developer/manager) can do this.
        """
        if request.user.is_visitor():
            raise PermissionDenied('Visitors cannot revoke device tokens.')
        screen = self.get_object()
        screen.revoke_device_token()

        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=screen,
                description=f"Revoked device token for screen '{screen.name}'",
                changes={'action': 'revoke_device_token'},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'status': 'success',
            'message': f"Device token revoked for screen '{screen.name}'. The TV will return to pairing mode.",
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='regenerate-token', permission_classes=[IsAuthenticated])
    def regenerate_token(self, request, id=None):
        """
        POST /api/screens/{id}/regenerate-token/

        Issue a brand-new device token (invalidates the old one).
        Returns the raw token once — the caller must deliver it to the TV.
        """
        if request.user.is_visitor():
            raise PermissionDenied('Visitors cannot regenerate device tokens.')
        screen = self.get_object()
        raw_token = screen.issue_device_token()
        screen.last_paired_at = timezone.now()
        screen.save(update_fields=['last_paired_at'])

        return Response({
            'status': 'success',
            'device_token': raw_token,
            'screen_id': str(screen.id),
            'message': 'New device token issued. Deliver it to the TV securely.',
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def heartbeat(self, request, id=None):
        """
        POST /api/screens/{id}/heartbeat/
        Alternative endpoint for heartbeat (using screen ID)
        """
        try:
            screen = self.get_object()
        except Screen.DoesNotExist:
            return Response(
                {'error': 'Screen not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = HeartbeatSerializer(data=request.data)
        if serializer.is_valid():
            screen = serializer.validated_data['screen']
            
            # Get IP address from request
            ip_address = self._get_client_ip(request)
            
            # Update heartbeat
            screen.update_heartbeat(
                latency=serializer.validated_data.get('latency'),
                cpu_usage=serializer.validated_data.get('cpu_usage'),
                memory_usage=serializer.validated_data.get('memory_usage'),
                ip_address=ip_address
            )
            
            # Update optional device information
            update_fields = []
            if 'app_version' in serializer.validated_data:
                screen.app_version = serializer.validated_data['app_version']
                update_fields.append('app_version')
            if 'os_version' in serializer.validated_data:
                screen.os_version = serializer.validated_data['os_version']
                update_fields.append('os_version')
            if 'device_model' in serializer.validated_data:
                screen.device_model = serializer.validated_data['device_model']
                update_fields.append('device_model')
            if 'screen_width' in serializer.validated_data:
                screen.screen_width = serializer.validated_data['screen_width']
                update_fields.append('screen_width')
            if 'screen_height' in serializer.validated_data:
                screen.screen_height = serializer.validated_data['screen_height']
                update_fields.append('screen_height')
            if 'brightness' in serializer.validated_data:
                screen.brightness = serializer.validated_data['brightness']
                update_fields.append('brightness')
            if 'orientation' in serializer.validated_data:
                screen.orientation = serializer.validated_data['orientation']
                update_fields.append('orientation')
            
            if update_fields:
                screen.save(update_fields=update_fields)
            
            return Response({
                'status': 'success',
                'message': 'Heartbeat received',
                'screen_id': str(screen.id),
                'is_online': screen.is_online,
                'last_heartbeat_at': screen.last_heartbeat_at
            }, status=status.HTTP_200_OK)
        
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Heartbeat validation failed')
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def heartbeat_endpoint(request):
    """
    POST /iot/screens/heartbeat/

    Requires X-Device-Token header + screen_id in body.
    """
    from django.http import JsonResponse

    screen, err = authenticate_device_request(request)
    if err:
        return err

    try:
        ip_address = _get_client_ip(request)

        data_source = request.data if request.data and isinstance(request.data, dict) else {}

        screen.update_heartbeat(
            latency=data_source.get('latency'),
            cpu_usage=data_source.get('cpu_usage'),
            memory_usage=data_source.get('memory_usage'),
            ip_address=ip_address,
        )
        screen.refresh_from_db()

        update_fields = []
        for field in ('app_version', 'os_version', 'device_model',
                      'screen_width', 'screen_height', 'brightness', 'orientation'):
            val = data_source.get(field)
            if val is not None:
                setattr(screen, field, val)
                update_fields.append(field)
        if update_fields:
            screen.save(update_fields=update_fields)

        response = JsonResponse({
            'status': 'success',
            'message': 'Heartbeat received',
            'screen_id': str(screen.id),
            'is_online': screen.is_online,
            'last_heartbeat_at': screen.last_heartbeat_at.isoformat() if screen.last_heartbeat_at else None,
        }, status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token'
        return response

    except Exception as e:
        logger.error(f"Heartbeat error: {e}", exc_info=True)
        response = JsonResponse({'error': 'Internal server error', 'message': str(e)}, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])  # Screen-based authentication via auth_token + secret_key
def command_pull_endpoint(request):
    """
    GET /api/screens/command-pull/
    Endpoint for Screens to fetch pending commands.
    Returns pending commands ordered by priority and creation time.
    """
    serializer = CommandPullSerializer(data=request.query_params)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Command pull validation failed')
    
    screen = serializer.validated_data['screen']
    limit = serializer.validated_data.get('limit', 10)
    
    # Get pending commands for this screen
    commands = Command.objects.filter(
        screen=screen,
        status='pending'
    ).exclude(
        # Exclude expired commands
        expire_at__lt=timezone.now()
    ).order_by(
        '-priority',
        'created_at'
    )[:limit]
    
    # Mark commands as being processed
    now = timezone.now()
    for command in commands:
        command.last_attempt_at = now
        command.attempt_count += 1
        command.save(update_fields=['last_attempt_at', 'attempt_count'])
        
        # Create execution log entry
        CommandExecutionLog.objects.create(
            command=command,
            screen=screen,
            status='running',
            started_at=now
        )
    
    # Update screen's last_command_sent_at
    if commands.exists():
        screen.last_command_sent_at = now
        screen.is_busy = True
        screen.save(update_fields=['last_command_sent_at', 'is_busy'])
    
    command_serializer = CommandSerializer(commands, many=True)
    
    return Response({
        'status': 'success',
        'commands': command_serializer.data,
        'count': len(command_serializer.data)
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def iot_command_pull_endpoint(request):
    """
    GET /iot/commands/pending/?screen_id=...

    Requires X-Device-Token header.
    """
    from django.http import JsonResponse

    screen, err = authenticate_device_request(request)
    if err:
        return err

    try:
        limit = min(int(request.GET.get('limit', '10')), 50)
    except (ValueError, TypeError):
        limit = 10

    try:
        commands = Command.objects.filter(
            screen=screen, status='pending',
        ).exclude(
            expire_at__lt=timezone.now(),
        ).order_by('-priority', 'created_at')[:limit]

        now = timezone.now()
        command_list = []
        for command in commands:
            command.status = 'executing'
            command.executed_at = now
            command.last_attempt_at = now
            command.attempt_count += 1
            command.save(update_fields=['status', 'executed_at', 'last_attempt_at', 'attempt_count'])
            CommandExecutionLog.objects.create(command=command, screen=screen, status='running', started_at=now)
            command_list.append({
                'id': str(command.id),
                'type': command.type,
                'payload': command.payload or {},
                'priority': command.priority,
                'name': command.name or '',
                'created_at': command.created_at.isoformat() if command.created_at else None,
            })

        if commands.exists():
            screen.last_command_sent_at = now
            screen.is_busy = True
            screen.save(update_fields=['last_command_sent_at', 'is_busy'])

        response = JsonResponse({'status': 'success', 'commands': command_list, 'count': len(command_list)}, status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token'
        return response

    except Exception as e:
        logger.error(f"Command pull error: {e}", exc_info=True)
        resp = JsonResponse({'error': 'Internal server error', 'message': str(e)}, status=500)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp


@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def iot_command_response_endpoint(request):
    """
    POST /iot/commands/status/

    Requires X-Device-Token header + screen_id & command_id in body.
    """
    from django.http import JsonResponse

    screen, err = authenticate_device_request(request)
    if err:
        return err

    data_source = request.data if request.data and isinstance(request.data, dict) else {}
    command_id = data_source.get('command_id')
    if not command_id:
        resp = JsonResponse({'error': 'command_id is required'}, status=400)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    try:
        command = Command.objects.filter(id=command_id, screen=screen).first()
        if not command:
            resp = JsonResponse({'error': 'Command not found'}, status=404)
            resp['Access-Control-Allow-Origin'] = '*'
            return resp

        response_status = data_source.get('status', 'done')
        if response_status not in ('done', 'failed'):
            response_status = 'done'
        error_message = data_source.get('error_message', '')
        response_payload = data_source.get('response_payload', {})

        now = timezone.now()
        if response_status == 'done':
            command.mark_done()
        else:
            command.mark_failed(error_message or 'Command execution failed')

        screen.last_command_received_at = now
        screen.is_busy = False
        screen.save(update_fields=['last_command_received_at', 'is_busy'])

        exec_log = CommandExecutionLog.objects.filter(
            command=command, screen=screen, status='running',
        ).order_by('-started_at').first()
        if exec_log:
            exec_log.status = response_status
            exec_log.finished_at = now
            exec_log.response_payload = response_payload
            if error_message:
                exec_log.error_message = error_message
            exec_log.save(update_fields=['status', 'finished_at', 'response_payload', 'error_message'])
        else:
            CommandExecutionLog.objects.create(
                command=command, screen=screen, status=response_status,
                started_at=command.executed_at or now, finished_at=now,
                response_payload=response_payload, error_message=error_message,
            )

        response = JsonResponse({
            'status': 'success', 'message': 'Command response recorded',
            'command_id': str(command.id), 'command_status': command.status,
        }, status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token'
        return response

    except Exception as e:
        logger.error(f"Command response error: {e}", exc_info=True)
        resp = JsonResponse({'error': 'Internal server error', 'message': str(e)}, status=500)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])  # Screen-based authentication via auth_token + secret_key
def command_response_endpoint(request):
    """
    POST /api/screens/command-response/
    Endpoint for Screens to send command execution responses.
    Updates command status and creates execution log entry.
    """
    serializer = CommandResponseSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Command response validation failed')
    
    screen = serializer.validated_data['screen']
    command = serializer.validated_data['command']
    response_status = serializer.validated_data['status']
    response_payload = serializer.validated_data.get('response_payload', {})
    error_message = serializer.validated_data.get('error_message', '')
    
    # Update command status
    if response_status == 'done':
        command.mark_done()
    else:
        command.mark_failed()
    
    # Update screen's last_command_received_at and is_busy
    screen.last_command_received_at = timezone.now()
    screen.is_busy = False
    screen.save(update_fields=['last_command_received_at', 'is_busy'])
    
    # Update or create execution log entry
    exec_log = CommandExecutionLog.objects.filter(
        command=command,
        screen=screen,
        status='running'
    ).order_by('-started_at').first()
    
    if exec_log:
        exec_log.status = response_status
        exec_log.finished_at = timezone.now()
        exec_log.response_payload = response_payload
        if error_message:
            exec_log.error_message = error_message
        exec_log.save(update_fields=['status', 'finished_at', 'response_payload', 'error_message'])
    else:
        # Create new log entry if none exists
        CommandExecutionLog.objects.create(
            command=command,
            screen=screen,
            status=response_status,
            started_at=command.last_attempt_at or timezone.now(),
            finished_at=timezone.now(),
            response_payload=response_payload,
            error_message=error_message
        )
    
    return Response({
        'status': 'success',
        'message': 'Command response recorded',
        'command_id': str(command.id),
        'command_status': command.status
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])  # Screen-based authentication via auth_token + secret_key
def health_check_endpoint(request):
    """
    GET /api/screens/health-check/
    Endpoint for Screens to perform health check.
    Returns comprehensive health status information.
    """
    auth_token = request.query_params.get('auth_token')
    secret_key = request.query_params.get('secret_key')
    
    if not auth_token or not secret_key:
        return Response(
            {'error': 'auth_token and secret_key are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        screen = Screen.objects.get(auth_token=auth_token)
    except Screen.DoesNotExist:
        return Response(
            {'error': 'Invalid authentication token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not screen.authenticate(auth_token, secret_key):
        return Response(
            {'error': 'Invalid secret key'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Perform health check
    health = screen.health_check()
    
    return Response({
        'status': 'success',
        'screen_id': str(screen.id),
        'screen_name': screen.name,
        'health': health
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])  # Screen-based authentication via auth_token + secret_key
def content_sync_endpoint(request):
    """
    POST /api/screens/content-sync/
    Endpoint for Screens to report content download status or request content sync.
    
    Supports two sync types:
    1. 'request': Screen requests content sync for specific content IDs or all active template content
    2. 'status': Screen reports download status for content items
    """
    serializer = ContentSyncSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Content sync validation failed')
    
    screen = serializer.validated_data['screen']
    sync_type = serializer.validated_data['sync_type']
    
    if sync_type == 'request':
        # Screen is requesting content sync
        content_ids = serializer.validated_data.get('content_ids', [])
        
        if not screen.active_template:
            return Response({
                'status': 'error',
                'message': 'No active template assigned to this screen'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get content to sync
        if content_ids:
            # Sync specific content items
            contents = Content.objects.filter(
                id__in=content_ids,
                widget__layer__template=screen.active_template,
                is_active=True
            )
        else:
            # Sync all active template content
            contents = screen.active_template.get_all_contents().filter(is_active=True)
        
        # Prepare content list for response
        content_list = []
        for content in contents:
            content_list.append({
                'id': str(content.id),
                'name': content.name,
                'type': content.type,
                'file_url': content.file_url,
                'content_json': content.content_json,
                'duration': content.duration,
                'order': content.order,
                'download_status': content.download_status
            })
        
        return Response({
            'status': 'success',
            'message': 'Content sync request processed',
            'template_id': str(screen.active_template.id),
            'template_name': screen.active_template.name,
            'contents': content_list,
            'count': len(content_list)
        }, status=status.HTTP_200_OK)
    
    elif sync_type == 'status':
        # Screen is reporting download status
        download_status = serializer.validated_data.get('download_status', [])
        
        synced_count = 0
        failed_count = 0
        
        for status_item in download_status:
            content_id = status_item.get('content_id')
            item_status = status_item.get('status')
            file_size = status_item.get('file_size')
            error_message = status_item.get('error_message', '')
            
            try:
                content = Content.objects.get(id=content_id)
            except Content.DoesNotExist:
                continue
            
            # Update content download status
            if item_status == 'success':
                content.mark_downloaded()
                synced_count += 1
            elif item_status == 'failed':
                content.mark_failed()
                failed_count += 1
            else:
                content.update_status('pending')
            
            # Create or update download log
            download_log = ContentDownloadLog.objects.filter(
                content=content,
                screen=screen
            ).order_by('-created_at').first()
            
            if download_log:
                download_log.status = item_status
                if file_size:
                    download_log.file_size = file_size
                if error_message:
                    download_log.error_message = error_message
                if item_status == 'success':
                    download_log.downloaded_at = timezone.now()
                download_log.save()
            else:
                ContentDownloadLog.objects.create(
                    content=content,
                    screen=screen,
                    status=item_status,
                    file_size=file_size,
                    error_message=error_message,
                    downloaded_at=timezone.now() if item_status == 'success' else None
                )
        
        return Response({
            'status': 'success',
            'message': 'Content download status updated',
            'synced_count': synced_count,
            'failed_count': failed_count,
            'total_reported': len(download_status)
        }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'message': 'Invalid sync_type'
    }, status=status.HTTP_400_BAD_REQUEST)


def _player_template_etag(screen):
    """
    Stable ETag for player template JSON (or empty assignment).
    Used with If-None-Match so TVs can poll without re-downloading unchanged layouts.
    """
    if not screen.active_template_id:
        return f'"screen-{screen.id}-no-template"'
    t = screen.active_template
    ts = t.updated_at.isoformat() if getattr(t, 'updated_at', None) else ''
    return f'"{t.id}-{ts}-v{t.version}"'


def _get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
@api_view(['GET', 'OPTIONS'])
@authentication_classes([])
@permission_classes([AllowAny])
def player_template_endpoint(request):
    """
    GET /iot/player/template/?screen_id=...

    Requires X-Device-Token header.
    """
    from django.http import JsonResponse

    screen, err = authenticate_device_request(request)
    if err:
        return err

    try:
        # Re-fetch with prefetch for efficient serialization
        screen = Screen.objects.select_related(
            'active_template',
        ).prefetch_related(
            'active_template__layers__widgets__contents',
        ).get(id=screen.id)

        etag = _player_template_etag(screen)
        inm = (request.META.get('HTTP_IF_NONE_MATCH') or '').strip()
        if inm:
            # Exact match on our quoted ETag (ignore weak validators for simplicity)
            tokens = [x.strip() for x in inm.split(',')]
            if etag in tokens:
                resp = HttpResponseNotModified()
                resp['ETag'] = etag
                resp['Access-Control-Allow-Origin'] = '*'
                resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                resp['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token, If-None-Match'
                resp['Access-Control-Expose-Headers'] = 'ETag, Date'
                return resp

        if not screen.active_template:
            response = JsonResponse({'status': 'no_template', 'template': None}, status=200)
            response['ETag'] = etag
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token, If-None-Match'
            response['Access-Control-Expose-Headers'] = 'ETag, Date'
            return response

        template = screen.active_template
        if not template.width or not template.height or template.width <= 0 or template.height <= 0:
            response = JsonResponse({'status': 'error', 'error': 'Template has invalid dimensions', 'template': None}, status=200)
            response['ETag'] = etag
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Expose-Headers'] = 'ETag, Date'
            return response

        serializer = PlayerTemplateSerializer(template, context={'request': request, 'screen': screen})

        response = JsonResponse({
            'status': 'success',
            'screen_id': str(screen.id),
            'template': serializer.data,
        }, status=200)
        response['ETag'] = etag
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token, If-None-Match'
        response['Access-Control-Expose-Headers'] = 'ETag, Date'
        return response

    except Exception as e:
        logger.error(f"Template endpoint error: {e}", exc_info=True)
        resp = JsonResponse({'error': 'Internal server error', 'message': str(e)}, status=500)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp


# Pairing endpoints
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_pairing_session(request):
    """
    POST /api/pairing/generate/
    
    Generate a new pairing session for TV/Web Player.
    Returns 6-digit code and pairing token for QR code.
    """
    # Generate 6-digit code (ensure uniqueness)
    max_attempts = 10
    for _ in range(max_attempts):
        pairing_code = str(secrets.randbelow(900000) + 100000)  # 100000-999999
        if not PairingSession.objects.filter(
            pairing_code=pairing_code,
            status='pending',
            expires_at__gt=timezone.now()
        ).exists():
            break
    else:
        return Response(
            {'error': 'Failed to generate unique pairing code. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Generate secure pairing token
    pairing_token = secrets.token_urlsafe(32)
    
    # Create pairing session (expires in 5 minutes)
    expires_at = timezone.now() + timedelta(minutes=5)
    session = PairingSession.objects.create(
        pairing_code=pairing_code,
        pairing_token=pairing_token,
        expires_at=expires_at,
        status='pending'
    )
    
    serializer = PairingSessionSerializer(session)
    return Response({
        'status': 'success',
        'pairing_session': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_pairing_status(request):
    """
    GET /api/pairing/status/?pairing_token=XXX

    TV polls this endpoint.  When the session is paired and the activation
    payload has **not** been delivered yet, we issue a one-time device token,
    return it, and mark ``activation_delivered_at`` so subsequent polls will
    NOT receive the raw token again.
    """
    serializer = PairingStatusSerializer(data=request.query_params)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Pairing status validation failed')

    session = serializer.validated_data['pairing_token']

    if session.status == 'paired' and session.screen:
        # One-time activation delivery
        if session.activation_delivered_at is None:
            raw_device_token = session.screen.issue_device_token()
            session.activation_delivered_at = timezone.now()
            session.save(update_fields=['activation_delivered_at'])
            return Response({
                'status': 'paired',
                'screen_id': str(session.screen.id),
                'device_token': raw_device_token,
                'screen_name': session.screen.name,
                'paired_at': session.paired_at,
            }, status=status.HTTP_200_OK)

        # Already delivered — confirm paired but do NOT re-send the token
        return Response({
            'status': 'paired',
            'screen_id': str(session.screen.id),
            'screen_name': session.screen.name,
            'paired_at': session.paired_at,
            'message': 'Activation already delivered',
        }, status=status.HTTP_200_OK)

    if session.status == 'pending':
        session_serializer = PairingSessionSerializer(session)
        return Response({
            'status': 'pending',
            'pairing_session': session_serializer.data,
        }, status=status.HTTP_200_OK)

    return Response({
        'status': session.status,
        'message': 'Pairing session has expired or is invalid',
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bind_pairing_session(request):
    """
    POST /api/pairing/bind/
    
    Bind a pairing session to the authenticated user.
    Creates a new Screen and links it to the user.
    
    Uses transaction.atomic() to ensure data integrity:
    - Screen creation and pairing session update are atomic
    - Prevents race conditions in PostgreSQL's strict transaction model
    """
    from django.db import transaction
    
    serializer = PairingBindSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Pairing bind validation failed')
    
    session = serializer.validated_data['session']
    screen_name = serializer.validated_data.get('screen_name', '')
    
    # Check if session is still valid
    if not session.is_valid():
        return Response({
            'error': 'Pairing session has expired or is invalid'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if already paired (do this before transaction to avoid unnecessary locking)
    if session.status != 'pending':
        return Response({
            'error': 'This pairing code/token has already been used'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Use atomic transaction to ensure screen creation and pairing are atomic
    # PostgreSQL's strict transaction handling will prevent race conditions
    try:
        with transaction.atomic():
            # Lock the session row to prevent concurrent pairing attempts
            session = PairingSession.objects.select_for_update().get(
                id=session.id,
                status='pending'
            )
            
            # Verify it's still valid (double-check after lock)
            if not session.is_valid():
                return Response({
                    'error': 'Pairing session has expired or is invalid'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                assert_can_create_screen(request.user)
            except DRFValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

            # Create new screen
            screen = Screen.objects.create(
                name=screen_name or f"Screen {session.pairing_code}",
                device_id=f"device_{uuid.uuid4().hex[:16]}",
                owner=request.user,
                is_online=False,
                last_paired_at=timezone.now(),
            )
            
            # Mark session as paired (this updates status atomically)
            session.mark_paired(screen, request.user)
            
            # Log audit event
            try:
                AuditLogger.log_action(
                    action_type='create',
                    user=request.user,
                    resource=screen,
                    description=f"Paired screen '{screen.name}' (pairing code: {session.pairing_code})",
                    changes={'before': None, 'after': {'name': screen.name, 'device_id': screen.device_id, 'pairing_code': session.pairing_code}},
                    request=request,
                )
            except Exception as audit_error:
                logger.error(f"Failed to log screen pairing audit: {audit_error}", exc_info=True)
            
    except PairingSession.DoesNotExist:
        return Response({
            'error': 'Pairing session not found or already used'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Return screen info
    screen_serializer = ScreenSerializer(screen)
    return Response({
        'status': 'success',
        'message': 'Screen paired successfully',
        'screen': screen_serializer.data,
        'pairing_code': session.pairing_code
    }, status=status.HTTP_200_OK)