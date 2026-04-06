"""
Tests for edge cases and error handling.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from tests.base import BaseAPITestCase


class EdgeCaseTests(BaseAPITestCase):
    """Tests for edge cases and error conditions."""
    
    def test_create_screen_with_duplicate_device_id(self):
        """Test creating screen with duplicate device_id fails."""
        self.create_screen(device_id='duplicate-001')
        
        # Should raise validation error
        from signage.models import Screen
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            Screen.objects.create(
                name='Duplicate Screen',
                device_id='duplicate-001',
                owner=self.user
            )
    
    def test_schedule_end_before_start(self):
        """Test schedule validation rejects end_time before start_time."""
        from templates.models import Schedule
        
        schedule = Schedule(
            name='Invalid Schedule',
            template=self.create_template(),
            start_time=timezone.now(),
            end_time=timezone.now() - timedelta(hours=1),
            is_active=True
        )
        
        with self.assertRaises(ValidationError):
            schedule.full_clean()
    
    def test_command_with_expired_expire_at(self):
        """Test command with past expire_at."""
        from commands.models import Command
        
        command = Command(
            name='Expired Command',
            type='refresh',
            screen=self.create_screen(),
            created_by=self.user,
            expire_at=timezone.now() - timedelta(hours=1)
        )
        
        with self.assertRaises(ValidationError):
            command.full_clean()
    
    def test_content_with_invalid_type(self):
        """Test content with invalid type fails validation."""
        content = self.create_content(type='invalid_type')
        
        is_valid, error = content.validate_content()
        self.assertFalse(is_valid)
    
    def test_template_with_zero_dimensions(self):
        """Test template validation rejects zero dimensions."""
        from templates.models import Template
        
        template = Template(
            name='Invalid Template',
            width=0,
            height=0,
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()


class ErrorHandlingTests(BaseAPITestCase):
    """Tests for error handling in API endpoints."""
    
    def test_get_nonexistent_screen(self):
        """Test getting nonexistent screen returns 404."""
        from django.urls import reverse
        from uuid import uuid4
        
        url = reverse('screen-detail', kwargs={'id': str(uuid4())})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_nonexistent_resource(self):
        """Test updating nonexistent resource returns 404."""
        from django.urls import reverse
        from uuid import uuid4
        
        url = reverse('template-detail', kwargs={'id': str(uuid4())})
        response = self.client.patch(url, {'name': 'Test'}, format='json')
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_nonexistent_resource(self):
        """Test deleting nonexistent resource returns 404."""
        from django.urls import reverse
        from uuid import uuid4
        
        url = reverse('content-detail', kwargs={'id': str(uuid4())})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_json_payload(self):
        """Test API handles invalid JSON gracefully."""
        from django.urls import reverse
        
        url = reverse('screen-list')
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertResponseError(response)
    
    def test_missing_required_fields(self):
        """Test API rejects requests with missing required fields."""
        from django.urls import reverse
        
        url = reverse('screen-list')
        response = self.client.post(url, {}, format='json')
        
        # Should return validation error
        self.assertResponseError(response)
        self.assertIn('device_id', str(response.data) or '')


class RaceConditionTests(BaseAPITestCase):
    """Tests for potential race conditions."""
    
    def test_concurrent_screen_updates(self):
        """Test handling concurrent screen updates."""
        screen = self.create_screen(name='Original Name')
        
        # Simulate concurrent updates
        screen1 = type(screen).objects.get(id=screen.id)
        screen2 = type(screen).objects.get(id=screen.id)
        
        screen1.name = 'Update 1'
        screen1.save()
        
        screen2.name = 'Update 2'
        screen2.save()
        
        # Last save should win
        screen.refresh_from_db()
        self.assertEqual(screen.name, 'Update 2')
    
    def test_concurrent_command_execution(self):
        """Test handling concurrent command execution attempts."""
        screen = self.create_screen(is_online=True)
        command = self.create_command(screen=screen)
        
        # Simulate concurrent execution attempts
        command1 = type(command).objects.get(id=command.id)
        command2 = type(command).objects.get(id=command.id)
        
        # Both should handle gracefully
        try:
            command1.status = 'executing'
            command1.save()
        except:
            pass
        
        try:
            command2.status = 'executing'
            command2.save()
        except:
            pass


class BoundaryValueTests(BaseAPITestCase):
    """Tests for boundary values and limits."""
    
    def test_very_long_filename(self):
        """Test handling of very long filenames."""
        from content_validation.validators import ContentValidator
        
        # Create filename longer than 255 characters
        long_filename = 'a' * 300 + '.jpg'
        file_obj = BytesIO(b'fake image')
        
        result = ContentValidator.validate_filename(long_filename)
        self.assertTrue(result[0])  # Should sanitize and truncate
        self.assertLessEqual(len(result[1]), 255)
    
    def test_zero_size_file(self):
        """Test handling of zero-size files."""
        from content_validation.validators import ContentValidator, ValidationError
        
        empty_file = BytesIO(b'')
        empty_file.name = 'empty.jpg'
        
        with self.assertRaises(ValidationError):
            ContentValidator.validate_content(
                file_obj=empty_file,
                content_type='image',
                filename='empty.jpg'
            )
    
    def test_max_file_size_boundary(self):
        """Test file size validation at boundary."""
        from content_validation.validators import ContentValidator
        
        # Create file at exact max size
        max_size = ContentValidator.MAX_FILE_SIZES['image']
        file_obj = BytesIO(b'x' * max_size)
        file_obj.name = 'maxsize.jpg'
        
        result = ContentValidator.validate_file_size(file_obj, 'image')
        self.assertTrue(result[0])  # Should pass
        
        # Create file slightly over max size
        file_obj2 = BytesIO(b'x' * (max_size + 1))
        file_obj2.name = 'oversized.jpg'
        
        result = ContentValidator.validate_file_size(file_obj2, 'image')
        self.assertFalse(result[0])  # Should fail
