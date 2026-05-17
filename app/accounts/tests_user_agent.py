"""Tests for User-Agent parsing used in active sessions."""

from django.test import TestCase

from .user_agent import parse_user_agent, session_device_fields


class UserAgentParseTests(TestCase):
    def test_chrome_windows(self):
        ua = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
        )
        parsed = parse_user_agent(ua)
        self.assertEqual(parsed['browser'], 'Chrome')
        self.assertIn('Windows', parsed['os'] or '')
        self.assertEqual(parsed['device_type'], 'desktop')
        self.assertIn('Chrome', parsed['label'])
        self.assertIn('Windows', parsed['label'])

    def test_iphone_safari(self):
        ua = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
        )
        parsed = parse_user_agent(ua)
        self.assertEqual(parsed['device_type'], 'mobile')
        self.assertIn('iOS', parsed['os'] or '')

    def test_empty_ua(self):
        parsed = parse_user_agent('')
        self.assertEqual(parsed['label'], 'Unknown device')
        fields = session_device_fields('')
        self.assertEqual(fields['device'], 'Unknown device')
