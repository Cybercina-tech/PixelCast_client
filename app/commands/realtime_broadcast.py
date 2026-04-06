"""
Real-time broadcasting utilities for WebSocket events.

Provides functions to broadcast command and content sync events
to connected dashboard users and screens.
"""
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

logger = logging.getLogger(__name__)


def broadcast_command_created(command):
    """
    Broadcast command creation event to dashboard users.
    
    Args:
        command: Command instance
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not configured, cannot broadcast command_created")
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'command_status_update',
                'data': {
                    'command_id': str(command.id),
                    'screen_id': str(command.screen.id),
                    'screen_name': command.screen.name,
                    'command_type': command.type,
                    'command_name': command.name,
                    'status': command.status,
                    'priority': command.priority,
                    'created_at': command.created_at.isoformat() if command.created_at else None,
                    'created_by': str(command.created_by.id) if command.created_by else None,
                    'timestamp': timezone.now().isoformat(),
                    'event_type': 'command_created'
                }
            }
        )
        logger.debug(f"Broadcasted command_created event for command {command.id}")
    except Exception as e:
        logger.error(f"Error broadcasting command_created: {str(e)}", exc_info=True)


def broadcast_command_status_update(command, status, progress=None, message=None):
    """
    Broadcast command status update to dashboard users.
    
    Args:
        command: Command instance
        status: New status ('pending', 'executing', 'done', 'failed')
        progress: Optional progress percentage (0-100)
        message: Optional status message
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'command_status_update',
                'data': {
                    'command_id': str(command.id),
                    'screen_id': str(command.screen.id),
                    'screen_name': command.screen.name,
                    'command_type': command.type,
                    'status': status,
                    'progress': progress,
                    'message': message,
                    'error_message': command.error_message if status == 'failed' else None,
                    'completed_at': command.completed_at.isoformat() if command.completed_at else None,
                    'timestamp': timezone.now().isoformat(),
                    'event_type': 'command_status_update'
                }
            }
        )
        logger.debug(f"Broadcasted command_status_update for command {command.id}: {status}")
    except Exception as e:
        logger.error(f"Error broadcasting command_status_update: {str(e)}", exc_info=True)


def broadcast_content_sync_started(screen_id, template_id, content_id=None):
    """
    Broadcast content sync started event.
    
    Args:
        screen_id: Screen UUID string
        template_id: Template UUID string
        content_id: Optional content UUID string
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'content_sync_progress',
                'data': {
                    'screen_id': str(screen_id),
                    'template_id': str(template_id),
                    'content_id': str(content_id) if content_id else None,
                    'status': 'started',
                    'progress': 0,
                    'timestamp': timezone.now().isoformat(),
                    'event_type': 'content_sync_started'
                }
            }
        )
        logger.debug(f"Broadcasted content_sync_started for screen {screen_id}")
    except Exception as e:
        logger.error(f"Error broadcasting content_sync_started: {str(e)}", exc_info=True)


def broadcast_content_sync_progress(screen_id, template_id, content_id, progress, status='downloading'):
    """
    Broadcast content sync progress update.
    
    Args:
        screen_id: Screen UUID string
        template_id: Template UUID string
        content_id: Content UUID string
        progress: Progress percentage (0-100)
        status: Status ('downloading', 'completed', 'failed')
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'content_sync_progress',
                'data': {
                    'screen_id': str(screen_id),
                    'template_id': str(template_id),
                    'content_id': str(content_id),
                    'status': status,
                    'progress': progress,
                    'timestamp': timezone.now().isoformat(),
                    'event_type': 'content_download_progress'
                }
            }
        )
        logger.debug(f"Broadcasted content_sync_progress for screen {screen_id}: {progress}%")
    except Exception as e:
        logger.error(f"Error broadcasting content_sync_progress: {str(e)}", exc_info=True)


def broadcast_content_sync_completed(screen_id, template_id, content_id=None):
    """
    Broadcast content sync completed event.
    
    Args:
        screen_id: Screen UUID string
        template_id: Template UUID string
        content_id: Optional content UUID string
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'content_sync_progress',
                'data': {
                    'screen_id': str(screen_id),
                    'template_id': str(template_id),
                    'content_id': str(content_id) if content_id else None,
                    'status': 'completed',
                    'progress': 100,
                    'timestamp': timezone.now().isoformat(),
                    'event_type': 'content_download_completed'
                }
            }
        )
        logger.debug(f"Broadcasted content_sync_completed for screen {screen_id}")
    except Exception as e:
        logger.error(f"Error broadcasting content_sync_completed: {str(e)}", exc_info=True)


def broadcast_content_sync_failed(screen_id, template_id, content_id, error_message):
    """
    Broadcast content sync failed event.
    
    Args:
        screen_id: Screen UUID string
        template_id: Template UUID string
        content_id: Content UUID string
        error_message: Error message
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'content_sync_progress',
                'data': {
                    'screen_id': str(screen_id),
                    'template_id': str(template_id),
                    'content_id': str(content_id),
                    'status': 'failed',
                    'progress': 0,
                    'error_message': error_message,
                    'timestamp': timezone.now().isoformat(),
                    'event_type': 'content_download_failed'
                }
            }
        )
        logger.debug(f"Broadcasted content_sync_failed for screen {screen_id}")
    except Exception as e:
        logger.error(f"Error broadcasting content_sync_failed: {str(e)}", exc_info=True)
