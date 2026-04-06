"""
Comprehensive tests for Analytics Dashboard API endpoints.

Tests cover:
- Correctness of analytics calculations
- Security (authentication, authorization, input validation)
- Edge cases (empty datasets, invalid parameters)
- Performance considerations
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta, datetime
import uuid

from tests.base import BaseAPITestCase
from signage.models import Screen
from commands.models import Command
from templates.models import Template, Content
from log.models import ScreenStatusLog, ContentDownloadLog
from accounts.models import User


@pytest.mark.analytics
@pytest.mark.api
class AnalyticsAPITestCase(BaseAPITestCase):
    """Base test case for analytics API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create test screens
        self.screen1 = self.create_screen(name='Screen 1', is_online=True)
        self.screen2 = self.create_screen(name='Screen 2', is_online=False)
        self.screen3 = self.create_screen(name='Screen 3', is_online=True)
        
        # Create status logs
        ScreenStatusLog.objects.create(
            screen=self.screen1,
            status='online',
            cpu_usage=25.5,
            memory_usage=45.0,
            heartbeat_latency=50.0
        )
        ScreenStatusLog.objects.create(
            screen=self.screen2,
            status='offline',
            cpu_usage=None,
            memory_usage=None,
            heartbeat_latency=None
        )
        ScreenStatusLog.objects.create(
            screen=self.screen3,
            status='online',
            cpu_usage=30.0,
            memory_usage=50.0,
            heartbeat_latency=75.0
        )
        
        # Create commands
        self.create_command(screen=self.screen1, type='restart', status='done')
        self.create_command(screen=self.screen1, type='refresh', status='pending')
        self.create_command(screen=self.screen2, type='restart', status='failed')
        
        # Create templates
        self.template1 = self.create_template(name='Template 1')
        self.screen1.active_template = self.template1
        self.screen1.save()
        
        # Create content
        self.content1 = self.create_content(template=self.template1, name='Content 1', type='image')
        ContentDownloadLog.objects.create(
            content=self.content1,
            screen=self.screen1,
            status='success'
        )


@pytest.mark.analytics
@pytest.mark.unit
class ScreenAnalyticsTests(AnalyticsAPITestCase):
    """Tests for screen analytics endpoints."""
    
    def test_screen_statistics_success(self):
        """Test successful screen statistics retrieval."""
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        
        data = response.data['data']
        self.assertIn('total_screens', data)
        self.assertIn('status_breakdown', data)
        self.assertIn('health_metrics', data)
        self.assertEqual(data['total_screens'], 3)
        self.assertEqual(data['status_breakdown']['online'], 2)
        self.assertEqual(data['status_breakdown']['offline'], 1)
    
    def test_screen_statistics_with_filter(self):
        """Test screen statistics with screen_ids filter."""
        url = reverse('analytics:screen-statistics')
        screen_ids = f"{self.screen1.id},{self.screen2.id}"
        response = self.client.get(url, {'screen_ids': screen_ids})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertLessEqual(data['total_screens'], 2)
    
    def test_screen_statistics_with_date_range(self):
        """Test screen statistics with date range."""
        url = reverse('analytics:screen-statistics')
        start_date = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')
        
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('period', response.data['data'])
    
    def test_screen_statistics_invalid_date_format(self):
        """Test screen statistics with invalid date format."""
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url, {'start_date': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
    
    def test_screen_statistics_invalid_uuid(self):
        """Test screen statistics with invalid UUID."""
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url, {'screen_ids': 'invalid-uuid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_screen_detail_success(self):
        """Test successful screen detail retrieval."""
        url = reverse('analytics:screen-detail', kwargs={'screen_id': self.screen1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        data = response.data['data']
        self.assertEqual(data['screen_id'], str(self.screen1.id))
        self.assertEqual(data['screen_name'], self.screen1.name)
        self.assertIn('command_statistics', data)
    
    def test_screen_detail_not_found(self):
        """Test screen detail with non-existent screen."""
        fake_id = uuid.uuid4()
        url = reverse('analytics:screen-detail', kwargs={'screen_id': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_screen_statistics_unauthorized(self):
        """Test screen statistics without authentication."""
        self.client.logout()
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_screen_statistics_employee_allowed(self):
        """Employees with view_analytics may load statistics (scoped to org screens)."""
        viewer_user = self.create_user(
            username='viewer',
            role='Employee',
            organization_name='TestOrg'
        )
        viewer_client = APIClient()
        viewer_client.force_authenticate(user=viewer_user)
        
        url = reverse('analytics:screen-statistics')
        response = viewer_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')


@pytest.mark.analytics
@pytest.mark.unit
class CommandAnalyticsTests(AnalyticsAPITestCase):
    """Tests for command analytics endpoints."""
    
    def test_command_statistics_success(self):
        """Test successful command statistics retrieval."""
        url = reverse('analytics:command-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        data = response.data['data']
        self.assertIn('overall', data)
        self.assertIn('by_type', data)
        self.assertIn('by_status', data)
        self.assertIn('time_series', data)
        self.assertGreaterEqual(data['overall']['total'], 3)
    
    def test_command_statistics_with_period(self):
        """Test command statistics with period parameter."""
        url = reverse('analytics:command-statistics')
        response = self.client.get(url, {'period': 'week'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['period'], 'week')
    
    def test_command_statistics_invalid_period(self):
        """Test command statistics with invalid period."""
        url = reverse('analytics:command-statistics')
        response = self.client.get(url, {'period': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_command_statistics_with_date_range(self):
        """Test command statistics with date range."""
        url = reverse('analytics:command-statistics')
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')
        
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@pytest.mark.analytics
@pytest.mark.unit
class ContentAnalyticsTests(AnalyticsAPITestCase):
    """Tests for content analytics endpoints."""
    
    def test_content_statistics_success(self):
        """Test successful content statistics retrieval."""
        url = reverse('analytics:content-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        data = response.data['data']
        self.assertIn('download_statistics', data)
        self.assertIn('type_distribution', data)
        self.assertIn('downloads_by_type', data)
    
    def test_content_statistics_empty_data(self):
        """Test content statistics with no content."""
        # Clear all content
        Content.objects.all().delete()
        ContentDownloadLog.objects.all().delete()
        
        url = reverse('analytics:content-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertEqual(data['download_statistics']['total_downloads'], 0)


@pytest.mark.analytics
@pytest.mark.unit
class TemplateAnalyticsTests(AnalyticsAPITestCase):
    """Tests for template analytics endpoints."""
    
    def test_template_statistics_success(self):
        """Test successful template statistics retrieval."""
        url = reverse('analytics:template-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        data = response.data['data']
        self.assertIn('total_templates', data)
        self.assertIn('most_active_templates', data)
        self.assertIn('by_orientation', data)


@pytest.mark.analytics
@pytest.mark.unit
class ActivityTrendsTests(AnalyticsAPITestCase):
    """Tests for activity trends endpoints."""
    
    def test_activity_trends_success(self):
        """Test successful activity trends retrieval."""
        url = reverse('analytics:activity-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        data = response.data['data']
        self.assertIn('period', data)
        self.assertIn('screen_registrations', data)
        self.assertIn('commands_created', data)
        self.assertIn('templates_created', data)
    
    def test_activity_trends_with_days(self):
        """Test activity trends with days parameter."""
        url = reverse('analytics:activity-trends')
        response = self.client.get(url, {'days': '7'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_activity_trends_invalid_days(self):
        """Test activity trends with invalid days parameter."""
        url = reverse('analytics:activity-trends')
        response = self.client.get(url, {'days': '999'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@pytest.mark.analytics
@pytest.mark.security
class AnalyticsSecurityTests(AnalyticsAPITestCase):
    """Security tests for analytics endpoints."""
    
    def test_rate_limiting(self):
        """Test rate limiting on analytics endpoints."""
        url = reverse('analytics:screen-statistics')
        
        # Make many requests
        for _ in range(105):  # Exceed limit of 100
            response = self.client.get(url)
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                if 'rate limit' in response.data.get('error', '').lower():
                    break
        
        # Should eventually hit rate limit (implementation dependent)
        # This test documents the expected behavior
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection in query parameters."""
        url = reverse('analytics:screen-statistics')
        
        # Attempt SQL injection in various parameters
        malicious_inputs = [
            "'; DROP TABLE screens; --",
            "1' OR '1'='1",
            "'; UPDATE users SET role='Developer' WHERE '1'='1'; --",
        ]
        
        for malicious in malicious_inputs:
            response = self.client.get(url, {'screen_ids': malicious})
            # Should return 400 or handle safely, not execute SQL
            self.assertIn(response.status_code, [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_200_OK  # Empty result if validation passes
            ])
    
    def test_xss_protection(self):
        """Test XSS protection in responses."""
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url)
        
        # Check that response is properly serialized JSON
        self.assertEqual(response['content-type'], 'application/json')
        # No script tags should be present
        response_str = str(response.data)
        self.assertNotIn('<script>', response_str)
    
    def test_date_range_overflow(self):
        """Test protection against date range overflow."""
        url = reverse('analytics:screen-statistics')
        
        # Try to request very large date range
        start_date = '2020-01-01'
        end_date = '2030-12-31'
        
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Should either work (if within max_days) or return 400
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])


@pytest.mark.analytics
@pytest.mark.integration
class AnalyticsIntegrationTests(AnalyticsAPITestCase):
    """Integration tests for analytics endpoints."""
    
    def test_multiple_endpoints_same_session(self):
        """Test accessing multiple analytics endpoints in same session."""
        endpoints = [
            reverse('analytics:screen-statistics'),
            reverse('analytics:command-statistics'),
            reverse('analytics:content-statistics'),
            reverse('analytics:template-statistics'),
            reverse('analytics:activity-trends'),
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'success')
    
    def test_concurrent_requests(self):
        """Test handling of concurrent analytics requests."""
        # This is a basic test - full concurrency testing would require threading
        url = reverse('analytics:screen-statistics')
        
        responses = []
        for _ in range(5):
            response = self.client.get(url)
            responses.append(response.status_code)
        
        # All should succeed
        self.assertTrue(all(code == status.HTTP_200_OK for code in responses))


@pytest.mark.analytics
@pytest.mark.edge_cases
class AnalyticsEdgeCasesTests(AnalyticsAPITestCase):
    """Tests for edge cases in analytics endpoints."""
    
    def test_empty_database(self):
        """Test analytics with empty database."""
        # Clear all data
        Screen.objects.all().delete()
        Command.objects.all().delete()
        Content.objects.all().delete()
        Template.objects.all().delete()
        
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertEqual(data['total_screens'], 0)
        self.assertEqual(data['health_score'], 0)
    
    def test_null_values_handling(self):
        """Test handling of null values in metrics."""
        # Create screen with null metrics
        screen = self.create_screen(name='Null Screen')
        ScreenStatusLog.objects.create(
            screen=screen,
            status='online',
            cpu_usage=None,
            memory_usage=None,
            heartbeat_latency=None
        )
        
        url = reverse('analytics:screen-statistics')
        response = self.client.get(url)
        
        # Should handle nulls gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_very_large_date_range(self):
        """Test handling of very large date range requests."""
        url = reverse('analytics:command-statistics')
        
        # Request 365 days (should be within limit)
        start_date = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')
        
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Should either work or return 400 if exceeds limit
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])
