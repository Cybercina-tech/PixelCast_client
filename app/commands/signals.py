"""
Django signals for command model events.

Broadcasts real-time WebSocket events when commands are created or updated.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Command
from .realtime_broadcast import broadcast_command_created, broadcast_command_status_update

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Command)
def command_saved(sender, instance, created, **kwargs):
    """
    Signal handler for command save events.
    
    Broadcasts:
    - command_created when a new command is created
    - command_status_update when command status changes
    """
    try:
        if created:
            # New command created
            broadcast_command_created(instance)
            logger.debug(f"Broadcasted command_created for command {instance.id}")
        else:
            # Command updated - check if status changed
            if 'status' in kwargs.get('update_fields', []):
                broadcast_command_status_update(
                    instance,
                    instance.status,
                    progress=None,
                    message=None
                )
                logger.debug(f"Broadcasted command_status_update for command {instance.id}: {instance.status}")
    except Exception as e:
        logger.error(f"Error in command_saved signal: {str(e)}", exc_info=True)


@receiver(post_delete, sender=Command)
def command_deleted(sender, instance, **kwargs):
    """
    Signal handler for command deletion.
    
    Note: Commands are rarely deleted, but we log it for audit purposes.
    """
    try:
        logger.info(f"Command {instance.id} deleted")
        # Optionally broadcast deletion event if needed
    except Exception as e:
        logger.error(f"Error in command_deleted signal: {str(e)}", exc_info=True)
