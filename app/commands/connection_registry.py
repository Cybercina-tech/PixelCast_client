"""
Connection registry for tracking active screen WebSocket connections.

Maintains a mapping between screen_id and channel_name for efficient
command delivery via WebSocket.
"""
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


class ScreenConnectionRegistry:
    """
    Registry for tracking active screen WebSocket connections.
    
    Uses Django cache to store connection mappings.
    Thread-safe and supports multiple ASGI workers.
    """
    
    CACHE_PREFIX = "screen_connection:"
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def register_connection(screen_id, channel_name):
        """
        Register a screen WebSocket connection.
        
        Args:
            screen_id: Screen UUID string
            channel_name: WebSocket channel name
        """
        cache_key = f"{ScreenConnectionRegistry.CACHE_PREFIX}{screen_id}"
        cache.set(cache_key, channel_name, ScreenConnectionRegistry.CACHE_TIMEOUT)
        logger.info(f"Registered WebSocket connection for screen {screen_id}: {channel_name}")
    
    @staticmethod
    def unregister_connection(screen_id):
        """
        Unregister a screen WebSocket connection.
        
        Args:
            screen_id: Screen UUID string
        """
        cache_key = f"{ScreenConnectionRegistry.CACHE_PREFIX}{screen_id}"
        cache.delete(cache_key)
        logger.info(f"Unregistered WebSocket connection for screen {screen_id}")
    
    @staticmethod
    def get_connection(screen_id):
        """
        Get channel name for a screen.
        
        Args:
            screen_id: Screen UUID string
            
        Returns:
            str: Channel name if connected, None otherwise
        """
        cache_key = f"{ScreenConnectionRegistry.CACHE_PREFIX}{screen_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def is_connected(screen_id):
        """
        Check if screen has active WebSocket connection.
        
        Args:
            screen_id: Screen UUID string
            
        Returns:
            bool: True if connected
        """
        return ScreenConnectionRegistry.get_connection(screen_id) is not None
    
    @staticmethod
    def send_command_to_screen(screen_id, command_data):
        """
        Send command to screen via WebSocket using group messaging.
        
        Args:
            screen_id: Screen UUID string
            command_data: Command data dict to send
            
        Returns:
            bool: True if sent successfully, False if screen not connected
        """
        if not ScreenConnectionRegistry.is_connected(screen_id):
            logger.warning(f"Screen {screen_id} is not connected via WebSocket")
            return False
        
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                # Send to screen's group (each screen has its own group)
                group_name = f'screen_{screen_id}'
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'command_message',
                        'command': command_data
                    }
                )
                logger.info(f"Sent command to screen {screen_id} via WebSocket group {group_name}")
                return True
            else:
                logger.error("Channel layer not configured")
                return False
        except Exception as e:
            logger.error(f"Error sending command to screen {screen_id}: {str(e)}")
            return False

