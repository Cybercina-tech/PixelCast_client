from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone
import requests
import logging

from .models import Command
from .serializers import (
    CommandSerializer, CommandCreateSerializer,
    CommandStatusSerializer, CommandExecutionSerializer
)
from accounts.permissions import RolePermissions
from core.api_errors import error_response

logger = logging.getLogger(__name__)


class CommandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Command model.
    Provides CRUD operations with role-based permissions.
    """
    queryset = Command.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CommandCreateSerializer
        return CommandSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_developer():
            return queryset

        if user.can_execute_commands() or user.can_manage_own_resources():
            from signage.models import Screen
            if user.is_manager():
                accessible_screens = Screen.objects.all()
            elif user.organization_name:
                accessible_screens = Screen.objects.filter(
                    Q(owner__organization_name=user.organization_name) |
                    Q(owner=user)
                )
            else:
                accessible_screens = Screen.objects.filter(owner=user)
            
            return queryset.filter(
                Q(created_by=user) | Q(screen__in=accessible_screens)
            )

        # Visitor: read-only — same breadth as Manager for listing; writes blocked in perform_*
        if user.is_visitor():
            from signage.models import Screen
            accessible_screens = Screen.objects.all()
            return queryset.filter(
                Q(created_by=user) | Q(screen__in=accessible_screens)
            )
        
        # Employee / fallback: commands they created
        return queryset.filter(created_by=user)
    
    def perform_create(self, serializer):
        """Check permissions before creating command"""
        user = self.request.user

        if not user.can_execute_commands():
            raise PermissionDenied("You do not have permission to create commands.")

        screen_id = serializer.validated_data.get('screen_id')
        if screen_id:
            from signage.models import Screen
            try:
                screen = Screen.objects.get(id=screen_id)
            except Screen.DoesNotExist:
                raise PermissionDenied("Screen not found.")
            if not RolePermissions.can_view_resource(user, screen):
                raise PermissionDenied("You do not have permission to create commands for this screen.")

        serializer.save()
    
    def perform_update(self, serializer):
        """Check permissions before update"""
        command = self.get_object()
        user = self.request.user
        
        if not (
            user.is_developer()
            or user.is_manager()
            or (user.is_employee() and command.created_by_id == user.id)
        ):
            raise PermissionDenied("You do not have permission to update commands.")
        
        # Don't allow updating executing or done commands
        if command.status in ['executing', 'done']:
            raise PermissionDenied("Cannot update commands that are executing or completed.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Check permissions before delete"""
        user = self.request.user
        
        if not (
            user.is_developer()
            or user.is_manager()
            or (user.is_employee() and instance.created_by_id == user.id)
        ):
            raise PermissionDenied("You do not have permission to delete commands.")
        
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def execute(self, request, id=None):
        """
        POST /api/commands/{id}/execute/
        Execute command on a screen.
        """
        command = self.get_object()
        serializer = CommandExecutionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST, default_message='Command execution validation failed')
        
        # Check permissions
        user = request.user
        if not user.can_execute_commands():
            raise PermissionDenied("You do not have permission to execute commands.")
        
        # Check if user can access the screen
        screen = command.screen
        screen_id = serializer.validated_data.get('screen_id')
        if screen_id:
            from signage.models import Screen
            try:
                screen = Screen.objects.get(id=screen_id)
            except Screen.DoesNotExist:
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if not RolePermissions.can_view_resource(user, screen):
            raise PermissionDenied("You do not have permission to access this screen.")
        
        # Execute command
        try:
            success = command.execute(screen)
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Command "{command.name or command.get_type_display()}" executed successfully',
                    'command_id': str(command.id),
                    'command_status': command.status
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Command execution failed',
                    'command_id': str(command.id),
                    'command_status': command.status,
                    'error_message': command.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        GET /api/commands/status/
        Get status of commands by id or screen.
        """
        command_id = request.query_params.get('id')
        screen_id = request.query_params.get('screen_id')
        
        if command_id:
            # Get specific command status
            try:
                command = self.get_queryset().get(id=command_id)
                status_data = command.get_status()
                serializer = CommandStatusSerializer(status_data)
                return Response({
                    'status': 'success',
                    'command': serializer.data
                }, status=status.HTTP_200_OK)
            except Command.DoesNotExist:
                return Response(
                    {'error': 'Command not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif screen_id:
            # Get all commands for a screen
            try:
                from signage.models import Screen
                screen = Screen.objects.get(id=screen_id)
                
                # Check permissions
                if not RolePermissions.can_view_resource(request.user, screen):
                    raise PermissionDenied("You do not have permission to view commands for this screen.")
                
                commands = self.get_queryset().filter(screen=screen)
                status_list = [cmd.get_status() for cmd in commands]
                serializer = CommandStatusSerializer(status_list, many=True)
                
                return Response({
                    'status': 'success',
                    'screen_id': str(screen.id),
                    'screen_name': screen.name,
                    'commands': serializer.data,
                    'count': len(serializer.data)
                }, status=status.HTTP_200_OK)
            except Screen.DoesNotExist:
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        else:
            # Get all commands user can access
            commands = self.get_queryset()
            status_list = [cmd.get_status() for cmd in commands]
            serializer = CommandStatusSerializer(status_list, many=True)
            
            return Response({
                'status': 'success',
                'commands': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        GET /api/commands/pending/
        Get pending commands.
        """
        screen_id = request.query_params.get('screen_id')
        limit = request.query_params.get('limit', 10)
        
        try:
            limit = int(limit)
            if limit < 1:
                limit = 10
        except (ValueError, TypeError):
            limit = 10
        
        try:
            if screen_id:
                from signage.models import Screen
                try:
                    screen = Screen.objects.get(id=screen_id)
                    if not RolePermissions.can_view_resource(request.user, screen):
                        return Response(
                            {'error': 'You do not have permission to view commands for this screen.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    commands = Command.get_pending_commands(screen=screen, limit=limit)
                except Screen.DoesNotExist:
                    return Response(
                        {'error': 'Screen not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Exception as e:
                    logger.error(f"Error fetching pending commands for screen {screen_id}: {str(e)}")
                    return Response(
                        {'error': 'An error occurred while fetching commands'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Get all pending commands first
                all_pending = Command.get_pending_commands(limit=limit)
                
                # Get user's accessible queryset
                user_queryset = self.get_queryset()
                
                # Filter pending commands by user permissions
                pending_ids = list(all_pending.values_list('id', flat=True))
                
                if pending_ids:
                    commands = user_queryset.filter(id__in=pending_ids)
                else:
                    # Return empty queryset if no pending commands
                    commands = user_queryset.none()
            
            serializer = self.get_serializer(commands, many=True)
            return Response({
                'status': 'success',
                'commands': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
            
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Error in pending commands endpoint: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred while fetching pending commands'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, id=None):
        """
        POST /api/commands/{id}/retry/
        Retry a failed command.
        """
        command = self.get_object()
        
        # Check permissions
        if not request.user.can_execute_commands():
            raise PermissionDenied("You do not have permission to retry commands.")
        
        # Check if command can be retried
        if not command.can_retry():
            return Response({
                'status': 'error',
                'message': 'Command cannot be retried. It may be completed, expired, or exceeded retry limit.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset status and retry
        command.reset_status()
        success = command.execute()
        
        if success:
            return Response({
                'status': 'success',
                'message': 'Command retried successfully',
                'command_id': str(command.id),
                'command_status': command.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'Command retry failed',
                'command_id': str(command.id),
                'command_status': command.status,
                'error_message': command.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


def send_command_via_http(screen, signed_payload):
    """
    Send command to screen via HTTP POST (fallback when WebSocket unavailable).
    
    This function attempts to send command to screen's HTTP endpoint.
    In production, screens should expose an endpoint to receive commands.
    
    Args:
        screen: Screen instance
        signed_payload: Signed command payload dict
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    # In production, screens should expose an endpoint like:
    # http://screen-ip:port/api/command-receive/
    # For now, this is a placeholder that returns False
    # Screens should implement their own HTTP endpoint to receive commands
    
    # TODO: Implement actual HTTP POST to screen endpoint
    # Example:
    # try:
    #     screen_endpoint = f"http://{screen.last_ip}/api/command-receive/"
    #     response = requests.post(
    #         screen_endpoint,
    #         json=signed_payload,
    #         headers={'Authorization': f'Bearer {screen.auth_token}'},
    #         timeout=5
    #     )
    #     return response.status_code == 200
    # except Exception as e:
    #     logger.error(f"HTTP command delivery failed: {str(e)}")
    #     return False
    
    logger.warning(f"HTTP fallback not fully implemented for screen {screen.id}")
    return False


def _get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AllowAny])
def command_receive_endpoint(request):
    """
    POST /api/commands/screens/command-receive/
    HTTP fallback endpoint for screens to receive commands.
    
    Used when WebSocket is unavailable. Requires signed payload with
    authentication and security validation.
    """
    from signage.models import Screen
    from commands.security import ScreenSecurity, SecurityError
    from commands.models import Command
    from log.models import CommandExecutionLog
    
    # Extract authentication from headers or payload
    auth_token = request.headers.get('X-Auth-Token') or request.data.get('auth_token')
    secret_key = request.headers.get('X-Secret-Key') or request.data.get('secret_key')
    
    if not auth_token or not secret_key:
        return Response(
            {'error': 'Authentication required (auth_token and secret_key)'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Authenticate screen
    try:
        screen = Screen.objects.get(auth_token=auth_token)
        if not screen.authenticate(auth_token, secret_key):
            logger.warning(f"HTTP command receive: Invalid credentials for screen {screen.id}")
            return Response(
                {'error': 'Invalid authentication credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Screen.DoesNotExist:
        logger.warning(f"HTTP command receive: Screen not found for auth_token")
        return Response(
            {'error': 'Screen not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate IP consistency
    client_ip = _get_client_ip(request)
    if screen.last_ip and client_ip != screen.last_ip:
        logger.warning(f"HTTP command receive: IP mismatch for screen {screen.id}. Expected: {screen.last_ip}, Got: {client_ip}")
        # Log but don't reject (IPs can change with NAT)
    
    # Extract and validate signed payload
    payload = request.data.get('payload', {})
    timestamp = request.data.get('timestamp')
    nonce = request.data.get('nonce')
    signature = request.data.get('signature')
    
    if not all([payload, timestamp, nonce, signature]):
        return Response(
            {'error': 'Missing required fields: payload, timestamp, nonce, signature'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate security
    try:
        ScreenSecurity.validate_message(
            secret_key=screen.secret_key,
            screen_id=str(screen.id),
            payload=payload,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature
        )
    except SecurityError as e:
        logger.error(f"HTTP command receive: Security validation failed for screen {screen.id}: {str(e)}")
        return Response(
            {'error': f'Security validation failed: {str(e)}'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Extract command information
    command_id = payload.get('command_id')
    command_type = payload.get('command_type')
    command_data = payload.get('payload', {})
    
    if not command_id:
        return Response(
            {'error': 'command_id is required in payload'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get command
    try:
        command = Command.objects.get(id=command_id, screen=screen)
    except Command.DoesNotExist:
        return Response(
            {'error': 'Command not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Create execution log
    CommandExecutionLog.objects.create(
        command=command,
        screen=screen,
        status='running',
        started_at=timezone.now()
    )
    
    # Update command status
    command.status = 'executing'
    command.executed_at = timezone.now()
    command.save(update_fields=['status', 'executed_at'])
    
    # Update screen
    screen.last_command_received_at = timezone.now()
    screen.last_ip = client_ip
    screen.save(update_fields=['last_command_received_at', 'last_ip'])
    
    logger.info(f"Command {command_id} received by screen {screen.id} via HTTP")
    
    return Response({
        'status': 'success',
        'message': 'Command received',
        'command_id': command_id,
        'command_type': command_type
    }, status=status.HTTP_200_OK)
