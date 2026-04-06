"""
Mocking utilities for external services.

Provides mocks for S3 storage, WebSocket connections, notification services, etc.
"""
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO


class MockStorage:
    """Mock storage backend for testing."""
    
    def __init__(self):
        self.files = {}
    
    def save(self, name, content):
        """Mock save operation."""
        self.files[name] = content.read() if hasattr(content, 'read') else content
        return name
    
    def open(self, name, mode='rb'):
        """Mock open operation."""
        if name in self.files:
            return BytesIO(self.files[name])
        raise FileNotFoundError(f"File {name} not found")
    
    def exists(self, name):
        """Mock exists check."""
        return name in self.files
    
    def delete(self, name):
        """Mock delete operation."""
        if name in self.files:
            del self.files[name]
            return True
        return False
    
    def url(self, name):
        """Mock URL generation."""
        return f"/media/{name}"


class MockWebSocketConnection:
    """Mock WebSocket connection for testing."""
    
    def __init__(self, screen_id):
        self.screen_id = screen_id
        self.connected = True
        self.messages = []
    
    def send(self, message):
        """Mock send message."""
        self.messages.append(message)
        return True
    
    def close(self):
        """Mock close connection."""
        self.connected = False


def mock_s3_storage(func):
    """Decorator to mock S3 storage."""
    def wrapper(*args, **kwargs):
        with patch('templates.storage.default_storage', new=MockStorage()):
            return func(*args, **kwargs)
    return wrapper


def mock_websocket_connection(func):
    """Decorator to mock WebSocket connections."""
    def wrapper(*args, **kwargs):
        with patch('commands.connection_registry.ScreenConnectionRegistry'):
            return func(*args, **kwargs)
    return wrapper


def mock_notification_service(func):
    """Decorator to mock notification service."""
    def wrapper(*args, **kwargs):
        with patch('notifications.dispatcher.NotificationDispatcher.send'):
            return func(*args, **kwargs)
    return wrapper
