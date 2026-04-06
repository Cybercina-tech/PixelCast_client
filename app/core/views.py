"""
Views for backup management and audit log access.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from core.models import AuditLog, SystemBackup, Notification, NotificationPreference, TVBrand
from core.backup import backup_manager
from core.serializers import (
    AuditLogSerializer,
    SystemBackupSerializer,
    NotificationSerializer,
    NotificationPreferenceSerializer,
    TVBrandWithModelsSerializer,
)
from core.audit import AuditLogger
import logging

logger = logging.getLogger(__name__)


class RoleBasedPermission(BasePermission):
    """DRF permission class for role-based access control."""
    
    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not self.required_roles:
            return True
        
        user_role = getattr(request.user, 'role', None)
        if user_role in self.required_roles:
            return True
        if 'Developer' in self.required_roles and getattr(request.user, 'is_superuser', False):
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        # For object-level permissions, check user role
        if not request.user.is_authenticated:
            return False
        
        if not self.required_roles:
            return True
        
        user_role = getattr(request.user, 'role', None)
        if user_role in self.required_roles:
            return True
        if 'Developer' in self.required_roles and getattr(request.user, 'is_superuser', False):
            return True
        return False


@extend_schema_view(
    list=extend_schema(
        summary='List audit logs',
        description='Retrieve a paginated list of audit logs. Filterable by action type, resource type, severity, success status, date range, and search query.',
        tags=['Core Infrastructure'],
        parameters=[
            OpenApiParameter(
                name='action_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by action type (create, update, delete, login, etc.)',
                required=False,
            ),
            OpenApiParameter(
                name='resource_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by resource type (Screen, Template, Content, etc.)',
                required=False,
            ),
            OpenApiParameter(
                name='severity',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by severity (low, medium, high, critical)',
                required=False,
                enum=['low', 'medium', 'high', 'critical'],
            ),
            OpenApiParameter(
                name='success',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by success status',
                required=False,
            ),
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter logs from this date (YYYY-MM-DD)',
                required=False,
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter logs until this date (YYYY-MM-DD)',
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in description, resource name, or username',
                required=False,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary='Retrieve audit log',
        description='Retrieve detailed information about a specific audit log entry.',
        tags=['Core Infrastructure'],
    ),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.

    Permissions:
    - Viewers: Can view their own logs
    - Operators: Can view logs for assigned resources
    - Managers/Admins: Can view all logs
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AuditLog.objects.all()

    def get_queryset(self):
        """Filter audit logs based on user permissions."""
        user = self.request.user
        queryset = AuditLog.objects.filter(is_archived=False)

        if user.is_developer():
            include_archived = self.request.query_params.get('include_archived')
            if include_archived and include_archived.lower() == 'true':
                queryset = AuditLog.objects.all()
        else:
            queryset = queryset.filter(user=user)

        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        success = self.request.query_params.get('success')
        if success is not None:
            queryset = queryset.filter(success=success.lower() == 'true')

        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(resource_name__icontains=search) |
                Q(username__icontains=search)
            )

        return queryset.order_by('-timestamp')

    @extend_schema(
        summary='Get audit log summary',
        description='Get summary statistics for audit logs including counts by action type and severity.',
        tags=['Core Infrastructure'],
        responses={
            200: AuditLogSerializer(many=True),
        },
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for audit logs."""
        queryset = self.get_queryset()

        total_count = queryset.count()
        success_count = queryset.filter(success=True).count()
        failed_count = queryset.filter(success=False).count()

        action_type_counts = {}
        for action_type, _ in AuditLog.ACTION_TYPES:
            count = queryset.filter(action_type=action_type).count()
            if count > 0:
                action_type_counts[action_type] = count

        severity_counts = {}
        for severity, _ in AuditLog.SEVERITY_LEVELS:
            count = queryset.filter(severity=severity).count()
            if count > 0:
                severity_counts[severity] = count

        return Response({
            'total_count': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': (success_count / total_count * 100) if total_count > 0 else 0,
            'action_type_counts': action_type_counts,
            'severity_counts': severity_counts,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export_csv(self, request):
        """Export audit logs as CSV (Developer only)."""
        if not request.user.is_developer():
            return Response({'detail': 'Forbidden'}, status=403)
        import csv
        import io
        from django.http import HttpResponse
        qs = self.get_queryset()[:10000]
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            'Timestamp', 'Username', 'Role', 'Action', 'Severity',
            'Resource Type', 'Resource Name', 'Description', 'Success',
            'IP Address',
        ])
        for log in qs.iterator():
            writer.writerow([
                log.timestamp.isoformat() if log.timestamp else '',
                log.username,
                log.user_role,
                log.action_type,
                log.severity,
                log.resource_type,
                log.resource_name,
                (log.description or '')[:500],
                'Yes' if log.success else 'No',
                log.ip_address or '',
            ])
        response = HttpResponse(buf.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs_export.csv"'
        return response


@extend_schema_view(
    list=extend_schema(
        summary='List system backups',
        description='Retrieve a paginated list of system backups. Filterable by backup type and status.',
        tags=['Core Infrastructure'],
        parameters=[
            OpenApiParameter(
                name='backup_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by backup type',
                required=False,
                enum=['database', 'media', 'full', 'incremental'],
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by backup status',
                required=False,
                enum=['pending', 'in_progress', 'completed', 'failed', 'expired'],
            ),
        ],
    ),
    retrieve=extend_schema(
        summary='Retrieve backup details',
        description='Retrieve detailed information about a specific backup.',
        tags=['Core Infrastructure'],
    ),
    create=extend_schema(
        summary='Create backup record',
        description='Create a new backup record (typically created automatically when backup is triggered).',
        tags=['Core Infrastructure'],
    ),
    update=extend_schema(
        summary='Update backup',
        description='Update backup record (limited fields).',
        tags=['Core Infrastructure'],
        exclude=True,  # Usually backups shouldn't be manually updated
    ),
    partial_update=extend_schema(
        summary='Partially update backup',
        description='Partially update backup record.',
        tags=['Core Infrastructure'],
        exclude=True,
    ),
    destroy=extend_schema(
        summary='Delete backup',
        description='Delete a backup record and optionally its file.',
        tags=['Core Infrastructure'],
    ),
)
class SystemBackupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system backups.

    Permissions:
    - Only Managers and Admins can create/delete backups
    - All authenticated users can view backups
    """
    serializer_class = SystemBackupSerializer
    permission_classes = [IsAuthenticated]
    queryset = SystemBackup.objects.all()

    def get_queryset(self):
        """Filter backups."""
        queryset = SystemBackup.objects.all()

        backup_type = self.request.query_params.get('backup_type')
        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-started_at')

    def get_permissions(self):
        """Backups are Developer-only (system infrastructure)."""
        return [IsAuthenticated(), RoleBasedPermission(required_roles=['Developer'])]

    @extend_schema(
        summary='Trigger backup',
        description='Manually trigger a system backup. Requires Manager, Admin, or SuperAdmin role.',
        tags=['Core Infrastructure'],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'backup_type': {
                        'type': 'string',
                        'enum': ['database', 'media', 'full'],
                        'description': 'Type of backup to create',
                        'default': 'database',
                    },
                    'compression': {
                        'type': 'boolean',
                        'description': 'Enable compression (default: true)',
                        'default': True,
                    },
                    'include_media': {
                        'type': 'boolean',
                        'description': 'Include media files (only for database type, default: false)',
                        'default': False,
                    },
                },
                'required': ['backup_type'],
                'example': {
                    'backup_type': 'database',
                    'compression': True,
                    'include_media': False,
                },
            }
        },
        responses={
            201: SystemBackupSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Database Backup Request',
                value={
                    'backup_type': 'database',
                    'compression': True,
                },
                request_only=True,
            ),
            OpenApiExample(
                'Media Backup Request',
                value={
                    'backup_type': 'media',
                    'compression': True,
                },
                request_only=True,
            ),
            OpenApiExample(
                'Full Backup Request',
                value={
                    'backup_type': 'full',
                    'compression': True,
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """
        Manually trigger a backup.

        Request body:
        {
            "backup_type": "database" | "media" | "full",
            "compression": true,
            "include_media": false (only for database type)
        }
        """
        backup_type = request.data.get('backup_type', 'database')
        compression = request.data.get('compression', True)

        try:
            if backup_type == 'database':
                backup = backup_manager.backup_database(
                    include_media=request.data.get('include_media', False),
                    compression=compression,
                    user=request.user
                )
            elif backup_type == 'media':
                backup = backup_manager.backup_media(
                    compression=compression,
                    user=request.user
                )
            elif backup_type == 'full':
                backup = backup_manager.backup_full(
                    compression=compression,
                    user=request.user
                )
            else:
                return Response(
                    {'error': f'Invalid backup_type: {backup_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(backup)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Backup trigger failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary='Verify backup integrity',
        description='Verify the integrity of a backup file by checking its checksum.',
        tags=['Core Infrastructure'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'is_valid': {'type': 'boolean', 'description': 'Whether backup file is valid'},
                    'checksum_match': {'type': 'boolean', 'description': 'Whether checksum matches'},
                },
            },
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify backup integrity."""
        backup = self.get_object()

        is_valid = backup_manager.verify_backup(backup)

        # Log verification
        AuditLogger.log_action(
            action_type='read',
            user=request.user,
            resource=backup,
            description=f"Backup verification: {'passed' if is_valid else 'failed'}",
            success=is_valid,
            request=request,
        )

        return Response({
            'is_valid': is_valid,
            'checksum_match': is_valid,
        })

    @extend_schema(
        summary='Cleanup expired backups',
        description='Delete expired backups based on retention policy. Requires Manager, Admin, or SuperAdmin role.',
        tags=['Core Infrastructure'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'deleted_count': {'type': 'integer', 'description': 'Number of backups deleted'},
                    'message': {'type': 'string', 'description': 'Success message'},
                },
            },
            403: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """Cleanup expired backups."""
        if not request.user.is_developer():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        deleted_count = backup_manager.cleanup_expired_backups()

        # Log cleanup
        AuditLogger.log_action(
            action_type='delete',
            user=request.user,
            resource_type='System',
            description=f"Cleaned up {deleted_count} expired backups",
            request=request,
        )

        return Response({
            'deleted_count': deleted_count,
            'message': f'Cleaned up {deleted_count} expired backups'
        })


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user notifications.
    
    Permissions:
    - Users can only view their own notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the current user."""
        try:
            return Notification.objects.filter(user=self.request.user).order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in NotificationViewSet.get_queryset: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"ERROR in NotificationViewSet.get_queryset: {str(e)}")
            print(traceback.format_exc())
            # Return empty queryset on error
            return Notification.objects.none()
    
    @extend_schema(
        summary='List notifications',
        description='Get the latest 10 notifications for the current user.',
        tags=['Notifications'],
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of notifications to return (default: 10)',
                required=False,
            ),
            OpenApiParameter(
                name='unread_only',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Return only unread notifications',
                required=False,
            ),
        ],
    )
    def list(self, request):
        """Get notifications for the current user."""
        try:
            queryset = self.get_queryset()
            
            # Filter by unread if requested
            unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
            if unread_only:
                queryset = queryset.filter(is_read=False)
            
            # Limit results
            try:
                limit = int(request.query_params.get('limit', 10))
                if limit < 1:
                    limit = 10
            except (ValueError, TypeError):
                limit = 10
            
            queryset = queryset[:limit]
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'notifications': serializer.data,
                'count': len(serializer.data)
            })
        except Exception as e:
            import traceback
            logger.error(f"Error in NotificationViewSet.list: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"ERROR in NotificationViewSet.list: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'error': 'An error occurred while fetching notifications',
                'notifications': [],
                'count': 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary='Mark notification as read',
        description='Mark a specific notification as read.',
        tags=['Notifications'],
    )
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        try:
            notification = self.get_object()
            
            # Ensure user owns this notification
            if notification.user != request.user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        except Exception as e:
            import traceback
            logger.error(f"Error in NotificationViewSet.mark_as_read: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"ERROR in NotificationViewSet.mark_as_read: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': 'An error occurred while marking notification as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary='Mark all notifications as read',
        description='Mark all unread notifications for the current user as read.',
        tags=['Notifications'],
    )
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read for the current user."""
        try:
            updated_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True)
            
            return Response({
                'status': 'success',
                'message': f'Marked {updated_count} notification(s) as read',
                'updated_count': updated_count
            })
        except Exception as e:
            import traceback
            logger.error(f"Error in NotificationViewSet.mark_all_as_read: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"ERROR in NotificationViewSet.mark_all_as_read: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': 'An error occurred while marking all notifications as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary='Dismiss notification',
        description='Delete a specific notification for the current user.',
        tags=['Notifications'],
    )
    @action(detail=True, methods=['delete'])
    def dismiss(self, request, pk=None):
        """Delete a notification owned by current user."""
        try:
            notification = self.get_object()
            if notification.user != request.user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            notification.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {'error': 'An error occurred while dismissing notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary='Clear notifications',
        description='Delete all notifications for the current user.',
        tags=['Notifications'],
    )
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Delete all notifications for current user."""
        try:
            deleted_count, _ = Notification.objects.filter(user=request.user).delete()
            return Response({
                'status': 'success',
                'deleted_count': deleted_count,
            })
        except Exception:
            return Response(
                {'error': 'An error occurred while clearing notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for current user's notification preferences.
    """
    permission_classes = [IsAuthenticated]

    def _get_or_create_preferences(self, user):
        defaults = {
            'notification_email': user.email or '',
        }
        return NotificationPreference.objects.get_or_create(user=user, defaults=defaults)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        preferences, _ = self._get_or_create_preferences(request.user)

        if request.method == 'GET':
            serializer = NotificationPreferenceSerializer(preferences)
            return Response(serializer.data)

        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=(request.method == 'PATCH'),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TVBrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only TV catalog endpoint for Data Center page.
    """

    serializer_class = TVBrandWithModelsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = TVBrand.objects.filter(is_active=True).prefetch_related('models')

        search = (self.request.query_params.get('search') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(models__name__icontains=search)
                | Q(models__model_code__icontains=search)
                | Q(models__series__icontains=search)
            )

        brand = (self.request.query_params.get('brand') or '').strip()
        if brand:
            queryset = queryset.filter(
                Q(slug__iexact=brand) | Q(name__iexact=brand)
            )

        platform = (self.request.query_params.get('platform') or '').strip()
        if platform:
            queryset = queryset.filter(models__platform=platform)

        operation_time = (self.request.query_params.get('operation_time') or '').strip()
        if operation_time:
            queryset = queryset.filter(models__operation_time=operation_time)

        brightness_class = (self.request.query_params.get('brightness_class') or '').strip()
        if brightness_class:
            queryset = queryset.filter(models__brightness_class=brightness_class)

        return queryset.distinct().order_by('sort_order', 'name')