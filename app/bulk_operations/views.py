"""
Bulk operation views for Screens, Templates, Contents, Schedules, and Commands.

Provides secure, transactional bulk operations with proper permissions,
logging, rate limiting, and error handling.
"""
import logging
from typing import List, Tuple, Any
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .utils import (
    BulkOperationError,
    RateLimitExceeded,
    BulkOperationResponse,
    BulkOperationResult,
    execute_bulk_operation
)
from .serializers import (
    BulkOperationRequestSerializer,
    BulkUpdateRequestSerializer,
    BulkScreenActivateTemplateSerializer,
    BulkScreenSendCommandSerializer,
    BulkTemplateActivateSerializer,
    BulkTemplateActivateOnScreensSerializer,
    BulkContentDownloadSerializer,
    BulkContentRetrySerializer,
    BulkScheduleActivateSerializer,
    BulkScheduleExecuteSerializer,
    BulkCommandExecuteSerializer,
    BulkCommandRetrySerializer
)
from accounts.permissions import RolePermissions

logger = logging.getLogger(__name__)


# ============================================================================
# SCREEN BULK OPERATIONS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_screens_delete(request):
    """
    POST /api/screens/bulk/delete/
    Delete multiple screens.
    """
    serializer = BulkOperationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    user = request.user
    
    def delete_screen(screen_id: str) -> Tuple[bool, str, Any]:
        """Delete a single screen"""
        try:
            from signage.models import Screen
            screen = Screen.objects.get(id=screen_id)
            
            # Check permissions
            if not (user.has_full_access() or screen.owner == user):
                return (False, 'Permission denied', None)
            
            screen_name = screen.name
            screen.delete()
            return (True, f'Screen "{screen_name}" deleted successfully', None)
        except Screen.DoesNotExist:
            return (False, 'Screen not found', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=delete_screen,
        operation_name='bulk_delete',
        user_id=user.id,
        username=user.username,
        module='screens',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_screens_update(request):
    """
    POST /api/screens/bulk/update/
    Update multiple screens with the same data.
    """
    serializer = BulkUpdateRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    update_data = serializer.validated_data['update_data']
    user = request.user
    
    def update_screen(screen_id: str) -> Tuple[bool, str, Any]:
        """Update a single screen"""
        try:
            from signage.models import Screen
            screen = Screen.objects.get(id=screen_id)
            
            # Check permissions
            if not RolePermissions.can_edit_resource(user, screen):
                return (False, 'Permission denied', None)
            
            # Remove fields that shouldn't be updated
            restricted_fields = ['id', 'auth_token', 'secret_key', 'registration_date', 'created_at']
            filtered_data = {k: v for k, v in update_data.items() if k not in restricted_fields}
            
            # Update screen
            for field, value in filtered_data.items():
                if hasattr(screen, field):
                    setattr(screen, field, value)
            
            screen.save()
            return (True, f'Screen "{screen.name}" updated successfully', {'screen_id': str(screen.id)})
        except Screen.DoesNotExist:
            return (False, 'Screen not found', None)
        except ValidationError as e:
            return (False, f'Validation error: {str(e)}', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=update_screen,
        operation_name='bulk_update',
        user_id=user.id,
        username=user.username,
        module='screens',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_screens_activate_template(request):
    """
    POST /api/screens/bulk/activate_template/
    Activate a template on multiple screens.
    """
    serializer = BulkScreenActivateTemplateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    template_id = serializer.validated_data['template_id']
    sync_content = serializer.validated_data.get('sync_content', True)
    user = request.user
    
    # Check if template exists and user has permission
    try:
        from templates.models import Template
        template = Template.objects.get(id=template_id)
        if not RolePermissions.can_view_resource(user, template):
            return Response(
                {'error': 'Permission denied to access template'},
                status=status.HTTP_403_FORBIDDEN
            )
    except Template.DoesNotExist:
        return Response(
            {'error': 'Template not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    def activate_template(screen_id: str) -> Tuple[bool, str, Any]:
        """Activate template on a single screen"""
        try:
            from signage.models import Screen
            screen = Screen.objects.get(id=screen_id)
            
            # Check permissions
            if not RolePermissions.can_edit_resource(user, screen):
                return (False, 'Permission denied', None)
            
            # Activate template
            success = screen.activate_template(template, sync_content=sync_content)
            if success:
                return (True, f'Template activated on screen "{screen.name}"', {'screen_id': str(screen.id)})
            else:
                return (False, 'Failed to activate template. Template may not be active.', None)
        except Screen.DoesNotExist:
            return (False, 'Screen not found', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=activate_template,
        operation_name='bulk_activate_template',
        user_id=user.id,
        username=user.username,
        module='screens',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_screens_send_command(request):
    """
    POST /api/screens/bulk/send_command/
    Send a command to multiple screens.
    """
    if not request.user.can_execute_commands():
        return Response(
            {'error': 'Permission denied. You do not have permission to execute commands.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = BulkScreenSendCommandSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    command_type = serializer.validated_data['command_type']
    payload = serializer.validated_data.get('payload', {})
    priority = serializer.validated_data.get('priority', 0)
    user = request.user
    
    def send_command(screen_id: str) -> Tuple[bool, str, Any]:
        """Send command to a single screen"""
        try:
            from signage.models import Screen
            from commands.models import Command
            
            screen = Screen.objects.get(id=screen_id)
            
            # Check permissions
            if not RolePermissions.can_view_resource(user, screen):
                return (False, 'Permission denied', None)
            
            # Create command
            command = Command.queue_command(
                command_type=command_type,
                screen=screen,
                payload=payload,
                priority=priority,
                created_by=user
            )
            
            return (True, f'Command queued for screen "{screen.name}"', {'command_id': str(command.id)})
        except Screen.DoesNotExist:
            return (False, 'Screen not found', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=send_command,
        operation_name='bulk_send_command',
        user_id=user.id,
        username=user.username,
        module='screens',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


# ============================================================================
# TEMPLATE BULK OPERATIONS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_templates_delete(request):
    """
    POST /api/templates/bulk/delete/
    Delete multiple templates.
    """
    serializer = BulkOperationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    user = request.user
    
    def delete_template(template_id: str) -> Tuple[bool, str, Any]:
        """Delete a single template"""
        try:
            from templates.models import Template
            template = Template.objects.get(id=template_id)
            
            # Check permissions
            if not (user.has_full_access() or template.created_by == user):
                return (False, 'Permission denied', None)
            
            template_name = template.name
            template.delete()
            return (True, f'Template "{template_name}" deleted successfully', None)
        except Template.DoesNotExist:
            return (False, 'Template not found', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=delete_template,
        operation_name='bulk_delete',
        user_id=user.id,
        username=user.username,
        module='templates',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_templates_update(request):
    """
    POST /api/templates/bulk/update/
    Update multiple templates with the same data.
    """
    serializer = BulkUpdateRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    update_data = serializer.validated_data['update_data']
    user = request.user
    
    def update_template(template_id: str) -> Tuple[bool, str, Any]:
        """Update a single template"""
        try:
            from templates.models import Template
            template = Template.objects.get(id=template_id)
            
            # Check permissions
            if not RolePermissions.can_edit_resource(user, template):
                return (False, 'Permission denied', None)
            
            # Remove fields that shouldn't be updated
            restricted_fields = ['id', 'created_by', 'created_at']
            filtered_data = {k: v for k, v in update_data.items() if k not in restricted_fields}
            
            # Update template
            for field, value in filtered_data.items():
                if hasattr(template, field):
                    setattr(template, field, value)
            
            template.save()
            return (True, f'Template "{template.name}" updated successfully', {'template_id': str(template.id)})
        except Template.DoesNotExist:
            return (False, 'Template not found', None)
        except ValidationError as e:
            return (False, f'Validation error: {str(e)}', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=update_template,
        operation_name='bulk_update',
        user_id=user.id,
        username=user.username,
        module='templates',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_templates_activate(request):
    """
    POST /api/templates/bulk/activate/
    Activate or deactivate multiple templates.
    """
    serializer = BulkTemplateActivateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    item_ids = serializer.validated_data['item_ids']
    is_active = serializer.validated_data['is_active']
    user = request.user
    
    def activate_template(template_id: str) -> Tuple[bool, str, Any]:
        """Activate/deactivate a single template"""
        try:
            from templates.models import Template
            template = Template.objects.get(id=template_id)
            
            # Check permissions
            if not RolePermissions.can_edit_resource(user, template):
                return (False, 'Permission denied', None)
            
            template.is_active = is_active
            template.save(update_fields=['is_active'])
            
            status_text = 'activated' if is_active else 'deactivated'
            return (True, f'Template "{template.name}" {status_text} successfully', {'template_id': str(template.id)})
        except Template.DoesNotExist:
            return (False, 'Template not found', None)
        except Exception as e:
            return (False, str(e), None)
    
    response = execute_bulk_operation(
        item_ids=item_ids,
        operation_func=activate_template,
        operation_name='bulk_activate' if is_active else 'bulk_deactivate',
        user_id=user.id,
        username=user.username,
        module='templates',
        use_transaction=True,
        continue_on_error=True
    )
    
    return response.to_response()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_templates_activate_on_screens(request):
    """
    POST /api/templates/bulk/activate_on_screens/
    Activate multiple templates on multiple screens.
    """
    serializer = BulkTemplateActivateOnScreensSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    template_ids = serializer.validated_data['item_ids']
    screen_ids = serializer.validated_data['screen_ids']
    sync_content = serializer.validated_data.get('sync_content', True)
    user = request.user
    
    # Validate all screens exist and user has permission
    from signage.models import Screen
    screens = Screen.objects.filter(id__in=screen_ids)
    accessible_screens = []
    for screen in screens:
        if RolePermissions.can_view_resource(user, screen):
            accessible_screens.append(screen)
    
    if not accessible_screens:
        return Response(
            {'error': 'No accessible screens found'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Process each template-screen combination
    response = BulkOperationResponse()
    
    for template_id in template_ids:
        try:
            from templates.models import Template
            template = Template.objects.get(id=template_id)
            
            # Check template permissions
            if not RolePermissions.can_edit_resource(user, template):
                for screen_id in screen_ids:
                    response.add_result(BulkOperationResult(
                        item_id=str(template_id),
                        status='failure',
                        message=f'Permission denied for template'
                    ))
                continue
            
            # Activate on each screen
            for screen in accessible_screens:
                try:
                    if not RolePermissions.can_edit_resource(user, screen):
                        response.add_result(BulkOperationResult(
                            item_id=f"{template_id}:{screen.id}",
                            status='failure',
                            message='Permission denied for screen'
                        ))
                        continue
                    
                    success = template.activate_on_screen(screen, sync_content=sync_content)
                    if success:
                        response.add_result(BulkOperationResult(
                            item_id=f"{template_id}:{screen.id}",
                            status='success',
                            message=f'Template "{template.name}" activated on screen "{screen.name}"',
                            data={'template_id': str(template.id), 'screen_id': str(screen.id)}
                        ))
                    else:
                        response.add_result(BulkOperationResult(
                            item_id=f"{template_id}:{screen.id}",
                            status='failure',
                            message='Failed to activate template. Template may not be active.'
                        ))
                except Exception as e:
                    response.add_result(BulkOperationResult(
                        item_id=f"{template_id}:{screen.id}",
                        status='failure',
                        message=str(e)
                    ))
        except Template.DoesNotExist:
            for screen_id in screen_ids:
                response.add_result(BulkOperationResult(
                    item_id=str(template_id),
                    status='failure',
                    message='Template not found'
                ))
        except Exception as e:
            for screen_id in screen_ids:
                response.add_result(BulkOperationResult(
                    item_id=str(template_id),
                    status='failure',
                    message=str(e)
                ))
    
    # Log operation
    from .utils import log_bulk_operation
    log_bulk_operation(
        user_id=user.id,
        username=user.username,
        operation_type='bulk_activate_on_screens',
        module='templates',
        item_ids=template_ids,
        success_count=response.success_count,
        failure_count=response.failure_count
    )
    
    return response.to_response()
