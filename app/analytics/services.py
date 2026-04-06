"""
Analytics services for aggregating and calculating metrics.

Provides services for screens, commands, content, templates, and activity analytics.
"""
import logging
from django.db.models import (
    Q, Count, Avg, Max, Min, Sum, F, Case, When, IntegerField,
    FloatField, DateTimeField, Value, CharField
)
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from datetime import timedelta, datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from signage.models import Screen
from commands.models import Command
from templates.models import Content, Template, Schedule
from log.models import (
    ScreenStatusLog, CommandExecutionLog, ContentDownloadLog
)
from accounts.models import User

logger = logging.getLogger(__name__)


class ScreenAnalyticsService:
    """Service for screen health and status analytics."""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def _latest_status_logs_per_screen(queryset):
        """
        Return one latest status log per screen from queryset.
        Uses PostgreSQL DISTINCT ON when available, with safe Python fallback.
        """
        from django.conf import settings

        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            return list(queryset.order_by('screen_id', '-recorded_at').distinct('screen_id'))

        recent_logs = queryset.order_by('-recorded_at')
        screen_ids_seen = set()
        recent_logs_list = []
        for log in recent_logs:
            if log.screen_id in screen_ids_seen:
                continue
            recent_logs_list.append(log)
            screen_ids_seen.add(log.screen_id)
        return recent_logs_list

    @staticmethod
    def get_screen_statistics(
        screen_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated screen statistics.
        
        Args:
            screen_ids: Optional list of screen IDs to filter by
            start_date: Optional start date for time range
            end_date: Optional end date for time range
            
        Returns:
            Dictionary with screen statistics
        """
        if screen_ids is not None and len(screen_ids) == 0:
            return {
                'total_screens': 0,
                'status_breakdown': {'online': 0, 'offline': 0, 'total': 0},
                'health_metrics': {
                    'avg_cpu_usage': 0.0,
                    'avg_memory_usage': 0.0,
                    'avg_latency_ms': 0.0,
                    'max_cpu_usage': 0.0,
                    'max_memory_usage': 0.0,
                    'max_latency_ms': 0.0,
                    'min_latency_ms': 0.0,
                },
                'health_score': 0.0,
                'period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                },
            }

        # Base queryset
        screens = Screen.objects.all()
        
        if screen_ids is not None:
            screens = screens.filter(id__in=screen_ids)
        
        # Get online/offline counts
        total_screens = screens.count()
        online_count = screens.filter(is_online=True).count()
        offline_count = total_screens - online_count
        
        # Get recent status logs for metrics
        status_logs = ScreenStatusLog.objects.all()
        if screen_ids is not None:
            status_logs = status_logs.filter(screen_id__in=screen_ids)
        if start_date:
            status_logs = status_logs.filter(recorded_at__gte=start_date)
        if end_date:
            status_logs = status_logs.filter(recorded_at__lte=end_date)
        
        recent_logs_list = ScreenAnalyticsService._latest_status_logs_per_screen(status_logs)

        # If the selected date range has no logs, fallback to latest known metrics overall.
        if not recent_logs_list:
            fallback_logs = ScreenStatusLog.objects.all()
            if screen_ids is not None:
                fallback_logs = fallback_logs.filter(screen_id__in=screen_ids)
            recent_logs_list = ScreenAnalyticsService._latest_status_logs_per_screen(fallback_logs)
        
        # Aggregate metrics from recent logs
        if recent_logs_list:
            # Aggregate using the filtered list (Python built-ins for SQLite compatibility)
            cpu_values = [log.cpu_usage for log in recent_logs_list if log.cpu_usage is not None]
            memory_values = [log.memory_usage for log in recent_logs_list if log.memory_usage is not None]
            latency_values = [log.heartbeat_latency for log in recent_logs_list if log.heartbeat_latency is not None]
            
            metrics = {
                'avg_cpu': sum(cpu_values) / len(cpu_values) if cpu_values else None,
                'avg_memory': sum(memory_values) / len(memory_values) if memory_values else None,
                'avg_latency': sum(latency_values) / len(latency_values) if latency_values else None,
                'max_cpu': max(cpu_values) if cpu_values else None,
                'max_memory': max(memory_values) if memory_values else None,
                'max_latency': max(latency_values) if latency_values else None,
                'min_latency': min(latency_values) if latency_values else None,
            }
        else:
            metrics = {
                'avg_cpu': None,
                'avg_memory': None,
                'avg_latency': None,
                'max_cpu': None,
                'max_memory': None,
                'max_latency': None,
                'min_latency': None,
            }
        
        # Get screens by status breakdown
        status_breakdown = {
            'online': online_count,
            'offline': offline_count,
            'total': total_screens
        }
        
        # Calculate health score (percentage of online screens)
        health_score = (online_count / total_screens * 100) if total_screens > 0 else 0
        
        return {
            'total_screens': total_screens,
            'status_breakdown': status_breakdown,
            'health_metrics': {
                'avg_cpu_usage': round(float(metrics['avg_cpu']), 2) if metrics['avg_cpu'] is not None else 0.0,
                'avg_memory_usage': round(float(metrics['avg_memory']), 2) if metrics['avg_memory'] is not None else 0.0,
                'avg_latency_ms': round(float(metrics['avg_latency']), 2) if metrics['avg_latency'] is not None else 0.0,
                'max_cpu_usage': round(float(metrics['max_cpu']), 2) if metrics['max_cpu'] is not None else 0.0,
                'max_memory_usage': round(float(metrics['max_memory']), 2) if metrics['max_memory'] is not None else 0.0,
                'max_latency_ms': round(float(metrics['max_latency']), 2) if metrics['max_latency'] is not None else 0.0,
                'min_latency_ms': round(float(metrics['min_latency']), 2) if metrics['min_latency'] is not None else 0.0,
            },
            'health_score': round(health_score, 2),
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
            }
        }
    
    @staticmethod
    def get_screen_details(screen_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific screen.
        
        Args:
            screen_id: UUID of the screen
            
        Returns:
            Dictionary with detailed screen analytics
        """
        try:
            screen = Screen.objects.get(id=screen_id)
        except Screen.DoesNotExist:
            logger.warning(f"Screen not found: {screen_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching screen {screen_id}: {str(e)}")
            raise
        
        try:
            # Get recent status logs (last 100)
            recent_logs = ScreenStatusLog.objects.filter(
                screen=screen
            ).order_by('-recorded_at')[:100]
            
            # Calculate averages from recent logs
            if recent_logs.exists():
                recent_metrics = recent_logs.aggregate(
                    avg_cpu=Avg('cpu_usage'),
                    avg_memory=Avg('memory_usage'),
                    avg_latency=Avg('heartbeat_latency'),
                )
            else:
                recent_metrics = {
                    'avg_cpu': None,
                    'avg_memory': None,
                    'avg_latency': None,
                }
            
            # Get command statistics
            commands = Command.objects.filter(screen=screen)
            command_stats = commands.aggregate(
                total=Count('id'),
                pending=Count('id', filter=Q(status='pending')),
                executing=Count('id', filter=Q(status='executing')),
                done=Count('id', filter=Q(status='done')),
                failed=Count('id', filter=Q(status='failed')),
            )
            
            # Get last heartbeat age
            last_heartbeat_age = None
            if screen.last_heartbeat_at:
                delta = timezone.now() - screen.last_heartbeat_at
                last_heartbeat_age = int(delta.total_seconds())
            
            # Get first status log safely
            first_log = recent_logs.first() if recent_logs.exists() else None
            
            return {
                'screen_id': str(screen.id),
                'screen_name': screen.name,
                'device_id': screen.device_id,
                'is_online': screen.is_online,
                'current_metrics': {
                    'cpu_usage': first_log.cpu_usage if first_log and first_log.cpu_usage is not None else None,
                    'memory_usage': first_log.memory_usage if first_log and first_log.memory_usage is not None else None,
                    'latency_ms': first_log.heartbeat_latency if first_log and first_log.heartbeat_latency is not None else None,
                },
                'recent_averages': {
                    'avg_cpu_usage': round(float(recent_metrics['avg_cpu']), 2) if recent_metrics['avg_cpu'] is not None else None,
                    'avg_memory_usage': round(float(recent_metrics['avg_memory']), 2) if recent_metrics['avg_memory'] is not None else None,
                    'avg_latency_ms': round(float(recent_metrics['avg_latency']), 2) if recent_metrics['avg_latency'] is not None else None,
                },
                'status': {
                    'last_heartbeat_at': screen.last_heartbeat_at.isoformat() if screen.last_heartbeat_at else None,
                    'last_heartbeat_age_seconds': last_heartbeat_age,
                    'is_busy': screen.is_busy,
                    'app_version': screen.app_version or None,
                    'os_version': screen.os_version or None,
                },
                'command_statistics': {
                    'total': command_stats['total'] or 0,
                    'pending': command_stats['pending'] or 0,
                    'executing': command_stats['executing'] or 0,
                    'done': command_stats['done'] or 0,
                    'failed': command_stats['failed'] or 0,
                },
                'active_template': {
                    'template_id': str(screen.active_template.id) if screen.active_template else None,
                    'template_name': screen.active_template.name if screen.active_template else None,
                } if screen.active_template else None,
            }
        except Exception as e:
            logger.error(f"Error processing screen details for {screen_id}: {str(e)}", exc_info=True)
            raise


class CommandAnalyticsService:
    """Service for command statistics analytics."""
    
    @staticmethod
    def get_command_statistics(
        screen_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = 'day'
    ) -> Dict[str, Any]:
        """
        Get aggregated command statistics.
        
        Args:
            screen_ids: Optional list of screen IDs to filter by
            start_date: Optional start date for time range
            end_date: Optional end date for time range
            period: Aggregation period ('day', 'week', 'month')
            
        Returns:
            Dictionary with command statistics
        """
        try:
            commands = Command.objects.all()
            
            if screen_ids is not None:
                if len(screen_ids) == 0:
                    commands = Command.objects.none()
                else:
                    commands = commands.filter(screen_id__in=screen_ids)
            if start_date:
                commands = commands.filter(created_at__gte=start_date)
            if end_date:
                commands = commands.filter(created_at__lte=end_date)
            
            # Overall statistics
            overall_stats = commands.aggregate(
                total=Count('id'),
                pending=Count('id', filter=Q(status='pending')),
                executing=Count('id', filter=Q(status='executing')),
                done=Count('id', filter=Q(status='done')),
                failed=Count('id', filter=Q(status='failed')),
            )
            
            # Statistics by command type
            type_stats = list(commands.values('type').annotate(
                count=Count('id'),
                pending=Count('id', filter=Q(status='pending')),
                done=Count('id', filter=Q(status='done')),
                failed=Count('id', filter=Q(status='failed')),
            ).order_by('-count'))
            
            # Statistics by status
            status_stats = list(commands.values('status').annotate(
                count=Count('id')
            ).order_by('-count'))
            
            # Time series aggregation
            trunc_func = TruncDate('created_at')
            if period == 'week':
                trunc_func = TruncWeek('created_at')
            elif period == 'month':
                trunc_func = TruncMonth('created_at')
            
            time_series = list(commands.annotate(
                period=trunc_func
            ).values('period').annotate(
                total=Count('id'),
                done=Count('id', filter=Q(status='done')),
                failed=Count('id', filter=Q(status='failed')),
            ).order_by('period'))
            
            # Calculate success rate
            total_count = overall_stats['total'] or 0
            done_count = overall_stats['done'] or 0
            success_rate = 0
            if total_count > 0:
                success_rate = (done_count / total_count) * 100
            
            return {
                'overall': {
                    'total': total_count,
                    'pending': overall_stats['pending'] or 0,
                    'executing': overall_stats['executing'] or 0,
                    'done': done_count,
                    'failed': overall_stats['failed'] or 0,
                    'success_rate': round(success_rate, 2),
                },
                'by_type': [
                    {
                        'type': item.get('type', 'unknown'),
                        'total': item.get('count', 0),
                        'pending': item.get('pending', 0),
                        'done': item.get('done', 0),
                        'failed': item.get('failed', 0),
                    }
                    for item in type_stats
                ],
                'by_status': [
                    {
                        'status': item.get('status', 'unknown'),
                        'count': item.get('count', 0),
                    }
                    for item in status_stats
                ],
                'time_series': [
                    {
                        'period': item['period'].isoformat() if item.get('period') else None,
                        'total': item.get('total', 0),
                        'done': item.get('done', 0),
                        'failed': item.get('failed', 0),
                    }
                    for item in time_series
                ],
                'period': period,
            }
        except Exception as e:
            logger.error(f"Error in get_command_statistics: {str(e)}", exc_info=True)
            raise


class ContentAnalyticsService:
    """Service for content download and usage analytics."""
    
    @staticmethod
    def get_content_statistics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        screen_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get content download and usage statistics.
        
        Args:
            start_date: Optional start date for time range
            end_date: Optional end date for time range
            screen_ids: When set, restrict download logs (and type stats) to these screens
            
        Returns:
            Dictionary with content statistics
        """
        try:
            # Content download logs
            download_logs = ContentDownloadLog.objects.all()
            if screen_ids is not None:
                if len(screen_ids) == 0:
                    download_logs = ContentDownloadLog.objects.none()
                else:
                    download_logs = download_logs.filter(screen_id__in=screen_ids)
            if start_date:
                download_logs = download_logs.filter(created_at__gte=start_date)
            if end_date:
                download_logs = download_logs.filter(created_at__lte=end_date)
            
            # Overall download statistics
            download_stats = download_logs.aggregate(
                total_downloads=Count('id'),
                successful=Count('id', filter=Q(status='success')),
                failed=Count('id', filter=Q(status='failed')),
                in_progress=Count('id', filter=Q(status='in_progress')),
            )
            
            # Statistics by content type (global, or from scoped download logs only)
            if screen_ids is not None:
                content_types = list(download_logs.values('content__type').annotate(
                    count=Count('id'),
                ).order_by('-count'))
            else:
                content_types = list(Content.objects.values('type').annotate(
                    count=Count('id'),
                ).order_by('-count'))
            
            # Download statistics by content type
            type_download_stats = []
            if download_logs.exists():
                type_download_stats = list(download_logs.values(
                    'content__type'
                ).annotate(
                    total=Count('id'),
                    successful=Count('id', filter=Q(status='success')),
                    failed=Count('id', filter=Q(status='failed')),
                ).order_by('-total'))
            
            # Calculate error rate
            total_downloads = download_stats['total_downloads'] or 0
            failed_count = download_stats['failed'] or 0
            error_rate = 0
            if total_downloads > 0:
                error_rate = (failed_count / total_downloads) * 100
            
            # Content type distribution
            if screen_ids is not None:
                total_content = sum(item.get('count', 0) for item in content_types)
            else:
                total_content = Content.objects.count()
            type_distribution = [
                {
                    'type': item.get('content__type' if screen_ids is not None else 'type', 'unknown'),
                    'count': item.get('count', 0),
                    'percentage': round((item.get('count', 0) / total_content * 100), 2) if total_content > 0 else 0,
                }
                for item in content_types
            ]
            
            return {
                'download_statistics': {
                    'total_downloads': total_downloads,
                    'successful': download_stats['successful'] or 0,
                    'failed': failed_count,
                    'in_progress': download_stats['in_progress'] or 0,
                    'error_rate': round(error_rate, 2),
                },
                'type_distribution': type_distribution,
                'downloads_by_type': [
                    {
                        'type': item.get('content__type', 'unknown'),
                        'total': item.get('total', 0),
                        'successful': item.get('successful', 0),
                        'failed': item.get('failed', 0),
                    }
                    for item in type_download_stats
                ],
                'total_content_items': (
                    Content.objects.count()
                    if screen_ids is None
                    else download_logs.values('content_id').distinct().count()
                ),
            }
        except Exception as e:
            logger.error(f"Error in get_content_statistics: {str(e)}", exc_info=True)
            raise


class TemplateAnalyticsService:
    """Service for template usage analytics."""
    
    @staticmethod
    def get_template_statistics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        screen_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get template usage statistics.
        
        Args:
            start_date: Optional start date for time range
            end_date: Optional end date for time range
            screen_ids: When set, limit to templates active on these screens
            
        Returns:
            Dictionary with template statistics
        """
        try:
            templates = Template.objects.all()
            if screen_ids is not None:
                if len(screen_ids) == 0:
                    templates = Template.objects.none()
                else:
                    templates = Template.objects.filter(active_screens__id__in=screen_ids).distinct()
            
            # Template usage statistics - count active screens per template (scoped when screen_ids set)
            if screen_ids is None:
                template_stats = templates.annotate(
                    active_screen_count=Count('active_screens', distinct=True),
                ).order_by('-active_screen_count')
            else:
                template_stats = templates.annotate(
                    active_screen_count=Count(
                        'active_screens',
                        filter=Q(active_screens__id__in=screen_ids),
                        distinct=True,
                    ),
                ).order_by('-active_screen_count')
            
            # Most active templates (currently on screens)
            most_active = list(template_stats[:10])
            
            # Total templates and active screens
            total_templates = templates.count()
            if screen_ids is None:
                total_active_screens = Screen.objects.filter(active_template__isnull=False).count()
            elif len(screen_ids) == 0:
                total_active_screens = 0
            else:
                total_active_screens = Screen.objects.filter(
                    id__in=screen_ids,
                    active_template__isnull=False,
                ).count()
            
            # Templates by orientation
            orientation_stats = list(templates.values('orientation').annotate(
                count=Count('id')
            ))
            
            return {
                'total_templates': total_templates,
                'total_active_screens': total_active_screens,
                'most_active_templates': [
                    {
                        'template_id': str(template.id),
                        'template_name': template.name,
                        'active_screen_count': getattr(template, 'active_screen_count', 0),
                    }
                    for template in most_active
                ],
                'by_orientation': [
                    {
                        'orientation': item.get('orientation', 'unknown'),
                        'count': item.get('count', 0),
                    }
                    for item in orientation_stats
                ],
            }
        except Exception as e:
            logger.error(f"Error in get_template_statistics: {str(e)}", exc_info=True)
            raise


class ActivityAnalyticsService:
    """Service for activity trends analytics."""
    
    @staticmethod
    def get_activity_trends(
        period: str = 'day',
        days: int = 30,
        screen_ids: Optional[List[str]] = None,
        scope_user=None,
    ) -> Dict[str, Any]:
        """
        Get activity trends over time.
        
        Args:
            period: Aggregation period ('day', 'week', 'month')
            days: Number of days to look back
            screen_ids: When set (Employee analytics), restrict screens/commands to these IDs
            scope_user: When set with screen_ids, limit template/content trends to this user
            
        Returns:
            Dictionary with activity trends
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)

            if screen_ids is not None and len(screen_ids) == 0:
                return {
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'screen_registrations': [],
                    'commands_created': [],
                    'templates_created': [],
                    'content_uploads': [],
                }
            
            trunc_func = TruncDate('created_at')
            if period == 'week':
                trunc_func = TruncWeek('created_at')
            elif period == 'month':
                trunc_func = TruncMonth('created_at')
            
            # Screen registrations
            screen_registrations = Screen.objects.filter(
                registration_date__gte=start_date,
                registration_date__lte=end_date
            )
            if screen_ids is not None:
                screen_registrations = screen_registrations.filter(id__in=screen_ids)
            screen_registrations = screen_registrations.annotate(
                period=trunc_func
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
            
            # Commands created
            commands_created = Command.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            if screen_ids is not None:
                commands_created = commands_created.filter(screen_id__in=screen_ids)
            commands_created = commands_created.annotate(
                period=trunc_func
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
            
            # Templates created
            templates_created = Template.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            if screen_ids is not None and scope_user is not None:
                templates_created = templates_created.filter(created_by=scope_user)
            templates_created = templates_created.annotate(
                period=trunc_func
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
            
            # Content uploads (from Content model)
            content_uploads = Content.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            if screen_ids is not None and scope_user is not None:
                content_uploads = content_uploads.filter(created_by=scope_user)
            content_uploads = content_uploads.annotate(
                period=trunc_func
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
            
            screen_registrations_list = list(screen_registrations)
            commands_created_list = list(commands_created)
            templates_created_list = list(templates_created)
            content_uploads_list = list(content_uploads)
            
            return {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'screen_registrations': [
                    {
                        'period': item.get('period').isoformat() if item.get('period') else None,
                        'count': item.get('count', 0),
                    }
                    for item in screen_registrations_list
                ],
                'commands_created': [
                    {
                        'period': item.get('period').isoformat() if item.get('period') else None,
                        'count': item.get('count', 0),
                    }
                    for item in commands_created_list
                ],
                'templates_created': [
                    {
                        'period': item.get('period').isoformat() if item.get('period') else None,
                        'count': item.get('count', 0),
                    }
                    for item in templates_created_list
                ],
                'content_uploads': [
                    {
                        'period': item.get('period').isoformat() if item.get('period') else None,
                        'count': item.get('count', 0),
                    }
                    for item in content_uploads_list
                ],
            }
        except Exception as e:
            logger.error(f"Error in get_activity_trends: {str(e)}", exc_info=True)
            raise
