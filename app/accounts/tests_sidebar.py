"""
Unit tests for sidebar items API and permission filtering.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from .sidebar_config import (
    get_user_permissions,
    has_permission,
    filter_sidebar_items,
    PERMISSIONS,
    ROLE_PERMISSIONS,
)

User = get_user_model()


class SidebarConfigTests(TestCase):
    """Test sidebar configuration and permission functions."""

    def setUp(self):
        self.developer = User.objects.create_user(
            username='developer',
            email='developer@test.com',
            password='testpass123',
            role='Developer',
            is_superuser=True,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role='Manager',
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role='Employee',
        )
        self.visitor = User.objects.create_user(
            username='visitor',
            email='visitor@test.com',
            password='testpass123',
            role='Visitor',
        )

    def test_get_user_permissions_developer(self):
        permissions = get_user_permissions(self.developer)
        self.assertEqual(len(permissions), len(PERMISSIONS))
        for perm in PERMISSIONS.values():
            self.assertIn(perm, permissions)

    def test_get_user_permissions_manager(self):
        permissions = get_user_permissions(self.manager)
        expected_perms = set(ROLE_PERMISSIONS['Manager'])
        self.assertEqual(permissions, expected_perms)

    def test_get_user_permissions_employee(self):
        permissions = get_user_permissions(self.employee)
        expected_perms = set(ROLE_PERMISSIONS['Employee'])
        self.assertEqual(permissions, expected_perms)
        self.assertIn('view_dashboard', permissions)

    def test_get_user_permissions_visitor(self):
        permissions = get_user_permissions(self.visitor)
        expected_perms = set(ROLE_PERMISSIONS['Visitor'])
        self.assertEqual(permissions, expected_perms)

    def test_has_permission(self):
        self.assertTrue(has_permission(self.developer, 'view_dashboard'))
        self.assertTrue(has_permission(self.developer, 'view_errors'))

        self.assertTrue(has_permission(self.manager, 'view_dashboard'))
        self.assertFalse(has_permission(self.manager, 'view_logs'))

        self.assertTrue(has_permission(self.employee, 'view_screens'))
        self.assertTrue(has_permission(self.employee, 'create_templates'))
        self.assertFalse(has_permission(self.employee, 'delete_templates'))
        self.assertTrue(has_permission(self.employee, 'create_commands'))
        self.assertTrue(has_permission(self.employee, 'execute_commands'))
        self.assertTrue(has_permission(self.employee, 'view_logs'))
        self.assertTrue(has_permission(self.employee, 'view_analytics'))
        self.assertTrue(has_permission(self.employee, 'view_settings'))
        self.assertFalse(has_permission(self.employee, 'view_users'))

        self.assertTrue(has_permission(self.visitor, 'view_dashboard'))
        self.assertTrue(has_permission(self.visitor, 'view_templates'))
        self.assertTrue(has_permission(self.visitor, 'view_screens'))
        self.assertFalse(has_permission(self.visitor, 'create_templates'))
        self.assertFalse(has_permission(self.visitor, 'view_users'))

    def test_filter_sidebar_items_developer(self):
        items = filter_sidebar_items(self.developer)
        item_ids = [item['id'] for item in items]
        self.assertIn('dashboard', item_ids)
        self.assertIn('settings', item_ids)
        self.assertNotIn('super-admin', item_ids)

    def test_filter_sidebar_items_employee(self):
        items = filter_sidebar_items(self.employee)
        item_ids = [item['id'] for item in items]
        self.assertIn('dashboard', item_ids)
        self.assertIn('screens', item_ids)
        self.assertIn('templates', item_ids)
        self.assertIn('contents', item_ids)
        self.assertIn('schedules', item_ids)
        self.assertIn('commands', item_ids)
        self.assertIn('logs', item_ids)
        self.assertIn('analytics', item_ids)
        self.assertIn('settings', item_ids)
        self.assertNotIn('users', item_ids)

    def test_filter_sidebar_items_visitor(self):
        items = filter_sidebar_items(self.visitor)
        item_ids = [item['id'] for item in items]
        self.assertIn('dashboard', item_ids)
        self.assertIn('templates', item_ids)
        self.assertIn('screens', item_ids)
        self.assertIn('contents', item_ids)
        self.assertIn('schedules', item_ids)
        self.assertIn('commands', item_ids)
        self.assertIn('logs', item_ids)
        self.assertIn('analytics', item_ids)
        self.assertNotIn('users', item_ids)
        self.assertNotIn('settings', item_ids)
        self.assertNotIn('super-admin', item_ids)

    def test_unauthenticated_user(self):
        items = filter_sidebar_items(None)
        self.assertEqual(len(items), 0)


class SidebarItemsAPITests(TestCase):
    """Test sidebar items API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.developer = User.objects.create_user(
            username='developer',
            email='developer@test.com',
            password='testpass123',
            role='Developer',
            is_superuser=True,
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role='Employee',
        )
        cache.clear()

    def test_sidebar_items_requires_authentication(self):
        response = self.client.get('/api/sidebar-items/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sidebar_items_developer(self):
        self.client.force_authenticate(user=self.developer)
        response = self.client.get('/api/sidebar-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('items', response.data)
        self.assertGreater(len(response.data['items']), 0)

    def test_sidebar_items_employee(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/sidebar-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['items']
        item_ids = [item['id'] for item in items]
        self.assertNotIn('users', item_ids)

    def test_sidebar_items_caching(self):
        self.client.force_authenticate(user=self.developer)
        response1 = self.client.get('/api/sidebar-items/')
        response2 = self.client.get('/api/sidebar-items/')
        self.assertEqual(response1.data, response2.data)

    def test_sidebar_items_cache_invalidation(self):
        self.client.force_authenticate(user=self.employee)
        response1 = self.client.get('/api/sidebar-items/')
        before_ids = {item['id'] for item in response1.data['items']}
        self.assertNotIn('users', before_ids)

        self.employee.role = 'Manager'
        self.employee.is_staff = True
        self.employee.save()
        cache.clear()

        response2 = self.client.get('/api/sidebar-items/')
        after_ids = {item['id'] for item in response2.data['items']}
        self.assertIn('users', after_ids)
