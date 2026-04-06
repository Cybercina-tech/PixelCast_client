"""Visitor role: template API read vs write."""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class VisitorTemplateAPITests(TestCase):
    def setUp(self):
        from templates.models import Template

        self.client = APIClient()
        self.dev = User.objects.create_user(
            username='devvt',
            email='devvt@example.com',
            password='pass12345!',
            role='Developer',
            is_superuser=True,
            is_staff=True,
        )
        self.visitor = User.objects.create_user(
            username='visvt',
            email='visvt@example.com',
            password='pass12345!',
            role='Visitor',
        )
        self.sample = Template.objects.create(
            name='Sample template',
            is_sample=True,
            created_by=self.dev,
            config_json={'widgets': []},
        )

    def test_visitor_can_list_sample_template(self):
        self.client.force_authenticate(user=self.visitor)
        response = self.client.get('/api/templates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data
        if isinstance(payload, list):
            results = payload
        else:
            results = payload.get('results') or []
        ids = [str(r['id']) for r in results]
        self.assertIn(str(self.sample.id), ids)

    def test_visitor_cannot_patch_template(self):
        self.client.force_authenticate(user=self.visitor)
        response = self.client.patch(
            f'/api/templates/{self.sample.id}/',
            {'name': 'Should Not Save'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_visitor_cannot_create_template(self):
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(
            '/api/templates/',
            {
                'name': 'New',
                'width': 1920,
                'height': 1080,
                'config_json': {'widgets': []},
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_visitor_operational_logs_list_returns_empty_not_403(self):
        """Dashboard must not receive 403 for log list endpoints (empty list for non-Developer)."""
        self.client.force_authenticate(user=self.visitor)
        for path in (
            '/api/logs/command-execution/',
            '/api/logs/content-download/',
            '/api/logs/screen-status/',
        ):
            r = self.client.get(path)
            self.assertEqual(r.status_code, status.HTTP_200_OK, msg=path)
            payload = r.data
            results = payload.get('results') if isinstance(payload, dict) else payload
            self.assertEqual(len(results or []), 0, msg=path)

    def test_visitor_log_summaries_return_empty_counts(self):
        self.client.force_authenticate(user=self.visitor)
        for path in (
            '/api/logs/command-execution/summary/',
            '/api/logs/content-download/summary/',
            '/api/logs/screen-status/summary/',
        ):
            r = self.client.get(path)
            self.assertEqual(r.status_code, status.HTTP_200_OK, msg=path)
            self.assertEqual(r.data.get('summary', {}).get('total_count'), 0, msg=path)
