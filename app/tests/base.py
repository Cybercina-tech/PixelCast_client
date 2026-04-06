"""
Base test classes and utilities for PixelCast Signage tests.
"""
import json
import uuid
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase
from django.utils import timezone
from datetime import timedelta
from io import BytesIO
from PIL import Image

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with common utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = self.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='Manager',
            organization_name='TestOrg'
        )
        self.client.force_authenticate(user=self.user)
    
    def create_user(self, **kwargs):
        """Create a test user."""
        defaults = {
            'is_active': True,
            'role': 'Manager',
        }
        defaults.update(kwargs)
        if 'username' not in defaults:
            defaults['username'] = f'user_{uuid.uuid4().hex[:12]}'
        if 'email' not in defaults:
            defaults['email'] = f'{defaults["username"]}@test.local'
        password = defaults.pop('password', 'testpass123')
        user = User.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        return user
    
    def create_screen(self, **kwargs):
        """Create a test screen."""
        from signage.models import Screen
        defaults = {
            'name': 'Test Screen',
            'device_id': f'dev-{uuid.uuid4().hex[:20]}',
            'owner': self.user,
            'is_online': True,
        }
        defaults.update(kwargs)
        return Screen.objects.create(**defaults)
    
    def create_template(self, **kwargs):
        """Create a test template."""
        from templates.models import Template
        defaults = {
            'name': 'Test Template',
            'width': 1920,
            'height': 1080,
            'created_by': self.user,
            'is_active': True,
        }
        defaults.update(kwargs)
        return Template.objects.create(**defaults)
    
    def create_content(self, template=None, **kwargs):
        """Create a test content."""
        from templates.models import Layer, Widget, Content
        if template is None:
            template = self.create_template()
        layer = Layer.objects.create(
            name='Test Layer',
            template=template,
            width=1920,
            height=1080
        )
        widget = Widget.objects.create(
            name='Test Widget',
            type='text',
            layer=layer
        )
        defaults = {
            'name': 'Test Content',
            'type': 'text',
            'widget': widget,
        }
        defaults.update(kwargs)
        return Content.objects.create(**defaults)
    
    def create_schedule(self, template=None, screen=None, **kwargs):
        """Create a test schedule."""
        from templates.models import Schedule
        if template is None:
            template = self.create_template()
        if screen is None:
            screen = self.create_screen()
        
        defaults = {
            'name': 'Test Schedule',
            'template': template,
            'start_time': timezone.now(),
            'end_time': timezone.now() + timedelta(hours=1),
            'is_active': True,
        }
        defaults.update(kwargs)
        schedule = Schedule.objects.create(**defaults)
        schedule.screens.add(screen)
        return schedule
    
    def create_command(self, screen=None, **kwargs):
        """Create a test command."""
        from commands.models import Command
        if screen is None:
            screen = self.create_screen()
        
        defaults = {
            'name': 'Test Command',
            'type': 'refresh',
            'screen': screen,
            'created_by': self.user,
            'status': 'pending',
        }
        defaults.update(kwargs)
        return Command.objects.create(**defaults)
    
    def create_image_file(self, filename='test.jpg', size=(100, 100), format='JPEG'):
        """Create a test image file."""
        img = Image.new('RGB', size, color='red')
        file = BytesIO()
        img.save(file, format=format)
        file.name = filename
        file.seek(0)
        return file
    
    def assertResponseSuccess(self, response, status_code=200):
        """Assert response is successful."""
        self.assertEqual(response.status_code, status_code)
    
    def assertResponseError(self, response, status_code=400):
        """Assert response is an error."""
        self.assertEqual(response.status_code, status_code)


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication."""
    
    def setUp(self):
        """Set up API test fixtures."""
        cache.clear()
        super().setUp()
        self.user = self.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='Manager',
            organization_name='TestOrg'
        )
        self.client.force_authenticate(user=self.user)
    
    def create_user(self, **kwargs):
        """Create a test user."""
        defaults = {
            'is_active': True,
            'role': 'Manager',
        }
        defaults.update(kwargs)
        if 'username' not in defaults:
            defaults['username'] = f'user_{uuid.uuid4().hex[:12]}'
        if 'email' not in defaults:
            defaults['email'] = f'{defaults["username"]}@test.local'
        password = defaults.pop('password', 'testpass123')
        user = User.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        return user
    
    def get_jwt_token(self, username='testuser', password='testpass123'):
        """Get JWT token for a user."""
        from accounts.tokens import ScreenGramRefreshToken
        user = User.objects.get(username=username)
        refresh = ScreenGramRefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_with_token(self, token):
        """Authenticate client with JWT token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def create_screen(self, **kwargs):
        """Create a test screen."""
        from signage.models import Screen
        defaults = {
            'name': 'Test Screen',
            'device_id': f'dev-{uuid.uuid4().hex[:20]}',
            'owner': self.user,
            'is_online': True,
        }
        defaults.update(kwargs)
        return Screen.objects.create(**defaults)
    
    def create_template(self, **kwargs):
        """Create a test template."""
        from templates.models import Template
        defaults = {
            'name': 'Test Template',
            'width': 1920,
            'height': 1080,
            'created_by': self.user,
            'is_active': True,
        }
        defaults.update(kwargs)
        return Template.objects.create(**defaults)
    
    def create_content(self, template=None, **kwargs):
        """Create test content linked to a widget (same shape as BaseTestCase)."""
        from templates.models import Layer, Widget, Content
        if template is None:
            template = self.create_template()
        layer = Layer.objects.create(
            name='Test Layer',
            template=template,
            width=1920,
            height=1080,
        )
        widget = Widget.objects.create(
            name='Test Widget',
            type='text',
            layer=layer,
        )
        defaults = {
            'name': 'Test Content',
            'type': 'text',
            'widget': widget,
        }
        defaults.update(kwargs)
        return Content.objects.create(**defaults)
    
    def create_schedule(self, template=None, screen=None, **kwargs):
        """Create a test schedule."""
        from templates.models import Schedule
        if template is None:
            template = self.create_template()
        if screen is None:
            screen = self.create_screen()
        defaults = {
            'name': 'Test Schedule',
            'template': template,
            'start_time': timezone.now(),
            'end_time': timezone.now() + timedelta(hours=1),
            'is_active': True,
        }
        defaults.update(kwargs)
        schedule = Schedule.objects.create(**defaults)
        schedule.screens.add(screen)
        return schedule
    
    def create_command(self, screen=None, **kwargs):
        """Create a test command."""
        from commands.models import Command
        if screen is None:
            screen = self.create_screen()
        defaults = {
            'name': 'Test Command',
            'type': 'refresh',
            'screen': screen,
            'created_by': self.user,
            'status': 'pending',
        }
        defaults.update(kwargs)
        return Command.objects.create(**defaults)
    
    def assertResponseSuccess(self, response, status_code=200):
        """Assert response is successful."""
        self.assertEqual(response.status_code, status_code)
    
    def assertResponseError(self, response, status_code=400):
        """Assert response is an error."""
        self.assertEqual(response.status_code, status_code)
    
    def assertPermissionDenied(self, response):
        """Assert permission denied response."""
        self.assertEqual(response.status_code, 403)
    
    def assertUnauthorized(self, response):
        """Assert unauthorized response."""
        self.assertEqual(response.status_code, 401)
