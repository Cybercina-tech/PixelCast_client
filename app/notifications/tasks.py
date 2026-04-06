"""
Celery tasks for async notification delivery.
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import NotificationLog, NotificationChannel, NotificationEvent
from .adapters import get_channel_adapter

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_async(
    self,
    log_entry_id: str,
    channel_id: str,
    event_key: str,
    payload: dict,
    severity: str
):
    """
    Async task to send notification via channel adapter.
    
    Args:
        log_entry_id: NotificationLog entry ID
        channel_id: NotificationChannel ID
        event_key: Event key
        payload: Event payload
        severity: Event severity
    """
    try:
        # Get objects
        log_entry = NotificationLog.objects.get(id=log_entry_id)
        channel = NotificationChannel.objects.get(id=channel_id)
        event = NotificationEvent.objects.get(event_key=event_key)
        
        # Get adapter
        adapter = get_channel_adapter(channel.type)
        
        # Send notification
        result = adapter.send(log_entry, channel, event, payload, severity)
        
        # Update log entry
        log_entry.status = 'sent' if result['success'] else 'failed'
        log_entry.provider_response = adapter._sanitize_response(result.get('response', ''))
        log_entry.error_message = result.get('error', '')
        log_entry.retry_count = self.request.retries
        
        if result['success']:
            log_entry.sent_at = timezone.now()
        
        log_entry.save()
        
        return {
            'success': result['success'],
            'log_entry_id': log_entry_id
        }
        
    except NotificationLog.DoesNotExist:
        logger.error(f"NotificationLog {log_entry_id} not found")
        return {'success': False, 'error': 'Log entry not found'}
    
    except NotificationChannel.DoesNotExist:
        logger.error(f"NotificationChannel {channel_id} not found")
        return {'success': False, 'error': 'Channel not found'}
    
    except NotificationEvent.DoesNotExist:
        logger.error(f"NotificationEvent {event_key} not found")
        return {'success': False, 'error': 'Event not found'}
    
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}", exc_info=True)
        
        # Update log entry with error
        try:
            log_entry = NotificationLog.objects.get(id=log_entry_id)
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.retry_count = self.request.retries
            log_entry.save()
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

