"""
WebSocket consumer for screen communication.

Handles WebSocket connections from screens, authenticates them,
and manages command delivery and status updates.
"""
import json
import logging
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from signage.models import Screen
from commands.models import Command
from commands.connection_registry import ScreenConnectionRegistry
from commands.security import ScreenSecurity, SecurityError, InvalidSignatureError, TimestampExpiredError, ReplayAttackError
from log.models import CommandExecutionLog

logger = logging.getLogger(__name__)


class ScreenConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for screen connections.
    
    Handles:
    - Screen authentication during handshake
    - Command delivery
    - Execution status updates
    - Connection lifecycle management
    - Enhanced security (HMAC, rate limiting, nonce protection)
    """
    
    # Rate limiting constants
    MAX_CONNECTIONS_PER_SCREEN = 3
    MAX_MESSAGES_PER_MINUTE = 100
    SUSPICIOUS_BEHAVIOR_THRESHOLD = 10  # Disconnect after N suspicious messages
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.screen = None
        self.screen_id = None
        self.screen_group_name = None
        self.message_count = 0
        self.message_window_start = time.time()
        self.suspicious_count = 0
        self.client_ip = None
    
    async def connect(self):
        """
        Handle WebSocket connection.
        
        Authenticates screen using auth_token and secret_key from query params.
        Rejects connection if authentication fails.
        """
        # Get client IP for logging and rate limiting
        self.client_ip = self.scope.get('client', [None, None])[0]
        
        # Parse query string
        query_string = self.scope.get('query_string', b'').decode()
        query_params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        
        # Get authentication credentials from query string
        auth_token = query_params.get('auth_token')
        secret_key = query_params.get('secret_key')
        
        if not auth_token or not secret_key:
            logger.warning(f"WebSocket connection rejected: missing auth credentials from IP {self.client_ip}")
            await self.close(code=4001)  # Unauthorized
            return
        
        # Check connection rate limiting per IP
        if not await self.check_connection_rate_limit():
            logger.warning(f"WebSocket connection rejected: rate limit exceeded from IP {self.client_ip}")
            await self.close(code=4003)  # Rate limit exceeded
            return
        
        # Authenticate screen
        try:
            self.screen = await self.authenticate_screen(auth_token, secret_key)
            if not self.screen:
                logger.warning(f"WebSocket connection rejected: invalid credentials from IP {self.client_ip}")
                await self.close(code=4001)  # Unauthorized
                return
            
            self.screen_id = str(self.screen.id)
            self.screen_group_name = f'screen_{self.screen_id}'
            
            # Check concurrent connections per screen
            if not await self.check_concurrent_connections():
                logger.warning(f"WebSocket connection rejected: max connections exceeded for screen {self.screen_id}")
                await self.close(code=4004)  # Too many connections
                return
            
            # Update screen IP from connection
            if self.client_ip:
                await self.update_screen_ip(self.client_ip)
            
            # Accept connection
            await self.channel_layer.group_add(
                self.screen_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Register connection
            ScreenConnectionRegistry.register_connection(self.screen_id, self.channel_name)
            
            # Mark screen as online and broadcast
            await self.mark_screen_online()
            await self.broadcast_screen_status('online')
            
            logger.info(f"Screen {self.screen_id} connected via WebSocket from IP {self.client_ip}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {str(e)}", exc_info=True)
            await self.close(code=4002)  # Internal error
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        
        Cleans up connection registry and marks screen as offline.
        """
        if self.screen_id:
            # Decrement connection count
            await self.decrement_connection_count()
            
            # Unregister connection
            ScreenConnectionRegistry.unregister_connection(self.screen_id)
            
            # Remove from group
            await self.channel_layer.group_discard(
                self.screen_group_name,
                self.channel_name
            )
            
            # Mark screen as offline and broadcast
            await self.mark_screen_offline()
            await self.broadcast_screen_status('offline')
            
            logger.info(f"Screen {self.screen_id} disconnected (code: {close_code}) from IP {self.client_ip}")
    
    async def receive(self, text_data):
        """
        Handle messages received from screen.
        
        Expected message types:
        - command_ack: Acknowledgment of command receipt
        - command_status: Status update for command execution
        - command_status_update: Real-time status update (executing, progress, done, failed)
        - content_sync_progress: Content download progress
        - screen_health_update: Screen health metrics
        - heartbeat: Optional heartbeat message
        """
        # Check message rate limiting
        if not await self.check_message_rate_limit():
            logger.warning(f"Message rate limit exceeded for screen {self.screen_id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Rate limit exceeded'
            }))
            return
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Validate message schema
            if not await self.validate_message_schema(data, message_type):
                self.suspicious_count += 1
                if self.suspicious_count >= self.SUSPICIOUS_BEHAVIOR_THRESHOLD:
                    logger.error(f"Suspicious behavior detected for screen {self.screen_id}, disconnecting")
                    await self.close(code=4005)  # Suspicious behavior
                    return
                return
            
            # Validate HMAC signature for all messages
            if not await self.validate_message_signature(data):
                self.suspicious_count += 1
                logger.warning(f"Invalid signature from screen {self.screen_id}")
                if self.suspicious_count >= self.SUSPICIOUS_BEHAVIOR_THRESHOLD:
                    await self.close(code=4005)
                    return
                return
            
            # Reset suspicious count on valid message
            self.suspicious_count = 0
            
            # Route message to appropriate handler
            if message_type == 'command_ack':
                await self.handle_command_ack(data)
            elif message_type == 'command_status':
                await self.handle_command_status(data)
            elif message_type == 'command_status_update':
                await self.handle_command_status_update(data)
            elif message_type == 'content_sync_progress':
                await self.handle_content_sync_progress(data)
            elif message_type == 'screen_health_update':
                await self.handle_screen_health_update(data)
            elif message_type == 'heartbeat':
                await self.handle_heartbeat(data)
            else:
                logger.warning(f"Unknown message type from screen {self.screen_id}: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from screen {self.screen_id}")
            self.suspicious_count += 1
        except Exception as e:
            logger.error(f"Error processing message from screen {self.screen_id}: {str(e)}", exc_info=True)
    
    async def command_message(self, event):
        """
        Handle command message sent to this screen.
        
        This is called when a command is sent to the screen's group.
        """
        command_data = event['command']
        
        # Validate message signature if present
        if 'signature' in command_data and self.screen:
            try:
                await database_sync_to_async(self._validate_command_signature)(
                    command_data
                )
            except SecurityError as e:
                logger.error(f"Security validation failed for command to screen {self.screen_id}: {str(e)}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Security validation failed',
                    'error': str(e)
                }))
                return
        
        # Send command to screen
        await self.send(text_data=json.dumps({
            'type': 'command',
            'command': command_data
        }))
        
        logger.info(f"Command sent to screen {self.screen_id} via WebSocket")
    
    async def command_status_update(self, event):
        """
        Handle command status update broadcast.
        
        Broadcasts status updates to dashboard users.
        """
        await self.send(text_data=json.dumps({
            'type': 'command_status_update',
            'data': event['data']
        }))
    
    async def content_sync_progress(self, event):
        """
        Handle content sync progress broadcast.
        """
        await self.send(text_data=json.dumps({
            'type': 'content_sync_progress',
            'data': event['data']
        }))
    
    async def screen_health_update(self, event):
        """
        Handle screen health update broadcast.
        """
        await self.send(text_data=json.dumps({
            'type': 'screen_health_update',
            'data': event['data']
        }))
    
    def _validate_command_signature(self, command_data):
        """Validate command signature (sync method for database_sync_to_async)"""
        ScreenSecurity.validate_message(
            secret_key=self.screen.secret_key,
            screen_id=self.screen_id,
            payload=command_data.get('payload', {}),
            timestamp=command_data.get('timestamp'),
            nonce=command_data.get('nonce'),
            signature=command_data.get('signature')
        )
    
    async def validate_message_signature(self, data):
        """Validate HMAC signature for incoming messages"""
        if not self.screen:
            return False
        
        signature = data.get('signature')
        timestamp = data.get('timestamp')
        nonce = data.get('nonce')
        payload = data.get('payload', {})
        
        if not all([signature, timestamp, nonce]):
            return False
        
        try:
            await database_sync_to_async(ScreenSecurity.validate_message)(
                secret_key=self.screen.secret_key,
                screen_id=self.screen_id,
                payload=payload,
                timestamp=timestamp,
                nonce=nonce,
                signature=signature
            )
            return True
        except (InvalidSignatureError, TimestampExpiredError, ReplayAttackError) as e:
            logger.warning(f"Message validation failed for screen {self.screen_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating message: {str(e)}")
            return False
    
    async def validate_message_schema(self, data, message_type):
        """Validate message schema based on type"""
        required_fields = {
            'command_ack': ['command_id'],
            'command_status': ['command_id', 'status'],
            'command_status_update': ['command_id', 'status'],
            'content_sync_progress': ['screen_id', 'template_id', 'progress'],
            'screen_health_update': ['screen_id'],
            'heartbeat': []
        }
        
        required = required_fields.get(message_type, [])
        return all(field in data for field in required)
    
    async def check_connection_rate_limit(self):
        """Check connection rate limiting per IP"""
        if not self.client_ip:
            return True
        
        cache_key = f"ws_connection_rate:{self.client_ip}"
        count = cache.get(cache_key, 0)
        
        if count >= 10:  # Max 10 connections per minute per IP
            return False
        
        cache.set(cache_key, count + 1, 60)
        return True
    
    async def check_concurrent_connections(self):
        """Check max concurrent connections per screen"""
        cache_key = f"screen_connections:{self.screen_id}"
        count = cache.get(cache_key, 0)
        
        if count >= self.MAX_CONNECTIONS_PER_SCREEN:
            return False
        
        cache.set(cache_key, count + 1, 3600)  # 1 hour timeout
        return True
    
    async def check_message_rate_limit(self):
        """Check message rate limiting"""
        current_time = time.time()
        
        # Reset window if more than 1 minute has passed
        if current_time - self.message_window_start > 60:
            self.message_count = 0
            self.message_window_start = current_time
        
        if self.message_count >= self.MAX_MESSAGES_PER_MINUTE:
            return False
        
        self.message_count += 1
        return True
    
    async def broadcast_screen_status(self, status):
        """Broadcast screen online/offline status to dashboard users"""
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                'dashboard_updates',
                {
                    'type': 'screen_status_update',
                    'data': {
                        'screen_id': self.screen_id,
                        'screen_name': self.screen.name if self.screen else None,
                        'status': status,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
    
    async def handle_command_ack(self, data):
        """
        Handle command acknowledgment from screen.
        
        Updates command status and creates execution log.
        """
        command_id = data.get('command_id')
        if not command_id:
            return
        
        try:
            command = await database_sync_to_async(Command.objects.get)(id=command_id, screen=self.screen)
            
            # Update command status
            await database_sync_to_async(self.update_command_ack)(command)
            
            # Broadcast to dashboard
            await self.broadcast_command_update(command, 'acknowledged')
            
            logger.info(f"Command {command_id} acknowledged by screen {self.screen_id}")
            
        except ObjectDoesNotExist:
            logger.warning(f"Command {command_id} not found for screen {self.screen_id}")
        except Exception as e:
            logger.error(f"Error handling command ack: {str(e)}")
    
    async def handle_command_status(self, data):
        """
        Handle command execution status update from screen.
        
        Updates command and execution log with status, response, and errors.
        """
        command_id = data.get('command_id')
        status = data.get('status')  # 'done' or 'failed'
        response_payload = data.get('response_payload', {})
        error_message = data.get('error_message', '')
        
        if not command_id:
            return
        
        try:
            command = await database_sync_to_async(Command.objects.get)(id=command_id, screen=self.screen)
            
            # Update command and log
            await database_sync_to_async(self.update_command_status)(
                command, status, response_payload, error_message
            )
            
            # Broadcast to dashboard
            await self.broadcast_command_update(command, status)
            
            logger.info(f"Command {command_id} status updated to {status} by screen {self.screen_id}")
            
        except ObjectDoesNotExist:
            logger.warning(f"Command {command_id} not found for screen {self.screen_id}")
        except Exception as e:
            logger.error(f"Error handling command status: {str(e)}")
    
    async def handle_command_status_update(self, data):
        """
        Handle real-time command status update (executing, progress, etc.)
        
        This is for intermediate status updates during command execution.
        """
        command_id = data.get('command_id')
        status = data.get('status')  # 'executing', 'progress', etc.
        progress = data.get('progress', 0)
        message = data.get('message', '')
        
        if not command_id:
            return
        
        try:
            command = await database_sync_to_async(Command.objects.get)(id=command_id, screen=self.screen)
            
            # Update command status if executing
            if status == 'executing':
                command.status = 'executing'
                command.executed_at = timezone.now()
                await database_sync_to_async(command.save)(update_fields=['status', 'executed_at'])
            
            # Broadcast to dashboard
            await self.broadcast_command_update(command, status, progress=progress, message=message)
            
            logger.debug(f"Command {command_id} status update: {status} (progress: {progress}%)")
            
        except ObjectDoesNotExist:
            logger.warning(f"Command {command_id} not found for screen {self.screen_id}")
        except Exception as e:
            logger.error(f"Error handling command status update: {str(e)}")
    
    async def handle_content_sync_progress(self, data):
        """
        Handle content sync progress update from screen.
        
        Broadcasts progress to dashboard users.
        """
        screen_id = data.get('screen_id')
        template_id = data.get('template_id')
        content_id = data.get('content_id')
        progress = data.get('progress', 0)
        status = data.get('status', 'downloading')  # 'downloading', 'completed', 'failed'
        error_message = data.get('error_message', '')
        
        # Broadcast to dashboard
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                'dashboard_updates',
                {
                    'type': 'content_sync_progress',
                    'data': {
                        'screen_id': screen_id or self.screen_id,
                        'template_id': template_id,
                        'content_id': content_id,
                        'progress': progress,
                        'status': status,
                        'error_message': error_message,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
        
        logger.debug(f"Content sync progress for screen {self.screen_id}: {progress}%")
    
    async def handle_screen_health_update(self, data):
        """
        Handle screen health metrics update.
        
        Broadcasts health status to dashboard users.
        """
        health_data = {
            'screen_id': self.screen_id,
            'cpu_usage': data.get('cpu_usage'),
            'memory_usage': data.get('memory_usage'),
            'disk_usage': data.get('disk_usage'),
            'uptime': data.get('uptime'),
            'timestamp': timezone.now().isoformat()
        }
        
        # Broadcast to dashboard
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                'dashboard_updates',
                {
                    'type': 'screen_health_update',
                    'data': health_data
                }
            )
    
    async def handle_heartbeat(self, data):
        """
        Handle heartbeat message from screen.
        
        Updates screen's last heartbeat timestamp.
        """
        if self.screen:
            await database_sync_to_async(self.update_heartbeat)(data)
    
    async def broadcast_command_update(self, command, status, progress=None, message=None):
        """Broadcast command update to dashboard users"""
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
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
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
    
    @database_sync_to_async
    def authenticate_screen(self, auth_token, secret_key):
        """Authenticate screen using credentials"""
        try:
            screen = Screen.objects.get(auth_token=auth_token)
            if screen.authenticate(auth_token, secret_key):
                return screen
        except ObjectDoesNotExist:
            pass
        return None
    
    @database_sync_to_async
    def update_screen_ip(self, ip_address):
        """Update screen's last IP address"""
        if self.screen:
            self.screen.last_ip = ip_address
            self.screen.save(update_fields=['last_ip'])
    
    @database_sync_to_async
    def mark_screen_online(self):
        """Mark screen as online"""
        if self.screen:
            self.screen.is_online = True
            self.screen.save(update_fields=['is_online'])
    
    @database_sync_to_async
    def mark_screen_offline(self):
        """Mark screen as offline"""
        if self.screen:
            self.screen.is_online = False
            self.screen.save(update_fields=['is_online'])
    
    @database_sync_to_async
    def update_command_ack(self, command):
        """Update command acknowledgment"""
        command.last_command_received_at = timezone.now()
        command.save(update_fields=['last_command_received_at'])
        
        # Create or update execution log
        exec_log, created = CommandExecutionLog.objects.get_or_create(
            command=command,
            screen=self.screen,
            defaults={
                'status': 'running',
                'started_at': timezone.now()
            }
        )
        if not created:
            exec_log.status = 'running'
            exec_log.started_at = timezone.now()
            exec_log.save(update_fields=['status', 'started_at'])
    
    @database_sync_to_async
    def update_command_status(self, command, status, response_payload, error_message):
        """Update command execution status"""
        if status == 'done':
            command.mark_done()
        else:
            command.mark_failed(error_message)
        
        # Update execution log
        exec_log = CommandExecutionLog.objects.filter(
            command=command,
            screen=self.screen
        ).order_by('-created_at').first()
        
        if exec_log:
            exec_log.status = status
            exec_log.finished_at = timezone.now()
            exec_log.response_payload = response_payload
            if error_message:
                exec_log.error_message = error_message
            exec_log.save(update_fields=['status', 'finished_at', 'response_payload', 'error_message'])
    
    async def decrement_connection_count(self):
        """Decrement connection count for this screen"""
        if self.screen_id:
            cache_key = f"screen_connections:{self.screen_id}"
            count = cache.get(cache_key, 0)
            if count > 0:
                cache.set(cache_key, count - 1, 3600)
    
    @database_sync_to_async
    def update_heartbeat(self, data):
        """Update screen heartbeat"""
        if self.screen:
            latency = data.get('latency')
            cpu_usage = data.get('cpu_usage')
            memory_usage = data.get('memory_usage')
            self.screen.update_heartbeat(
                latency=latency,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                ip_address=self.client_ip
            )
