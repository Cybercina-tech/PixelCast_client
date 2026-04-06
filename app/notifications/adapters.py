"""
Channel Adapters for Notification Delivery.

Provides secure, provider-agnostic adapters for:
- Email (SMTP)
- SMS (Twilio/Generic)
- Webhook (HTTP with HMAC signing)
"""

import hmac
import hashlib
import json
import logging
import time
import secrets
from typing import Dict, Any, Optional
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from django.utils import timezone
import requests
from urllib.parse import urlparse

from .models import NotificationChannel, NotificationEvent, NotificationLog

logger = logging.getLogger(__name__)


class BaseAdapter:
    """Base class for all channel adapters"""
    
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    
    def send(
        self,
        log_entry: NotificationLog,
        channel: NotificationChannel,
        event: NotificationEvent,
        payload: Dict[str, Any],
        severity: str
    ) -> Dict[str, Any]:
        """
        Send notification via this adapter.
        
        Args:
            log_entry: Notification log entry
            channel: Channel configuration
            event: Event that triggered notification
            payload: Event payload
            severity: Event severity
            
        Returns:
            Dict with success status and response/error
        """
        raise NotImplementedError
    
    def _sanitize_response(self, response: Any) -> str:
        """Sanitize provider response to remove secrets"""
        if isinstance(response, str):
            # Remove potential secrets
            sanitized = response
            forbidden_patterns = ['password', 'secret', 'token', 'key', 'api_key', 'auth']
            for pattern in forbidden_patterns:
                # Simple sanitization - can be enhanced
                sanitized = sanitized.replace(pattern, '[REDACTED]')
            return sanitized[:1000]  # Limit length
        return str(response)[:1000]
    
    def _mask_pii(self, text: str) -> str:
        """Mask PII in text"""
        # Simple PII masking - can be enhanced
        import re
        # Mask email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        # Mask phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        return text


class EmailAdapter(BaseAdapter):
    """Email adapter using Django's SMTP backend"""
    
    def send(
        self,
        log_entry: NotificationLog,
        channel: NotificationChannel,
        event: NotificationEvent,
        payload: Dict[str, Any],
        severity: str
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            config = channel.config
            to_emails = config.get('to_emails', [])
            if not to_emails:
                return {
                    'success': False,
                    'error': 'Missing required email configuration (to_emails)',
                }

            use_system = bool(config.get('use_system_smtp'))
            if use_system:
                from core.email_service import get_system_email_connection, resolve_default_from_email

                from_email = (config.get('from_email') or '').strip() or resolve_default_from_email()
                conn = get_system_email_connection()
            else:
                smtp_host = config.get('smtp_host')
                smtp_port = config.get('smtp_port', 587)
                from_email = config.get('from_email')
                use_tls = config.get('use_tls', True)
                use_ssl = config.get('use_ssl', False)
                username = config.get('username')
                password = config.get('password')
                if not all([smtp_host, from_email]):
                    return {
                        'success': False,
                        'error': 'Missing required email configuration',
                    }
                conn = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=smtp_host,
                    port=int(smtp_port),
                    username=username or None,
                    password=password or None,
                    use_tls=use_tls,
                    use_ssl=use_ssl,
                    fail_silently=False,
                )

            subject = self._build_subject(event, severity, payload)
            message = self._build_message(event, payload, severity)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=to_emails,
                connection=conn,
            )
            msg.send(fail_silently=False)

            return {
                'success': True,
                'response': f"Email sent to {len(to_emails)} recipient(s)",
            }
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Email delivery failed: {error_msg}")
            return {
                'success': False,
                'error': self._mask_pii(error_msg)
            }
    
    def _build_subject(self, event: NotificationEvent, severity: str, payload: Dict[str, Any]) -> str:
        """Build email subject"""
        severity_prefix = {
            'critical': '[CRITICAL]',
            'warning': '[WARNING]',
            'info': '[INFO]'
        }.get(severity, '[INFO]')
        
        return f"{severity_prefix} PixelCast Signage Alert: {event.event_key}"
    
    def _build_message(self, event: NotificationEvent, payload: Dict[str, Any], severity: str) -> str:
        """Build email message body"""
        lines = [
            f"Event: {event.event_key}",
            f"Severity: {severity.upper()}",
            f"Description: {event.description}",
            "",
            "Payload:",
            json.dumps(payload, indent=2)
        ]
        return "\n".join(lines)


class SMSAdapter(BaseAdapter):
    """SMS adapter using Twilio or generic HTTP API"""
    
    def send(
        self,
        log_entry: NotificationLog,
        channel: NotificationChannel,
        event: NotificationEvent,
        payload: Dict[str, Any],
        severity: str
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            config = channel.config
            provider = config.get('provider', 'twilio')
            
            if provider == 'twilio':
                return self._send_twilio(config, event, payload, severity)
            else:
                return self._send_generic(config, event, payload, severity)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SMS delivery failed: {error_msg}")
            return {
                'success': False,
                'error': self._mask_pii(error_msg)
            }
    
    def _send_twilio(self, config: Dict[str, Any], event: NotificationEvent, payload: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = config.get('account_sid')
            auth_token = config.get('auth_token')
            from_number = config.get('from_number')
            to_numbers = config.get('to_numbers', [])
            
            if not all([account_sid, auth_token, from_number, to_numbers]):
                return {
                    'success': False,
                    'error': 'Missing required Twilio configuration'
                }
            
            client = Client(account_sid, auth_token)
            
            # Build message
            message = self._build_sms_message(event, payload, severity)
            
            # Send to all recipients
            results = []
            for to_number in to_numbers:
                try:
                    twilio_message = client.messages.create(
                        body=message,
                        from_=from_number,
                        to=to_number
                    )
                    results.append({
                        'to': to_number,
                        'sid': twilio_message.sid,
                        'status': twilio_message.status
                    })
                except Exception as e:
                    results.append({
                        'to': to_number,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'response': f"SMS sent to {len(results)} recipient(s)"
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'Twilio library not installed'
            }
    
    def _send_generic(self, config: Dict[str, Any], event: NotificationEvent, payload: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Send SMS via generic HTTP API"""
        api_url = config.get('api_url')
        api_key = config.get('api_key')
        to_numbers = config.get('to_numbers', [])
        
        if not all([api_url, api_key, to_numbers]):
            return {
                'success': False,
                'error': 'Missing required generic SMS configuration'
            }
        
        message = self._build_sms_message(event, payload, severity)
        
        try:
            response = requests.post(
                api_url,
                json={
                    'to': to_numbers,
                    'message': message,
                    'api_key': api_key
                },
                timeout=self.TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'response': self._sanitize_response(response.text)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_sms_message(self, event: NotificationEvent, payload: Dict[str, Any], severity: str) -> str:
        """Build SMS message (max 160 chars)"""
        severity_prefix = {
            'critical': '[CRIT]',
            'warning': '[WARN]',
            'info': '[INFO]'
        }.get(severity, '[INFO]')
        
        # Truncate to fit SMS length
        message = f"{severity_prefix} {event.event_key}"
        if len(message) < 140:
            # Add key payload info
            payload_str = json.dumps(payload)[:140-len(message)-3]
            message += f": {payload_str}"
        
        return message[:160]


class WebhookAdapter(BaseAdapter):
    """Webhook adapter with HMAC signing and security"""
    
    def send(
        self,
        log_entry: NotificationLog,
        channel: NotificationChannel,
        event: NotificationEvent,
        payload: Dict[str, Any],
        severity: str
    ) -> Dict[str, Any]:
        """Send webhook notification with HMAC signing"""
        try:
            config = channel.config
            url = config.get('url')
            secret_key = config.get('secret_key')
            
            if not all([url, secret_key]):
                return {
                    'success': False,
                    'error': 'Missing required webhook configuration'
                }
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme in ('http', 'https'):
                return {
                    'success': False,
                    'error': 'Invalid webhook URL scheme'
                }
            
            # Enforce HTTPS in production
            if not settings.DEBUG and parsed_url.scheme != 'https':
                return {
                    'success': False,
                    'error': 'Webhook URL must use HTTPS in production'
                }
            
            # Check domain allowlist (if configured)
            if not self._is_allowed_domain(parsed_url.netloc, config):
                return {
                    'success': False,
                    'error': 'Webhook domain not in allowlist'
                }
            
            # Build signed payload
            signed_payload = self._sign_payload(payload, event, severity, secret_key)
            
            # Send webhook
            response = requests.post(
                url,
                json=signed_payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'PixelCastSignage-Notifications/1.0'
                },
                timeout=self.TIMEOUT_SECONDS,
                allow_redirects=False
            )
            
            response.raise_for_status()
            
            return {
                'success': True,
                'response': self._sanitize_response(response.text)
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f"Webhook delivery failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Webhook error: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def _sign_payload(
        self,
        payload: Dict[str, Any],
        event: NotificationEvent,
        severity: str,
        secret_key: str
    ) -> Dict[str, Any]:
        """Sign payload with HMAC-SHA256"""
        timestamp = int(time.time())
        nonce = secrets.token_urlsafe(16)
        
        # Build payload to sign
        payload_to_sign = {
            'event_key': event.event_key,
            'severity': severity,
            'timestamp': timestamp,
            'nonce': nonce,
            'payload': payload
        }
        
        # Create signature
        message = json.dumps(payload_to_sign, sort_keys=True)
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'signature': signature,
            'timestamp': timestamp,
            'nonce': nonce,
            'event_key': event.event_key,
            'severity': severity,
            'payload': payload
        }
    
    def _is_allowed_domain(self, domain: str, config: Dict[str, Any]) -> bool:
        """Check if domain is in allowlist"""
        allowlist = config.get('allowed_domains', [])
        
        # If no allowlist, allow all (can be restricted in production)
        if not allowlist:
            return True
        
        # Check domain
        domain_lower = domain.lower()
        for allowed in allowlist:
            if domain_lower == allowed.lower() or domain_lower.endswith('.' + allowed.lower()):
                return True
        
        return False


def get_channel_adapter(channel_type: str) -> BaseAdapter:
    """Get adapter for channel type"""
    adapters = {
        'email': EmailAdapter(),
        'sms': SMSAdapter(),
        'webhook': WebhookAdapter(),
    }
    
    adapter = adapters.get(channel_type)
    if not adapter:
        raise ValueError(f"Unknown channel type: {channel_type}")
    
    return adapter

