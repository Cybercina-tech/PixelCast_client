"""
Comprehensive unit tests for all database models.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import json
from tests.base import BaseTestCase


class UserModelTests(BaseTestCase):
    """Tests for User model."""
    
    def test_create_user(self):
        """Test creating a user."""
        user = self.create_user(username='newuser', email='new@test.com')
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@test.com')
        self.assertTrue(user.is_active)
    
    def test_user_role_helpers(self):
        """Test user role helper methods."""
        user = self.create_user(role='Developer', is_superuser=True, is_staff=True)
        self.assertTrue(user.is_developer())
        self.assertTrue(user.is_superadmin())
        self.assertTrue(user.has_full_access())
        self.assertTrue(user.can_execute_commands())

        user = self.create_user(role='Manager', is_staff=True)
        self.assertTrue(user.is_manager())
        self.assertTrue(user.can_manage_own_resources())
        self.assertTrue(user.can_execute_commands())

        user = self.create_user(role='Employee')
        self.assertTrue(user.is_employee())
        self.assertFalse(user.has_full_access())
        self.assertFalse(user.can_execute_commands())
    
    def test_user_email_lowercase(self):
        """Test email is stored in lowercase."""
        user = self.create_user(email='Test@Example.COM')
        self.assertEqual(user.email, 'test@example.com')
    
    def test_user_organization_access(self):
        """Test organization access control."""
        user1 = self.create_user(username='user1', organization_name='Org1')
        user2 = self.create_user(username='user2', organization_name='Org1')
        user3 = self.create_user(username='user3', organization_name='Org2')
        
        # Same organization
        self.assertTrue(user1.can_access_user_resource(user2))
        
        # Different organization
        self.assertFalse(user1.can_access_user_resource(user3))
        
        dev = self.create_user(role='Developer', is_superuser=True, is_staff=True)
        self.assertTrue(dev.can_access_user_resource(user1))


class ScreenModelTests(BaseTestCase):
    """Tests for Screen model."""
    
    def test_create_screen(self):
        """Test creating a screen."""
        screen = self.create_screen(name='New Screen', device_id='device-001')
        self.assertEqual(screen.name, 'New Screen')
        self.assertEqual(screen.device_id, 'device-001')
        self.assertIsNotNone(screen.auth_token)
        self.assertIsNotNone(screen.secret_key)
    
    def test_screen_auto_generate_tokens(self):
        """Test tokens are auto-generated."""
        screen = self.create_screen()
        self.assertIsNotNone(screen.auth_token)
        self.assertIsNotNone(screen.secret_key)
        self.assertNotEqual(screen.auth_token, screen.secret_key)
    
    def test_screen_authentication(self):
        """Test screen authentication."""
        screen = self.create_screen()
        auth_token = screen.auth_token
        secret_key = screen.secret_key
        
        self.assertTrue(screen.authenticate(auth_token, secret_key))
        self.assertFalse(screen.authenticate('wrong', secret_key))
        self.assertFalse(screen.authenticate(auth_token, 'wrong'))
    
    def test_screen_update_heartbeat(self):
        """Test updating screen heartbeat."""
        screen = self.create_screen(is_online=False)
        screen.update_heartbeat(latency=50, cpu_usage=30.5, memory_usage=45.2)
        
        self.assertTrue(screen.is_online)
        self.assertIsNotNone(screen.last_heartbeat_at)
    
    def test_screen_activate_template(self):
        """Test activating template on screen."""
        screen = self.create_screen()
        template = self.create_template()
        
        result = screen.activate_template(template, sync_content=False)
        self.assertTrue(result)
        self.assertEqual(screen.active_template, template)
        self.assertIsNotNone(screen.last_template_update_at)
    
    def test_screen_health_check(self):
        """Test screen health check."""
        screen = self.create_screen(is_online=True)
        health = screen.health_check()
        
        self.assertIn('is_online', health)
        self.assertIn('is_heartbeat_stale', health)
        self.assertIn('has_active_template', health)
        self.assertIn('pending_commands_count', health)
    
    def test_screen_queue_command(self):
        """Test queuing command for screen."""
        screen = self.create_screen()
        command = screen.queue_command('restart', priority=5, created_by=self.user)
        
        self.assertEqual(command.screen, screen)
        self.assertEqual(command.type, 'restart')
        self.assertEqual(command.priority, 5)
        self.assertEqual(command.status, 'pending')


class TemplateModelTests(BaseTestCase):
    """Tests for Template model."""
    
    def test_create_template(self):
        """Test creating a template."""
        template = self.create_template(name='New Template', width=1920, height=1080)
        self.assertEqual(template.name, 'New Template')
        self.assertEqual(template.width, 1920)
        self.assertEqual(template.height, 1080)
        self.assertEqual(template.version, 1)
    
    def test_template_activate_on_screen(self):
        """Test activating template on screen."""
        template = self.create_template()
        screen = self.create_screen()
        
        result = template.activate_on_screen(screen, sync_content=False)
        self.assertTrue(result)
        self.assertEqual(screen.active_template, template)


class ContentModelTests(BaseTestCase):
    """Tests for Content model."""
    
    def test_create_content(self):
        """Test creating content."""
        content = self.create_content(name='New Content', type='text')
        self.assertEqual(content.name, 'New Content')
        self.assertEqual(content.type, 'text')
        self.assertTrue(content.is_active)
        self.assertFalse(content.downloaded)
    
    def test_content_mark_downloaded(self):
        """Test marking content as downloaded."""
        content = self.create_content()
        content.mark_downloaded()
        
        self.assertTrue(content.downloaded)
        self.assertEqual(content.download_status, 'success')
        self.assertIsNotNone(content.last_download_attempt)
    
    def test_content_mark_failed(self):
        """Test marking content as failed."""
        content = self.create_content()
        content.mark_failed('Test error')
        
        self.assertFalse(content.downloaded)
        self.assertEqual(content.download_status, 'failed')
        self.assertEqual(content.retry_count, 1)
    
    def test_content_needs_download(self):
        """Test checking if content needs download."""
        content = self.create_content()
        self.assertTrue(content.needs_download)
        
        content.mark_downloaded()
        self.assertFalse(content.needs_download)
    
    def test_content_validate_content(self):
        """Test content validation."""
        content = self.create_content(type='text', content_json={'text': 'Hello'})
        is_valid, error = content.validate_content()
        self.assertTrue(is_valid)
        
        # Invalid content
        content = self.create_content(type='image')
        is_valid, error = content.validate_content()
        self.assertFalse(is_valid)


class ScheduleModelTests(BaseTestCase):
    """Tests for Schedule model."""
    
    def test_create_schedule(self):
        """Test creating a schedule."""
        schedule = self.create_schedule(
            name='Test Schedule',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
        self.assertEqual(schedule.name, 'Test Schedule')
        self.assertTrue(schedule.is_active)
        self.assertEqual(schedule.repeat_type, 'none')
    
    def test_schedule_clean_validation(self):
        """Test schedule validation."""
        schedule = self.create_schedule()
        # Should not raise
        schedule.full_clean()
        
        # Invalid: end_time before start_time
        schedule.end_time = schedule.start_time - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            schedule.full_clean()
    
    def test_schedule_activate_deactivate(self):
        """Test activating/deactivating schedule."""
        schedule = self.create_schedule()
        
        schedule.deactivate()
        self.assertFalse(schedule.is_active)
        self.assertFalse(schedule.is_currently_running)
        
        schedule.activate()
        self.assertTrue(schedule.is_active)
    
    def test_schedule_duration_property(self):
        """Test schedule duration calculation."""
        start = timezone.now()
        end = start + timedelta(hours=2)
        schedule = self.create_schedule(start_time=start, end_time=end)
        
        self.assertEqual(schedule.duration, 7200)  # 2 hours in seconds
    
    def test_schedule_next_run(self):
        """Test calculating next run time."""
        schedule = self.create_schedule(repeat_type='daily')
        next_run = schedule.next_run()
        
        # Should return a datetime for daily schedule
        self.assertIsNotNone(next_run)


class CommandModelTests(BaseTestCase):
    """Tests for Command model."""
    
    def test_create_command(self):
        """Test creating a command."""
        command = self.create_command(
            name='Test Command',
            type='restart',
            priority=10
        )
        self.assertEqual(command.name, 'Test Command')
        self.assertEqual(command.type, 'restart')
        self.assertEqual(command.priority, 10)
        self.assertEqual(command.status, 'pending')
    
    def test_command_mark_done(self):
        """Test marking command as done."""
        command = self.create_command()
        command.mark_done()
        
        self.assertEqual(command.status, 'done')
        self.assertIsNotNone(command.completed_at)
    
    def test_command_mark_failed(self):
        """Test marking command as failed."""
        command = self.create_command()
        command.mark_failed('Test error')
        
        self.assertEqual(command.status, 'failed')
        self.assertEqual(command.attempt_count, 1)
        self.assertEqual(command.error_message, 'Test error')
    
    def test_command_is_expired(self):
        """Test checking if command is expired."""
        command = self.create_command()
        self.assertFalse(command.is_expired())
        
        command.expire_at = timezone.now() - timedelta(hours=1)
        command.save()
        self.assertTrue(command.is_expired())
    
    def test_command_can_retry(self):
        """Test checking if command can be retried."""
        command = self.create_command()
        self.assertTrue(command.can_retry())
        
        command.attempt_count = 3
        command.save()
        self.assertFalse(command.can_retry())
    
    def test_command_reset_status(self):
        """Test resetting command status."""
        command = self.create_command(status='failed')
        command.reset_status()
        
        self.assertEqual(command.status, 'pending')
        self.assertIsNone(command.last_attempt_at)
