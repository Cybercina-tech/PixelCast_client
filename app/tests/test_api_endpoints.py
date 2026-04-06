"""
Integration tests for all API endpoints.
"""
import json
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from tests.base import BaseAPITestCase
from io import BytesIO
from PIL import Image


class ScreenAPITests(BaseAPITestCase):
    """Tests for Screen API endpoints."""
    
    def test_list_screens(self):
        """Test listing screens."""
        self.create_screen(name='Screen 1')
        self.create_screen(name='Screen 2')
        
        url = reverse('screen-list')
        response = self.client.get(url)
        
        self.assertResponseSuccess(response)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_screen(self):
        """Test creating a screen."""
        url = reverse('screen-list')
        data = {
            'name': 'New Screen',
            'device_id': 'new-device-001',
            'location': 'New Location'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response, status_code=201)
        self.assertEqual(response.data['name'], 'New Screen')
    
    def test_get_screen_detail(self):
        """Test getting screen details."""
        screen = self.create_screen()
        url = reverse('screen-detail', kwargs={'id': str(screen.id)})
        
        response = self.client.get(url)
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['name'], screen.name)
    
    def test_update_screen(self):
        """Test updating a screen."""
        screen = self.create_screen()
        url = reverse('screen-detail', kwargs={'id': str(screen.id)})
        data = {'name': 'Updated Screen'}
        
        response = self.client.patch(url, data, format='json')
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['name'], 'Updated Screen')
    
    def test_delete_screen(self):
        """Test deleting a screen."""
        screen = self.create_screen()
        url = reverse('screen-detail', kwargs={'id': str(screen.id)})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
    
    def test_screen_heartbeat(self):
        """Test screen heartbeat endpoint."""
        screen = self.create_screen()
        url = reverse('screen-heartbeat', kwargs={'id': str(screen.id)})
        data = {
            'auth_token': screen.auth_token,
            'secret_key': screen.secret_key,
            'latency': 50,
            'cpu_usage': 30.5
        }
        
        response = self.client.post(url, data, format='json')
        self.assertResponseSuccess(response)


class TemplateAPITests(BaseAPITestCase):
    """Tests for Template API endpoints."""
    
    def test_list_templates(self):
        """Test listing templates."""
        self.create_template(name='Template 1')
        self.create_template(name='Template 2')
        
        url = reverse('template-list')
        response = self.client.get(url)
        
        self.assertResponseSuccess(response)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_template(self):
        """Test creating a template."""
        url = reverse('template-list')
        data = {
            'name': 'New Template',
            'width': 1920,
            'height': 1080,
            'orientation': 'landscape'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response, status_code=201)
        self.assertEqual(response.data['name'], 'New Template')
    
    def test_get_template_detail(self):
        """Test getting template details."""
        template = self.create_template()
        url = reverse('template-detail', kwargs={'id': str(template.id)})
        
        response = self.client.get(url)
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['name'], template.name)
    
    def test_update_template(self):
        """Test updating a template."""
        template = self.create_template()
        url = reverse('template-detail', kwargs={'id': str(template.id)})
        data = {'name': 'Updated Template'}
        
        response = self.client.patch(url, data, format='json')
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['name'], 'Updated Template')
    
    def test_delete_template(self):
        """Test deleting a template."""
        template = self.create_template()
        url = reverse('template-detail', kwargs={'id': str(template.id)})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
    
    def test_activate_template_on_screen(self):
        """Test activating template on screen."""
        template = self.create_template()
        screen = self.create_screen()
        
        url = reverse('template-activate-on-screen', kwargs={'id': str(template.id)})
        data = {'screen_id': str(screen.id), 'sync_content': False}
        
        response = self.client.post(url, data, format='json')
        self.assertResponseSuccess(response)


class ContentAPITests(BaseAPITestCase):
    """Tests for Content API endpoints."""
    
    def test_list_contents(self):
        """Test listing contents."""
        self.create_content(name='Content 1')
        self.create_content(name='Content 2')
        
        url = reverse('content-list')
        response = self.client.get(url)
        
        self.assertResponseSuccess(response)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_contents_library_only_returns_standalone_uploads(self):
        """Media library lists only rows with no widget (not template/widget-bound)."""
        from templates.models import Content

        self.create_content(name='Widget bound')
        Content.objects.create(name='Library upload', type='image', widget=None)

        url = reverse('content-list')
        response = self.client.get(url, {'library_only': '1'})
        self.assertResponseSuccess(response)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Library upload')
        self.assertIsNone(response.data['results'][0].get('widget'))
    
    def test_create_content(self):
        """Test creating content."""
        template = self.create_template()
        from templates.models import Layer, Widget
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
        
        url = reverse('content-list')
        data = {
            'name': 'New Content',
            'type': 'text',
            'widget': str(widget.id),
            'content_json': {'text': 'Hello World'}
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response, status_code=201)
        self.assertEqual(response.data['name'], 'New Content')
    
    def test_upload_content_file(self):
        """Test uploading content file."""
        content = self.create_content(type='image')
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        img_file = BytesIO()
        img.save(img_file, format='JPEG')
        img_file.name = 'test.jpg'
        img_file.seek(0)
        
        url = reverse('content-upload', kwargs={'id': str(content.id)})
        response = self.client.post(url, {'file': img_file}, format='multipart')
        
        self.assertResponseSuccess(response)
    
    def test_get_content_detail(self):
        """Test getting content details."""
        content = self.create_content()
        url = reverse('content-detail', kwargs={'id': str(content.id)})
        
        response = self.client.get(url)
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['name'], content.name)


class ScheduleAPITests(BaseAPITestCase):
    """Tests for Schedule API endpoints."""
    
    def test_list_schedules(self):
        """Test listing schedules."""
        self.create_schedule(name='Schedule 1')
        self.create_schedule(name='Schedule 2')
        
        url = reverse('schedule-list')
        response = self.client.get(url)
        
        self.assertResponseSuccess(response)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_schedule(self):
        """Test creating a schedule."""
        template = self.create_template()
        
        url = reverse('schedule-list')
        data = {
            'name': 'New Schedule',
            'template': str(template.id),
            'start_time': timezone.now().isoformat(),
            'end_time': (timezone.now() + timedelta(hours=1)).isoformat(),
            'repeat_type': 'none'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response, status_code=201)
        self.assertEqual(response.data['name'], 'New Schedule')
    
    def test_execute_schedule(self):
        """Test executing a schedule."""
        schedule = self.create_schedule()
        
        url = reverse('schedule-execute', kwargs={'id': str(schedule.id)})
        data = {'force': True}
        
        response = self.client.post(url, data, format='json')
        self.assertResponseSuccess(response)


class CommandAPITests(BaseAPITestCase):
    """Tests for Command API endpoints."""
    
    def test_list_commands(self):
        """Test listing commands."""
        self.create_command(name='Command 1')
        self.create_command(name='Command 2')
        
        url = reverse('command-list')
        response = self.client.get(url)
        
        self.assertResponseSuccess(response)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_command(self):
        """Test creating a command."""
        screen = self.create_screen()
        
        url = reverse('command-list')
        data = {
            'name': 'New Command',
            'type': 'restart',
            'screen_id': str(screen.id),
            'payload': {}
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response, status_code=201)
        self.assertEqual(response.data['name'], 'New Command')
    
    def test_execute_command(self):
        """Test executing a command."""
        command = self.create_command()
        
        url = reverse('command-execute', kwargs={'id': str(command.id)})
        response = self.client.post(url, {}, format='json')
        
        # May succeed or fail depending on screen online status
        self.assertIn(response.status_code, [200, 400])
    
    def test_retry_command(self):
        """Test retrying a command."""
        command = self.create_command(status='failed')
        command.attempt_count = 1
        command.save()
        
        url = reverse('command-retry', kwargs={'id': str(command.id)})
        response = self.client.post(url, {}, format='json')
        
        self.assertIn(response.status_code, [200, 400])


class AuthenticationTests(BaseAPITestCase):
    """Tests for authentication and authorization."""
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied."""
        self.client.logout()
        
        url = reverse('screen-list')
        response = self.client.get(url)
        
        self.assertUnauthorized(response)
    
    def test_jwt_authentication(self):
        """Test JWT token authentication."""
        token = self.get_jwt_token()
        self.client.force_authenticate(user=None)
        self.authenticate_with_token(token)
        
        url = reverse('screen-list')
        response = self.client.get(url)
        
        self.assertResponseSuccess(response)
    
    def test_role_based_access(self):
        """Test role-based access control."""
        employee = self.create_user(role='Employee')
        self.client.force_authenticate(user=employee)

        url = reverse('screen-list')
        data = {'name': 'Test', 'device_id': 'test-001'}
        response = self.client.post(url, data, format='json')

        self.assertIn(response.status_code, [201, 400])
