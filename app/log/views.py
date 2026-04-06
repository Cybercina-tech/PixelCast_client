from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, datetime
import logging

from .models import ScreenStatusLog, ContentDownloadLog, CommandExecutionLog, ErrorLog
from .serializers import (
    ScreenStatusLogSerializer, ContentDownloadLogSerializer,
    CommandExecutionLogSerializer, LogSummarySerializer, ErrorLogSerializer
)

logger = logging.getLogger(__name__)


def _operational_logs_visible(user):
    """Developer sees all; others need sidebar view_logs (e.g. Employee)."""
    from accounts.sidebar_config import has_permission

    return bool(
        user
        and user.is_authenticated
        and (user.has_full_access() or has_permission(user, 'view_logs'))
    )


def _accessible_screens_qs(user):
    """Screens whose operational logs a scoped user may read (org + own)."""
    from django.db.models import Q
    from signage.models import Screen

    if not user.is_authenticated:
        return Screen.objects.none()
    if user.has_full_access():
        return Screen.objects.all()
    org = (getattr(user, 'organization_name', None) or '').strip()
    q = Q(owner=user)
    if org:
        q |= Q(owner__organization_name=org)
    return Screen.objects.filter(q)


class LogPagination(PageNumberPagination):
    """Custom pagination for log endpoints - 50 items per page"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


def parse_date_param(date_string):
    """
    Helper function to parse date parameters.
    Supports ISO format and YYYY-MM-DD format.
    
    Args:
        date_string: Date string to parse
        
    Returns:
        datetime: Parsed datetime object or None
    """
    if not date_string:
        return None
    
    try:
        # Try ISO format first
        if 'T' in date_string or 'Z' in date_string:
            date_string = date_string.replace('Z', '+00:00')
            return timezone.datetime.fromisoformat(date_string)
        else:
            # Try YYYY-MM-DD format
            parsed = timezone.datetime.strptime(date_string, '%Y-%m-%d')
            return timezone.make_aware(parsed)
    except (ValueError, AttributeError):
        return None


class ScreenStatusLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ScreenStatusLog model.
    Provides read-only access with role-based permissions, filtering, and summary statistics.
    
    Endpoints:
    - GET /api/logs/screen-status/ - List all screen status logs
    - GET /api/logs/screen-status/{id}/ - Retrieve specific log
    - GET /api/logs/screen-status/summary/ - Get summary statistics
    
    Query Parameters:
    - screen_id: Filter by screen UUID
    - status: Filter by status (online/offline)
    - start_date: Filter from date (ISO or YYYY-MM-DD)
    - end_date: Filter to date (ISO or YYYY-MM-DD)
    - page: Page number for pagination
    - page_size: Items per page (max 1000)
    """
    queryset = ScreenStatusLog.objects.select_related('screen').all()
    serializer_class = ScreenStatusLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LogPagination
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        Ensures no duplicates and optimizes queries.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not _operational_logs_visible(user):
            return queryset.none()
        if not user.has_full_access():
            queryset = queryset.filter(screen__in=_accessible_screens_qs(user))

        # Filter by screen if provided
        screen_id = self.request.query_params.get('screen_id')
        if screen_id:
            try:
                queryset = queryset.filter(screen_id=screen_id)
            except ValueError:
                # Invalid UUID format
                queryset = queryset.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            valid_statuses = [choice[0] for choice in ScreenStatusLog.STATUS_CHOICES]
            if status_filter in valid_statuses:
                queryset = queryset.filter(status=status_filter)
        
        # Filter by date range if provided
        start_date = parse_date_param(self.request.query_params.get('start_date'))
        end_date = parse_date_param(self.request.query_params.get('end_date'))
        
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            # Include entire end date
            end_date = end_date + timedelta(days=1)
            queryset = queryset.filter(recorded_at__lt=end_date)
        
        # Ensure no duplicates and order by recorded_at descending
        # PostgreSQL optimization: distinct() without arguments removes exact duplicates
        # This is safe and efficient for PostgreSQL
        queryset = queryset.distinct().order_by('-recorded_at', '-id')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/logs/screen-status/summary/
        Get summary statistics for screen status logs.
        
        Query Parameters:
        - screen_id: Filter by screen UUID
        - start_date: Filter from date (ISO or YYYY-MM-DD)
        - end_date: Filter to date (ISO or YYYY-MM-DD)
        """
        if not _operational_logs_visible(request.user):
            return Response({
                'status': 'success',
                'summary': {'total_count': 0},
            }, status=status.HTTP_200_OK)

        base_qs = None
        if not request.user.has_full_access():
            base_qs = ScreenStatusLog.objects.filter(screen__in=_accessible_screens_qs(request.user))

        screen_id = request.query_params.get('screen_id')
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        
        # Handle end_date to include entire day
        if end_date:
            end_date = end_date + timedelta(days=1)
        
        screen = None
        if screen_id:
            from signage.models import Screen
            from accounts.permissions import RolePermissions
            try:
                screen = Screen.objects.get(id=screen_id)
            except Screen.DoesNotExist:
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if not request.user.has_full_access() and not RolePermissions.can_view_resource(request.user, screen):
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        stats = ScreenStatusLog.get_summary_stats(
            screen=screen,
            start_date=start_date,
            end_date=end_date,
            base_queryset=base_qs,
        )
        
        serializer = LogSummarySerializer(stats)
        return Response({
            'status': 'success',
            'summary': serializer.data
        }, status=status.HTTP_200_OK)


class ContentDownloadLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ContentDownloadLog model.
    Provides read-only access with role-based permissions, filtering, and summary statistics.
    
    Endpoints:
    - GET /api/logs/content-download/ - List all content download logs
    - GET /api/logs/content-download/{id}/ - Retrieve specific log
    - GET /api/logs/content-download/summary/ - Get summary statistics
    
    Query Parameters:
    - content_id: Filter by content UUID
    - screen_id: Filter by screen UUID
    - status: Filter by status (pending/success/failed)
    - start_date: Filter from date (ISO or YYYY-MM-DD) - filters by created_at
    - end_date: Filter to date (ISO or YYYY-MM-DD) - filters by created_at
    - downloaded_from: Filter downloads from date - filters by downloaded_at
    - downloaded_to: Filter downloads to date - filters by downloaded_at
    - page: Page number for pagination
    - page_size: Items per page (max 1000)
    """
    queryset = ContentDownloadLog.objects.select_related('content', 'screen').all()
    serializer_class = ContentDownloadLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LogPagination
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        Ensures no duplicates and optimizes queries.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not _operational_logs_visible(user):
            return queryset.none()
        if not user.has_full_access():
            queryset = queryset.filter(screen__in=_accessible_screens_qs(user))
        
        # Filter by content if provided
        content_id = self.request.query_params.get('content_id')
        if content_id:
            try:
                queryset = queryset.filter(content_id=content_id)
            except ValueError:
                queryset = queryset.none()
        
        # Filter by screen if provided
        screen_id = self.request.query_params.get('screen_id')
        if screen_id:
            try:
                queryset = queryset.filter(screen_id=screen_id)
            except ValueError:
                queryset = queryset.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            valid_statuses = [choice[0] for choice in ContentDownloadLog.STATUS_CHOICES]
            if status_filter in valid_statuses:
                queryset = queryset.filter(status=status_filter)
        
        # Filter by created_at date range if provided
        start_date = parse_date_param(self.request.query_params.get('start_date'))
        end_date = parse_date_param(self.request.query_params.get('end_date'))
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            end_date = end_date + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_date)
        
        # Filter by downloaded_at date range if provided
        downloaded_from = parse_date_param(self.request.query_params.get('downloaded_from'))
        downloaded_to = parse_date_param(self.request.query_params.get('downloaded_to'))
        
        if downloaded_from:
            queryset = queryset.filter(downloaded_at__gte=downloaded_from)
        if downloaded_to:
            downloaded_to = downloaded_to + timedelta(days=1)
            queryset = queryset.filter(downloaded_at__lt=downloaded_to)
        
        # Ensure no duplicates and order by created_at descending
        queryset = queryset.distinct().order_by('-created_at', '-id')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/logs/content-download/summary/
        Get summary statistics for content download logs.
        
        Query Parameters:
        - content_id: Filter by content UUID
        - screen_id: Filter by screen UUID
        - start_date: Filter from date (ISO or YYYY-MM-DD)
        - end_date: Filter to date (ISO or YYYY-MM-DD)
        """
        if not _operational_logs_visible(request.user):
            return Response({
                'status': 'success',
                'summary': {'total_count': 0},
            }, status=status.HTTP_200_OK)

        base_qs = None
        if not request.user.has_full_access():
            base_qs = ContentDownloadLog.objects.filter(screen__in=_accessible_screens_qs(request.user))
        
        content_id = request.query_params.get('content_id')
        screen_id = request.query_params.get('screen_id')
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        
        # Handle end_date to include entire day
        if end_date:
            end_date = end_date + timedelta(days=1)
        
        content = None
        if content_id:
            from templates.models import Content
            try:
                content = Content.objects.get(id=content_id)
            except Content.DoesNotExist:
                return Response(
                    {'error': 'Content not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        screen = None
        if screen_id:
            from signage.models import Screen
            from accounts.permissions import RolePermissions
            try:
                screen = Screen.objects.get(id=screen_id)
            except Screen.DoesNotExist:
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if not request.user.has_full_access() and not RolePermissions.can_view_resource(request.user, screen):
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        stats = ContentDownloadLog.get_summary_stats(
            content=content,
            screen=screen,
            start_date=start_date,
            end_date=end_date,
            base_queryset=base_qs,
        )
        
        serializer = LogSummarySerializer(stats)
        return Response({
            'status': 'success',
            'summary': serializer.data
        }, status=status.HTTP_200_OK)


class CommandExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for CommandExecutionLog model.
    Provides read-only access with role-based permissions, filtering, and summary statistics.
    
    Endpoints:
    - GET /api/logs/command-execution/ - List all command execution logs
    - GET /api/logs/command-execution/{id}/ - Retrieve specific log
    - GET /api/logs/command-execution/summary/ - Get summary statistics
    
    Query Parameters:
    - command_id: Filter by command UUID
    - screen_id: Filter by screen UUID
    - status: Filter by status (pending/running/done/failed)
    - start_date: Filter from date (ISO or YYYY-MM-DD) - filters by created_at
    - end_date: Filter to date (ISO or YYYY-MM-DD) - filters by created_at
    - started_from: Filter executions started from date - filters by started_at
    - started_to: Filter executions started to date - filters by started_at
    - finished_from: Filter executions finished from date - filters by finished_at
    - finished_to: Filter executions finished to date - filters by finished_at
    - page: Page number for pagination
    - page_size: Items per page (max 1000)
    """
    queryset = CommandExecutionLog.objects.select_related('command', 'screen').all()
    serializer_class = CommandExecutionLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LogPagination
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        Ensures no duplicates and optimizes queries.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not _operational_logs_visible(user):
            return queryset.none()
        if not user.has_full_access():
            queryset = queryset.filter(screen__in=_accessible_screens_qs(user))
        
        # Filter by command if provided
        command_id = self.request.query_params.get('command_id')
        if command_id:
            try:
                queryset = queryset.filter(command_id=command_id)
            except ValueError:
                queryset = queryset.none()
        
        # Filter by screen if provided
        screen_id = self.request.query_params.get('screen_id')
        if screen_id:
            try:
                queryset = queryset.filter(screen_id=screen_id)
            except ValueError:
                queryset = queryset.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            valid_statuses = [choice[0] for choice in CommandExecutionLog.STATUS_CHOICES]
            if status_filter in valid_statuses:
                queryset = queryset.filter(status=status_filter)
        
        # Filter by created_at date range if provided
        start_date = parse_date_param(self.request.query_params.get('start_date'))
        end_date = parse_date_param(self.request.query_params.get('end_date'))
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            end_date = end_date + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_date)
        
        # Filter by started_at date range if provided
        started_from = parse_date_param(self.request.query_params.get('started_from'))
        started_to = parse_date_param(self.request.query_params.get('started_to'))
        
        if started_from:
            queryset = queryset.filter(started_at__gte=started_from)
        if started_to:
            started_to = started_to + timedelta(days=1)
            queryset = queryset.filter(started_at__lt=started_to)
        
        # Filter by finished_at date range if provided
        finished_from = parse_date_param(self.request.query_params.get('finished_from'))
        finished_to = parse_date_param(self.request.query_params.get('finished_to'))
        
        if finished_from:
            queryset = queryset.filter(finished_at__gte=finished_from)
        if finished_to:
            finished_to = finished_to + timedelta(days=1)
            queryset = queryset.filter(finished_at__lt=finished_to)
        
        # Ensure no duplicates and order by created_at descending
        queryset = queryset.distinct().order_by('-created_at', '-id')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/logs/command-execution/summary/
        Get summary statistics for command execution logs.
        
        Query Parameters:
        - command_id: Filter by command UUID
        - screen_id: Filter by screen UUID
        - start_date: Filter from date (ISO or YYYY-MM-DD)
        - end_date: Filter to date (ISO or YYYY-MM-DD)
        """
        if not _operational_logs_visible(request.user):
            return Response({
                'status': 'success',
                'summary': {'total_count': 0},
            }, status=status.HTTP_200_OK)

        base_qs = None
        if not request.user.has_full_access():
            base_qs = CommandExecutionLog.objects.filter(screen__in=_accessible_screens_qs(request.user))
        
        command_id = request.query_params.get('command_id')
        screen_id = request.query_params.get('screen_id')
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        
        # Handle end_date to include entire day
        if end_date:
            end_date = end_date + timedelta(days=1)
        
        command = None
        if command_id:
            from commands.models import Command
            try:
                command = Command.objects.get(id=command_id)
            except Command.DoesNotExist:
                return Response(
                    {'error': 'Command not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        screen = None
        if screen_id:
            from signage.models import Screen
            from accounts.permissions import RolePermissions
            try:
                screen = Screen.objects.get(id=screen_id)
            except Screen.DoesNotExist:
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if not request.user.has_full_access() and not RolePermissions.can_view_resource(request.user, screen):
                return Response(
                    {'error': 'Screen not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        stats = CommandExecutionLog.get_summary_stats(
            command=command,
            screen=screen,
            start_date=start_date,
            end_date=end_date,
            base_queryset=base_qs,
        )
        
        serializer = LogSummarySerializer(stats)
        return Response({
            'status': 'success',
            'summary': serializer.data
        }, status=status.HTTP_200_OK)


class ErrorLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ErrorLog model.
    Provides read-only access for SuperAdmin users only.
    
    Endpoints:
    - GET /api/admin/errors/ - List all error logs
    - GET /api/admin/errors/{id}/ - Retrieve specific error log
    - PATCH /api/admin/errors/{id}/resolve/ - Mark error as resolved
    - GET /api/admin/errors/stats/ - Get error statistics
    
    Query Parameters:
    - level: Filter by error level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - endpoint: Filter by endpoint (partial match)
    - start_date: Filter from date (ISO or YYYY-MM-DD)
    - end_date: Filter to date (ISO or YYYY-MM-DD)
    - is_resolved: Filter by resolved status (true/false)
    - user_id: Filter by user ID
    - exception_type: Filter by exception type
    - page: Page number for pagination
    - page_size: Items per page (max 1000)
    """
    queryset = ErrorLog.objects.select_related('user', 'resolved_by').all()
    serializer_class = ErrorLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LogPagination
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Filter queryset based on SuperAdmin permission and query parameters.
        Only SuperAdmin users can access error logs.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Only SuperAdmin can access error logs
        if not user.is_superadmin():
            raise PermissionDenied("Only Developer users can access error logs.")
        
        # Filter by level
        level = self.request.query_params.get('level')
        if level:
            valid_levels = [choice[0] for choice in ErrorLog.LEVEL_CHOICES]
            if level.upper() in valid_levels:
                queryset = queryset.filter(level=level.upper())
        
        # Filter by endpoint
        endpoint = self.request.query_params.get('endpoint')
        if endpoint:
            queryset = queryset.filter(endpoint__icontains=endpoint)
        
        # Filter by date range
        start_date = parse_date_param(self.request.query_params.get('start_date'))
        end_date = parse_date_param(self.request.query_params.get('end_date'))
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            end_date = end_date + timedelta(days=1)
            queryset = queryset.filter(timestamp__lt=end_date)
        
        # Filter by resolved status
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            is_resolved_bool = is_resolved.lower() == 'true'
            queryset = queryset.filter(is_resolved=is_resolved_bool)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            try:
                queryset = queryset.filter(user_id=int(user_id))
            except ValueError:
                queryset = queryset.none()
        
        # Filter by exception type
        exception_type = self.request.query_params.get('exception_type')
        if exception_type:
            queryset = queryset.filter(exception_type__icontains=exception_type)
        
        # Order by timestamp descending (most recent first)
        queryset = queryset.distinct().order_by('-timestamp', '-id')
        
        return queryset
    
    @action(detail=True, methods=['patch'])
    def resolve(self, request, id=None):
        """
        PATCH /api/admin/errors/{id}/resolve/
        Mark an error as resolved.
        """
        if not request.user.is_superadmin():
            raise PermissionDenied("Only Developer users can resolve errors.")
        
        error_log = self.get_object()
        error_log.is_resolved = True
        error_log.resolved_at = timezone.now()
        error_log.resolved_by = request.user
        error_log.save()
        
        serializer = self.get_serializer(error_log)
        return Response({
            'status': 'success',
            'message': 'Error marked as resolved',
            'error': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/admin/errors/stats/
        Get error statistics.
        """
        if not request.user.is_superadmin():
            raise PermissionDenied("Only Developer users can view error statistics.")
        
        queryset = self.get_queryset()
        
        # Get date range from query params if provided
        start_date = parse_date_param(request.query_params.get('start_date'))
        end_date = parse_date_param(request.query_params.get('end_date'))
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            end_date = end_date + timedelta(days=1)
            queryset = queryset.filter(timestamp__lt=end_date)
        
        total_count = queryset.count()
        unresolved_count = queryset.filter(is_resolved=False).count()
        
        # Count by level
        level_counts = {}
        for level, _ in ErrorLog.LEVEL_CHOICES:
            level_counts[level] = queryset.filter(level=level).count()
        
        # Count by exception type (top 10)
        from django.db.models import Count
        top_exceptions = queryset.values('exception_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'status': 'success',
            'stats': {
                'total_count': total_count,
                'unresolved_count': unresolved_count,
                'resolved_count': total_count - unresolved_count,
                'level_counts': level_counts,
                'top_exceptions': list(top_exceptions),
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated for client-side error reporting
def client_log_view(request):
    """
    Endpoint for receiving client-side JavaScript errors from Player/Editor.
    
    This is the "Black Box" - allows debugging screens that are physically far away.
    
    POST /api/logs/client/
    
    Body:
    {
        "level": "error|warning|info|debug",
        "message": "Error message",
        "filename": "script.js",
        "lineno": 42,
        "colno": 10,
        "stack": "Stack trace...",
        "user_agent": "Browser user agent",
        "url": "Current page URL",
        "timestamp": "ISO timestamp",
        "metadata": {
            "screen_id": "...",
            "template_id": "...",
            "viewport": {...}
        }
    }
    """
    try:
        data = request.data
        
        # Map client log level to ErrorLog level
        level_mapping = {
            'error': 'ERROR',
            'warning': 'WARNING',
            'info': 'INFO',
            'debug': 'DEBUG',
        }
        error_level = level_mapping.get(data.get('level', 'error'), 'ERROR')
        
        # Build error message
        message_parts = [data.get('message', 'Unknown client error')]
        if data.get('filename'):
            message_parts.append(f"File: {data.get('filename')}")
        if data.get('lineno'):
            message_parts.append(f"Line: {data.get('lineno')}")
        if data.get('colno'):
            message_parts.append(f"Column: {data.get('colno')}")
        
        error_message = ' | '.join(message_parts)
        
        # Extract metadata
        metadata = data.get('metadata', {})
        metadata['source'] = 'client'
        metadata['url'] = data.get('url', '')
        if data.get('viewport'):
            metadata['viewport'] = data.get('viewport')
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Create ErrorLog entry
        ErrorLog.objects.create(
            level=error_level,
            message=error_message,
            stack_trace=data.get('stack', ''),
            endpoint=data.get('url', ''),
            request_method='CLIENT',
            ip_address=ip_address,
            user_agent=data.get('user_agent', ''),
            exception_type='ClientError',
            metadata=metadata,
        )
        
        # Also log to standard logger
        logger.info(
            f"Client error logged: {error_message}",
            extra={
                'level': error_level,
                'url': data.get('url'),
                'screen_id': metadata.get('screen_id'),
                'template_id': metadata.get('template_id'),
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'Client error logged successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Failed to log client error: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': 'Failed to log client error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
