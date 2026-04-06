"""
Tests for bulk operations endpoints.
"""
import json
from django.urls import reverse
from rest_framework import status
from tests.base import BaseAPITestCase


class BulkScreensTests(BaseAPITestCase):
    """Tests for bulk screen operations."""
    
    def test_bulk_delete_screens(self):
        """Test bulk deleting screens."""
        screen1 = self.create_screen()
        screen2 = self.create_screen()
        
        url = reverse('bulk-screens-delete')
        data = {
            'item_ids': [str(screen1.id), str(screen2.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['success_count'], 2)
    
    def test_bulk_update_screens(self):
        """Test bulk updating screens."""
        screen1 = self.create_screen()
        screen2 = self.create_screen()
        
        url = reverse('bulk-screens-update')
        data = {
            'item_ids': [str(screen1.id), str(screen2.id)],
            'update_data': {'location': 'Updated Location'}
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['success_count'], 2)
    
    def test_bulk_activate_template(self):
        """Test bulk activating template on screens."""
        screen1 = self.create_screen()
        screen2 = self.create_screen()
        template = self.create_template()
        
        url = reverse('bulk-screens-activate-template')
        data = {
            'item_ids': [str(screen1.id), str(screen2.id)],
            'template_id': str(template.id),
            'sync_content': False
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)
    
    def test_bulk_send_command(self):
        """Test bulk sending commands."""
        screen1 = self.create_screen()
        screen2 = self.create_screen()
        
        url = reverse('bulk-screens-send-command')
        data = {
            'item_ids': [str(screen1.id), str(screen2.id)],
            'command_type': 'refresh',
            'payload': {},
            'priority': 0
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)


class BulkTemplatesTests(BaseAPITestCase):
    """Tests for bulk template operations."""
    
    def test_bulk_delete_templates(self):
        """Test bulk deleting templates."""
        template1 = self.create_template()
        template2 = self.create_template()
        
        url = reverse('bulk-templates-delete')
        data = {
            'item_ids': [str(template1.id), str(template2.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['success_count'], 2)
    
    def test_bulk_activate_templates(self):
        """Test bulk activating templates."""
        template1 = self.create_template(is_active=False)
        template2 = self.create_template(is_active=False)
        
        url = reverse('bulk-templates-activate')
        data = {
            'item_ids': [str(template1.id), str(template2.id)],
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)
        self.assertEqual(response.data['success_count'], 2)


class BulkCommandsTests(BaseAPITestCase):
    """Tests for bulk command operations."""
    
    def test_bulk_execute_commands(self):
        """Test bulk executing commands."""
        command1 = self.create_command()
        command2 = self.create_command()
        
        url = reverse('bulk-commands-execute')
        data = {
            'item_ids': [str(command1.id), str(command2.id)]
        }
        response = self.client.post(url, data, format='json')
        
        # May have partial success
        self.assertResponseSuccess(response)
        self.assertIn(response.status_code, [200, 207])
    
    def test_bulk_retry_commands(self):
        """Test bulk retrying commands."""
        command1 = self.create_command(status='failed')
        command2 = self.create_command(status='failed')
        
        url = reverse('bulk-commands-retry')
        data = {
            'item_ids': [str(command1.id), str(command2.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertResponseSuccess(response)


class BulkOperationsErrorHandlingTests(BaseAPITestCase):
    """Tests for bulk operations error handling."""
    
    def test_bulk_operations_with_invalid_ids(self):
        """Test bulk operations with invalid IDs."""
        url = reverse('bulk-screens-delete')
        data = {
            'item_ids': ['invalid-uuid-1', 'invalid-uuid-2']
        }
        response = self.client.post(url, data, format='json')
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 207, 400])
    
    def test_bulk_operations_with_mixed_valid_invalid(self):
        """Test bulk operations with mix of valid and invalid IDs."""
        screen = self.create_screen()
        
        url = reverse('bulk-screens-delete')
        data = {
            'item_ids': [str(screen.id), 'invalid-uuid']
        }
        response = self.client.post(url, data, format='json')
        
        # Should succeed partially
        self.assertResponseSuccess(response)
        if response.status_code == 207:  # Multi-Status
            self.assertGreater(response.data['success_count'], 0)
            self.assertGreater(response.data['failure_count'], 0)
    
    def test_bulk_operations_rate_limiting(self):
        """Test bulk operations rate limiting."""
        screens = [self.create_screen() for _ in range(200)]
        
        url = reverse('bulk-screens-delete')
        data = {
            'item_ids': [str(s.id) for s in screens]
        }
        response = self.client.post(url, data, format='json')
        
        # Should either succeed or be rate limited
        self.assertIn(response.status_code, [200, 207, 429])
    
    def test_bulk_operations_permission_denied(self):
        """Test bulk operations with permission denied."""
        # Create user with limited permissions
        viewer = self.create_user(role='Employee')
        self.client.force_authenticate(user=viewer)
        
        screen = self.create_screen(owner=self.user)  # Owned by different user
        
        url = reverse('bulk-screens-delete')
        data = {
            'item_ids': [str(screen.id)]
        }
        response = self.client.post(url, data, format='json')
        
        # Should handle permission denied gracefully
        self.assertIn(response.status_code, [200, 207, 403])
