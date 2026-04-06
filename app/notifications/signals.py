"""
Django signals for notification event triggers.

Integrates with existing PixelCast Signage systems to emit notification events.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .dispatcher import NotificationDispatcher
from .models import NotificationEvent

logger = logging.getLogger(__name__)


# Screen offline detection
@receiver(post_save, sender='signage.Screen')
def screen_status_changed(sender, instance, created, **kwargs):
    """Emit notification when screen goes offline"""
    if created:
        return
    
    # Check if screen went offline
    if not instance.is_online:
        # Check last heartbeat
        if instance.last_heartbeat_at:
            offline_duration = timezone.now() - instance.last_heartbeat_at
            # Emit notification if offline for more than 5 minutes
            if offline_duration > timedelta(minutes=5):
                try:
                    NotificationDispatcher.dispatch(
                        event_key='screen.offline',
                        payload={
                            'screen_id': str(instance.id),
                            'screen_name': instance.name,
                            'offline_duration_seconds': int(offline_duration.total_seconds()),
                            'last_heartbeat_at': instance.last_heartbeat_at.isoformat() if instance.last_heartbeat_at else None,
                            'last_ip': instance.last_ip
                        },
                        organization=instance.owner,
                        severity='warning'
                    )
                except Exception as e:
                    logger.error(f"Error dispatching screen.offline notification: {str(e)}")


# Command execution failure
@receiver(post_save, sender='commands.Command')
def command_status_changed(sender, instance, created, **kwargs):
    """Emit notification when command execution fails"""
    if created:
        return
    
    # Check if command failed
    if instance.status == 'failed':
        try:
            # Check if event exists and is active before dispatching
            from notifications.models import NotificationEvent
            try:
                event = NotificationEvent.objects.get(event_key='command.failed', is_active=True)
            except NotificationEvent.DoesNotExist:
                # Event not configured, skip notification (not an error)
                logger.debug(f"Notification event 'command.failed' not found or inactive, skipping notification")
                return
            
            NotificationDispatcher.dispatch(
                event_key='command.failed',
                payload={
                    'command_id': str(instance.id),
                    'command_type': instance.type,
                    'screen_id': str(instance.screen.id) if instance.screen else None,
                    'screen_name': instance.screen.name if instance.screen else None,
                    'error_message': instance.error_message,
                    'attempt_count': instance.attempt_count
                },
                organization=instance.created_by,
                severity='warning'
            )
        except Exception as e:
            logger.error(f"Error dispatching command.failed notification: {str(e)}")


# Content sync failure (triggered from Content model)
def emit_content_sync_failed(content, screen, error_message):
    """Emit notification when content sync fails"""
    try:
        NotificationDispatcher.dispatch(
            event_key='content.sync_failed',
            payload={
                'content_id': str(content.id),
                'content_name': content.name,
                'screen_id': str(screen.id),
                'screen_name': screen.name,
                'error_message': error_message,
                'retry_count': content.retry_count
            },
            organization=screen.owner if hasattr(screen, 'owner') else None,
            severity='warning'
        )
    except Exception as e:
        logger.error(f"Error dispatching content.sync_failed notification: {str(e)}")


# Schedule execution failure (triggered from Schedule model)
def emit_schedule_execution_failed(schedule, error_message):
    """Emit notification when schedule execution fails"""
    try:
        NotificationDispatcher.dispatch(
            event_key='schedule.execution_failed',
            payload={
                'schedule_id': str(schedule.id),
                'schedule_name': schedule.name,
                'template_id': str(schedule.template.id),
                'template_name': schedule.template.name,
                'error_message': error_message
            },
            organization=schedule.template.created_by if hasattr(schedule.template, 'created_by') else None,
            severity='warning'
        )
    except Exception as e:
        logger.error(f"Error dispatching schedule.execution_failed notification: {str(e)}")


# Security anomaly (triggered from security modules)
def emit_security_anomaly(anomaly_type: str, details: dict, severity: str = 'critical'):
    """
    Emit notification for security anomalies.
    
    Args:
        anomaly_type: Type of anomaly (rate_limit_breach, invalid_signature, replay_attempt)
        details: Anomaly details
        severity: Severity level (default: critical)
    """
    try:
        NotificationDispatcher.dispatch(
            event_key=f'security.{anomaly_type}',
            payload=details,
            severity=severity
        )
    except Exception as e:
        logger.error(f"Error dispatching security.{anomaly_type} notification: {str(e)}")

