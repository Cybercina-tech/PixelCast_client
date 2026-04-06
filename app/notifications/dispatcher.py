"""
Notification Dispatcher for PixelCast Signage Digital Signage System.

Handles event-driven notification delivery with:
- Rule resolution
- Cooldown enforcement
- Severity filtering
- Deduplication
- Channel adapter routing
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
from django.conf import settings

from .models import NotificationEvent, NotificationRule, NotificationChannel, NotificationLog

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """
    Central dispatcher for notification delivery.
    
    Accepts events and dispatches them to appropriate channels based on rules.
    Enforces cooldowns, severity filtering, and deduplication.
    """
    
    # Maximum payload size (10 KB)
    MAX_PAYLOAD_SIZE = 10 * 1024
    
    # Cooldown cache prefix
    COOLDOWN_CACHE_PREFIX = "notification_cooldown:"
    
    # Deduplication cache prefix
    DEDUP_CACHE_PREFIX = "notification_dedup:"
    
    # Deduplication window (5 minutes)
    DEDUP_WINDOW_SECONDS = 300
    
    @classmethod
    def dispatch(
        cls,
        event_key: str,
        payload: Dict[str, Any],
        organization: Optional[Any] = None,
        severity: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch a notification event.
        
        Args:
            event_key: Event identifier (e.g., 'screen.offline')
            payload: Event payload (must be JSON-serializable, max 10KB)
            organization: Optional organization/user to scope rules
            severity: Optional severity override
            force: If True, bypass cooldown and deduplication
            
        Returns:
            Dict with dispatch results
        """
        try:
            # Validate inputs
            cls._validate_event_key(event_key)
            cls._validate_payload(payload)
            
            # Get event
            try:
                event = NotificationEvent.objects.get(event_key=event_key, is_active=True)
            except NotificationEvent.DoesNotExist:
                logger.warning(f"Event '{event_key}' not found or inactive")
                return {
                    'success': False,
                    'message': f"Event '{event_key}' not found or inactive",
                    'dispatched': 0
                }
            
            # Use event severity if not provided
            if severity is None:
                severity = event.severity
            
            # Resolve applicable rules
            rules = cls._resolve_rules(event, organization, severity)
            
            if not rules:
                logger.debug(f"No rules found for event '{event_key}'")
                return {
                    'success': True,
                    'message': "No applicable rules found",
                    'dispatched': 0
                }
            
            # Generate idempotency key
            idempotency_key = cls._generate_idempotency_key(event_key, payload, organization)
            
            # Check deduplication (unless forced)
            if not force:
                if cls._is_duplicate(idempotency_key):
                    logger.debug(f"Duplicate notification detected: {idempotency_key}")
                    return {
                        'success': True,
                        'message': "Duplicate notification suppressed",
                        'dispatched': 0,
                        'idempotency_key': idempotency_key
                    }
            
            # Dispatch to each rule
            results = {
                'success': True,
                'message': f"Dispatched to {len(rules)} rule(s)",
                'dispatched': 0,
                'failed': 0,
                'idempotency_key': idempotency_key,
                'details': []
            }
            
            for rule in rules:
                # Check cooldown (unless forced)
                if not force:
                    if cls._is_in_cooldown(rule, event_key, organization):
                        logger.debug(f"Rule {rule.id} in cooldown for event '{event_key}'")
                        results['details'].append({
                            'rule_id': str(rule.id),
                            'status': 'cooldown',
                            'message': 'Rule in cooldown period'
                        })
                        continue
                
                # Dispatch to channels
                rule_result = cls._dispatch_to_rule(rule, event, payload, idempotency_key, severity)
                results['details'].append(rule_result)
                
                if rule_result['success']:
                    results['dispatched'] += rule_result['dispatched']
                    # Set cooldown
                    if not force:
                        cls._set_cooldown(rule, event_key, organization)
                else:
                    results['failed'] += 1
                    results['success'] = False
            
            # Mark deduplication (unless forced)
            if not force:
                cls._mark_deduplication(idempotency_key)
            
            return results
            
        except Exception as e:
            logger.error(f"Error dispatching notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Dispatch error: {str(e)}",
                'dispatched': 0
            }
    
    @classmethod
    def _validate_event_key(cls, event_key: str) -> None:
        """Validate event key format and security"""
        if not isinstance(event_key, str):
            raise ValueError("event_key must be a string")
        
        if len(event_key) > 100:
            raise ValueError("event_key exceeds maximum length")
        
        # Security: only allow alphanumeric, dots, underscores, hyphens
        if not all(c.isalnum() or c in ('.', '_', '-') for c in event_key):
            raise ValueError("event_key contains invalid characters")
        
        # Must follow pattern: category.action
        if '.' not in event_key:
            raise ValueError("event_key must follow pattern: 'category.action'")
    
    @classmethod
    def _validate_payload(cls, payload: Dict[str, Any]) -> None:
        """Validate payload size and structure"""
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")
        
        # Check payload size
        import json
        payload_str = json.dumps(payload)
        if len(payload_str.encode('utf-8')) > cls.MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload exceeds maximum size ({cls.MAX_PAYLOAD_SIZE} bytes)")
        
        # Sanitize: remove any potential secrets
        # This is a basic check - more sophisticated sanitization can be added
        forbidden_keys = ['password', 'secret', 'token', 'key', 'api_key', 'auth']
        for key in payload.keys():
            if any(forbidden in key.lower() for forbidden in forbidden_keys):
                logger.warning(f"Potential secret in payload key: {key}")
    
    @classmethod
    def _resolve_rules(
        cls,
        event: NotificationEvent,
        organization: Optional[Any],
        severity: str
    ) -> List[NotificationRule]:
        """Resolve applicable notification rules"""
        # Build query
        query = Q(
            event=event,
            is_enabled=True,
            channels__is_enabled=True
        )
        
        # Severity filtering: only rules with threshold <= event severity
        severity_order = {'info': 1, 'warning': 2, 'critical': 3}
        threshold_order = severity_order.get(severity, 1)
        
        # Filter by severity threshold
        query &= Q(
            severity_threshold__in=[
                s for s, order in severity_order.items()
                if order <= threshold_order
            ]
        )
        
        # Organization scoping
        if organization:
            query &= (Q(organization=organization) | Q(organization__isnull=True))
        else:
            query &= Q(organization__isnull=True)
        
        # Get rules
        rules = NotificationRule.objects.filter(query).distinct().select_related(
            'event', 'organization'
        ).prefetch_related('channels')
        
        return list(rules)
    
    @classmethod
    def _is_in_cooldown(
        cls,
        rule: NotificationRule,
        event_key: str,
        organization: Optional[Any]
    ) -> bool:
        """Check if rule is in cooldown period"""
        if rule.cooldown_seconds == 0:
            return False
        
        cache_key = f"{cls.COOLDOWN_CACHE_PREFIX}{rule.id}:{event_key}"
        if organization:
            cache_key += f":{organization.id}"
        
        return cache.get(cache_key) is not None
    
    @classmethod
    def _set_cooldown(
        cls,
        rule: NotificationRule,
        event_key: str,
        organization: Optional[Any]
    ) -> None:
        """Set cooldown for rule"""
        if rule.cooldown_seconds == 0:
            return
        
        cache_key = f"{cls.COOLDOWN_CACHE_PREFIX}{rule.id}:{event_key}"
        if organization:
            cache_key += f":{organization.id}"
        
        cache.set(cache_key, True, rule.cooldown_seconds)
    
    @classmethod
    def _is_duplicate(cls, idempotency_key: str) -> bool:
        """Check if notification is duplicate"""
        cache_key = f"{cls.DEDUP_CACHE_PREFIX}{idempotency_key}"
        return cache.get(cache_key) is not None
    
    @classmethod
    def _mark_deduplication(cls, idempotency_key: str) -> None:
        """Mark notification as sent for deduplication"""
        cache_key = f"{cls.DEDUP_CACHE_PREFIX}{idempotency_key}"
        cache.set(cache_key, True, cls.DEDUP_WINDOW_SECONDS)
    
    @classmethod
    def _generate_idempotency_key(
        cls,
        event_key: str,
        payload: Dict[str, Any],
        organization: Optional[Any]
    ) -> str:
        """Generate idempotency key for deduplication"""
        import json
        key_parts = [
            event_key,
            json.dumps(payload, sort_keys=True),
            str(organization.id) if organization else 'system'
        ]
        key_string = ':'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @classmethod
    def _dispatch_to_rule(
        cls,
        rule: NotificationRule,
        event: NotificationEvent,
        payload: Dict[str, Any],
        idempotency_key: str,
        severity: str
    ) -> Dict[str, Any]:
        """Dispatch notification to all channels in a rule"""
        from .tasks import send_notification_async
        
        result = {
            'rule_id': str(rule.id),
            'success': True,
            'dispatched': 0,
            'failed': 0,
            'details': []
        }
        
        channels = rule.channels.filter(is_enabled=True)
        
        for channel in channels:
            try:
                # Create log entry
                log_entry = NotificationLog.objects.create(
                    rule=rule,
                    event_key=event.event_key,
                    channel=channel,
                    status='pending',
                    idempotency_key=idempotency_key
                )
                
                # Dispatch async (or sync in development)
                if getattr(settings, 'NOTIFICATIONS_ASYNC', True):
                    # Use Celery task
                    send_notification_async.delay(
                        log_entry_id=str(log_entry.id),
                        channel_id=str(channel.id),
                        event_key=event.event_key,
                        payload=payload,
                        severity=severity
                    )
                else:
                    # Sync dispatch (for testing)
                    from .adapters import get_channel_adapter
                    adapter = get_channel_adapter(channel.type)
                    adapter_result = adapter.send(log_entry, channel, event, payload, severity)
                    
                    # Update log
                    log_entry.status = 'sent' if adapter_result['success'] else 'failed'
                    log_entry.provider_response = adapter_result.get('response', '')
                    log_entry.error_message = adapter_result.get('error', '')
                    if adapter_result['success']:
                        log_entry.sent_at = timezone.now()
                    log_entry.save()
                
                result['dispatched'] += 1
                result['details'].append({
                    'channel_id': str(channel.id),
                    'channel_type': channel.type,
                    'status': 'queued' if getattr(settings, 'NOTIFICATIONS_ASYNC', True) else 'sent'
                })
                
            except Exception as e:
                logger.error(f"Error dispatching to channel {channel.id}: {str(e)}")
                result['failed'] += 1
                result['success'] = False
                result['details'].append({
                    'channel_id': str(channel.id),
                    'channel_type': channel.type,
                    'status': 'error',
                    'error': str(e)
                })
        
        return result

