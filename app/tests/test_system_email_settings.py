"""Tests for system email settings API and email service."""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import SystemEmailSettings
from core.email_service import get_system_email_connection, send_system_email

User = get_user_model()


class SystemEmailSettingsAPITests(TestCase):
    """API tests (Developer-only)."""

    def setUp(self):
        self.dev = User.objects.create_user(
            username='dev',
            email='dev@test.com',
            password='x',
            role='Developer',
            is_superuser=True,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            username='mgr',
            email='mgr@test.com',
            password='x',
            role='Manager',
            organization_name='TestOrg',
        )

    def test_get_forbidden_for_manager(self):
        c = APIClient()
        c.force_authenticate(user=self.manager)
        r = c.get('/api/core/system-email-settings/')
        self.assertEqual(r.status_code, 403)

    def test_get_and_patch_developer(self):
        c = APIClient()
        c.force_authenticate(user=self.dev)
        r = c.get('/api/core/system-email-settings/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('delivery_mode', r.data)
        self.assertNotIn('smtp_password', r.data)
        self.assertIn('smtp_password_configured', r.data)

        r2 = c.patch(
            '/api/core/system-email-settings/',
            {
                'delivery_mode': 'smtp',
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'use_tls': True,
                'use_ssl': False,
                'smtp_username': 'user',
                'smtp_password': 'secretpass',
                'default_from_email': 'from@example.com',
            },
            format='json',
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data['smtp_host'], 'smtp.example.com')
        self.assertTrue(r2.data['smtp_password_configured'])

        obj = SystemEmailSettings.get_solo()
        self.assertEqual(obj.get_smtp_password(), 'secretpass')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_system_email_and_connection(self):
        solo = SystemEmailSettings.get_solo()
        solo.delivery_mode = SystemEmailSettings.DELIVERY_CONSOLE
        solo.save()
        send_system_email('Hi', 'Body', ['a@b.com'])
        conn = get_system_email_connection()
        self.assertIsNotNone(conn)

    def test_test_endpoint(self):
        c = APIClient()
        c.force_authenticate(user=self.dev)
        solo = SystemEmailSettings.get_solo()
        solo.delivery_mode = SystemEmailSettings.DELIVERY_CONSOLE
        solo.save()
        r = c.post(
            '/api/core/system-email-settings/test/',
            {'to': 'test@example.com'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data.get('success'))
        solo.refresh_from_db()
        self.assertTrue(solo.last_smtp_test_ok)
        self.assertIsNotNone(solo.last_smtp_test_at)

    def test_patch_rejects_tls_and_ssl_together(self):
        c = APIClient()
        c.force_authenticate(user=self.dev)
        r = c.patch(
            '/api/core/system-email-settings/',
            {
                'delivery_mode': 'smtp',
                'smtp_host': 'smtp.example.com',
                'use_tls': True,
                'use_ssl': True,
            },
            format='json',
        )
        self.assertEqual(r.status_code, 400)
