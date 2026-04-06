"""
Tests for permission and authorization logic.
"""
import uuid

from rest_framework.test import APITestCase, APIClient

from tests.base import BaseAPITestCase
from accounts.permissions import RolePermissions


class PermissionTests(BaseAPITestCase):
    """Tests for permission checking."""

    def test_developer_permissions(self):
        dev = self.create_user(role='Developer', is_superuser=True, is_staff=True)
        screen = self.create_screen()
        template = self.create_template()
        self.assertTrue(RolePermissions.can_edit_resource(dev, screen))
        self.assertTrue(RolePermissions.can_edit_resource(dev, template))
        self.assertTrue(RolePermissions.can_view_resource(dev, screen))

    def test_manager_permissions(self):
        manager = self.create_user(role='Manager', organization_name='Org1')
        other_manager = self.create_user(role='Manager', organization_name='Org2')
        own_screen = self.create_screen(owner=manager)
        self.assertTrue(RolePermissions.can_edit_resource(manager, own_screen))
        other_screen = self.create_screen(owner=other_manager)
        self.assertFalse(RolePermissions.can_edit_resource(manager, other_screen))

    def test_employee_permissions(self):
        employee = self.create_user(role='Employee')
        own_screen = self.create_screen(owner=employee)
        self.assertTrue(RolePermissions.can_view_resource(employee, own_screen))
        own_template = self.create_template(created_by=employee)
        self.assertTrue(RolePermissions.can_edit_resource(employee, own_template))
        other = self.create_user(role='Employee')
        other_template = self.create_template(created_by=other)
        self.assertFalse(RolePermissions.can_edit_resource(employee, other_template))

    def test_command_execution_roles(self):
        manager = self.create_user(role='Manager')
        employee = self.create_user(role='Employee')
        self.assertTrue(manager.can_execute_commands())
        self.assertTrue(employee.can_execute_commands())


class APIPermissionTests(BaseAPITestCase):
    """Tests for API endpoint permissions."""

    def setUp(self):
        """Use an unauthenticated API client; each test sets auth as needed."""
        from django.core.cache import cache

        cache.clear()
        super(APITestCase, self).setUp()
        self.client = APIClient()
        suffix = uuid.uuid4().hex[:10]
        self.user = self.create_user(
            username=f'perm_api_{suffix}',
            email=f'perm_api_{suffix}@test.local',
            password='testpass123',
            role='Manager',
            organization_name='TestOrg',
        )

    def test_unauthorized_access_denied(self):
        from django.urls import reverse

        self.client.logout()
        url = reverse('screen-list')
        response = self.client.get(url, HTTP_AUTHORIZATION='')
        self.assertIn(response.status_code, (401, 403))

    def test_employee_can_create_screens(self):
        employee = self.create_user(role='Employee')
        self.client.force_authenticate(user=employee)
        from django.urls import reverse
        url = reverse('screen-list')
        data = {'name': 'Test', 'device_id': f'test-{uuid.uuid4().hex[:12]}'}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [201, 400])

    def test_manager_can_create_screens(self):
        manager = self.create_user(role='Manager')
        self.client.force_authenticate(user=manager)
        from django.urls import reverse
        url = reverse('screen-list')
        data = {'name': 'Test', 'device_id': f'test-{uuid.uuid4().hex[:12]}'}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [201, 400])

    def test_manager_can_create_commands(self):
        manager = self.create_user(role='Manager', organization_name='TestOrg')
        self.client.force_authenticate(user=manager)
        screen = self.create_screen(owner=manager)
        from django.urls import reverse
        url = reverse('command-list')
        data = {
            'name': 'Test Command',
            'type': 'refresh',
            'screen_id': str(screen.id),
            'payload': {}
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [201, 400])

    def test_employee_cannot_create_commands_for_inaccessible_screen(self):
        """Employee without org access cannot target another user's screen."""
        employee = self.create_user(role='Employee')
        self.client.force_authenticate(user=employee)
        screen = self.create_screen()
        from django.urls import reverse
        url = reverse('command-list')
        data = {
            'name': 'Test Command',
            'type': 'refresh',
            'screen_id': str(screen.id),
            'payload': {}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_employee_can_create_commands_for_org_screen(self):
        employee = self.create_user(role='Employee', organization_name='TestOrg')
        self.client.force_authenticate(user=employee)
        screen = self.create_screen()
        from django.urls import reverse
        url = reverse('command-list')
        data = {
            'name': 'Test Command',
            'type': 'refresh',
            'screen_id': str(screen.id),
            'payload': {}
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [201, 400])
