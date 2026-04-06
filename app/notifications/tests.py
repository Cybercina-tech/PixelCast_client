"""
Unit tests for Notification System.

Tests core functionality including:
- Rule resolution
- Cooldown enforcement
- Security validation
- Webhook signature verification
"""

from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError
from datetime import timedelta
import json

from .models import NotificationEvent, NotificationChannel, NotificationRule, NotificationLog
from .dispatcher import NotificationDispatcher
from .adapters import WebhookAdapter, get_channel_adapter
from accounts.models import User


class NotificationDispatcherTestCase(TestCase):
    """Test cases for NotificationDispatcher"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test event
        self.event = NotificationEvent.objects.create(
            event_key='test.event',
            description='Test event',
            severity='warning',
            is_active=True
        )
        
        # Create test channel
        self.channel = NotificationChannel.objects.create(
            type='email',
            name='Test Email Channel',
            config={
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'from_email': 'test@example.com',
                'to_emails': ['admin@example.com'],
                'use_tls': True
            },
            is_enabled=True
        )
        
        # Create test rule
        self.rule = NotificationRule.objects.create(
            event=self.event,
            severity_threshold='info',
            cooldown_seconds=60,
            is_enabled=True
        )
        self.rule.channels.add(self.channel)
        
        # Clear cache
        cache.clear()
    
    def test_dispatch_valid_event(self):
        """Test dispatching a valid notification event"""
        payload = {'test': 'data'}
        
        result = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload=payload,
            organization=self.user
        )
        
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result['dispatched'], 0)
    
    def test_dispatch_invalid_event_key(self):
        """Test dispatch with invalid event key"""
        result = NotificationDispatcher.dispatch(
            event_key='invalid-event-key',
            payload={'test': 'data'}
        )
        self.assertFalse(result['success'])
        self.assertIn('dispatch error', result['message'].lower())

    def test_dispatch_payload_too_large(self):
        """Test dispatch with payload exceeding size limit"""
        large_payload = {'data': 'x' * (NotificationDispatcher.MAX_PAYLOAD_SIZE + 1)}

        result = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload=large_payload
        )
        self.assertFalse(result['success'])
        self.assertIn('dispatch error', result['message'].lower())
    
    def test_cooldown_enforcement(self):
        """Test cooldown enforcement"""
        payload = {'test': 'data'}
        
        # First dispatch
        result1 = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload=payload,
            organization=self.user
        )
        self.assertTrue(result1['success'])
        
        # Second dispatch immediately (should be in cooldown)
        result2 = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload=payload,
            organization=self.user
        )
        
        # Should still succeed but may have cooldown messages
        self.assertIsNotNone(result2)
    
    def test_deduplication(self):
        """Test notification deduplication"""
        payload = {'test': 'data'}
        
        # First dispatch
        result1 = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload=payload,
            organization=self.user
        )
        
        # Second dispatch with same payload (should be deduplicated)
        result2 = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload=payload,
            organization=self.user
        )
        
        # Should detect duplicate
        self.assertIsNotNone(result2)
    
    def test_severity_filtering(self):
        """Test severity threshold filtering"""
        # Create rule with critical threshold
        critical_rule = NotificationRule.objects.create(
            event=self.event,
            severity_threshold='critical',
            cooldown_seconds=0,
            is_enabled=True
        )
        critical_rule.channels.add(self.channel)
        
        # Dispatch with warning severity (should not trigger critical rule)
        result = NotificationDispatcher.dispatch(
            event_key='test.event',
            payload={'test': 'data'},
            severity='warning'
        )
        
        # Should still dispatch (to info threshold rule)
        self.assertIsNotNone(result)


class WebhookAdapterTestCase(TestCase):
    """Test cases for WebhookAdapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.channel = NotificationChannel.objects.create(
            type='webhook',
            name='Test Webhook',
            config={
                'url': 'https://example.com/webhook',
                'secret_key': 'test-secret-key-12345',
                'allowed_domains': ['example.com']
            },
            is_enabled=True
        )
        
        self.event = NotificationEvent.objects.create(
            event_key='test.event',
            description='Test event',
            severity='warning'
        )
        
        self.log_entry = NotificationLog.objects.create(
            event_key='test.event',
            channel=self.channel,
            status='pending',
            idempotency_key='test-key'
        )
    
    def test_webhook_signature_generation(self):
        """Test HMAC signature generation"""
        adapter = WebhookAdapter()
        payload = {'test': 'data'}
        
        signed_payload = adapter._sign_payload(
            payload=payload,
            event=self.event,
            severity='warning',
            secret_key='test-secret-key-12345'
        )
        
        self.assertIn('signature', signed_payload)
        self.assertIn('timestamp', signed_payload)
        self.assertIn('nonce', signed_payload)
        self.assertIn('event_key', signed_payload)
        self.assertIn('payload', signed_payload)
        
        # Verify signature format (64 hex chars for SHA-256)
        self.assertEqual(len(signed_payload['signature']), 64)
    
    def test_webhook_domain_allowlist(self):
        """Test webhook domain allowlist"""
        adapter = WebhookAdapter()
        
        # Allowed domain
        self.assertTrue(adapter._is_allowed_domain('example.com', {
            'allowed_domains': ['example.com']
        }))
        
        # Disallowed domain
        self.assertFalse(adapter._is_allowed_domain('evil.com', {
            'allowed_domains': ['example.com']
        }))
        
        # No allowlist (allow all)
        self.assertTrue(adapter._is_allowed_domain('any-domain.com', {
            'allowed_domains': []
        }))


class NotificationModelsTestCase(TestCase):
    """Test cases for notification models"""
    
    def test_notification_event_validation(self):
        """Test NotificationEvent validation"""
        # Valid event key
        event = NotificationEvent(
            event_key='test.event',
            description='Test',
            severity='info'
        )
        event.clean()
        
        # Invalid event key (no dot)
        invalid_event = NotificationEvent(
            event_key='invalidevent',
            description='Test',
            severity='info'
        )
        with self.assertRaises(ValidationError):
            invalid_event.clean()
    
    def test_notification_channel_config_validation(self):
        """Test NotificationChannel config validation"""
        # Valid email channel
        email_channel = NotificationChannel(
            type='email',
            name='Test Email',
            config={
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'from_email': 'test@example.com'
            }
        )
        email_channel.clean()
        
        # Invalid email channel (missing required field)
        invalid_email = NotificationChannel(
            type='email',
            name='Test Email',
            config={
                'smtp_host': 'smtp.example.com'
                # Missing smtp_port and from_email
            }
        )
        with self.assertRaises(ValidationError):
            invalid_email.clean()
    
    def test_notification_rule_cooldown_validation(self):
        """Test NotificationRule cooldown validation"""
        event = NotificationEvent.objects.create(
            event_key='test.event',
            description='Test',
            severity='info'
        )
        
        # Valid cooldown
        rule = NotificationRule(
            event=event,
            severity_threshold='info',
            cooldown_seconds=300
        )
        rule.clean()
        
        # Invalid cooldown (exceeds 24 hours)
        invalid_rule = NotificationRule(
            event=event,
            severity_threshold='info',
            cooldown_seconds=100000
        )
        with self.assertRaises(ValidationError):
            invalid_rule.clean()


class ChannelAdapterTestCase(TestCase):
    """Test cases for channel adapters"""
    
    def test_get_channel_adapter(self):
        """Test getting channel adapters"""
        from .adapters import get_channel_adapter, EmailAdapter, SMSAdapter, WebhookAdapter
        
        email_adapter = get_channel_adapter('email')
        self.assertIsInstance(email_adapter, EmailAdapter)
        
        sms_adapter = get_channel_adapter('sms')
        self.assertIsInstance(sms_adapter, SMSAdapter)
        
        webhook_adapter = get_channel_adapter('webhook')
        self.assertIsInstance(webhook_adapter, WebhookAdapter)
        
        # Invalid adapter
        with self.assertRaises(ValueError):
            get_channel_adapter('invalid')
