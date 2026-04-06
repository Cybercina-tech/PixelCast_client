"""
Security helpers for screen communication.

Provides HMAC signature validation, timestamp validation, nonce tracking,
and other security mechanisms for secure command delivery to screens.
"""
import hmac
import hashlib
import time
import json
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings


class SecurityError(Exception):
    """Base exception for security-related errors"""
    pass


class InvalidSignatureError(SecurityError):
    """Raised when HMAC signature validation fails"""
    pass


class TimestampExpiredError(SecurityError):
    """Raised when message timestamp is too old"""
    pass


class ReplayAttackError(SecurityError):
    """Raised when nonce has been used before (replay attack)"""
    pass


class ScreenSecurity:
    """
    Security utilities for screen communication.
    
    Implements:
    - HMAC signature generation and validation
    - Timestamp validation (reject messages older than threshold)
    - Nonce-based replay protection
    - Rate limiting per screen
    """
    
    # Timestamp tolerance in seconds (messages older than this are rejected)
    TIMESTAMP_TOLERANCE = 300  # 5 minutes
    
    # Nonce cache timeout (how long to remember nonces)
    NONCE_CACHE_TIMEOUT = 3600  # 1 hour
    
    # Rate limiting: max commands per minute per screen
    RATE_LIMIT_COMMANDS_PER_MINUTE = 60
    
    @staticmethod
    def generate_signature(secret_key, payload, timestamp, nonce):
        """
        Generate HMAC-SHA256 signature for payload.
        
        Args:
            secret_key: Screen's secret key
            payload: Command payload (dict)
            timestamp: Unix timestamp
            nonce: Unique nonce string
            
        Returns:
            str: Hexadecimal signature
        """
        # Create message string: timestamp|nonce|json_payload
        message = f"{timestamp}|{nonce}|{json.dumps(payload, sort_keys=True)}"
        
        # Generate HMAC-SHA256
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def validate_signature(secret_key, payload, timestamp, nonce, received_signature):
        """
        Validate HMAC signature.
        
        Args:
            secret_key: Screen's secret key
            payload: Command payload (dict)
            timestamp: Unix timestamp
            nonce: Unique nonce string
            received_signature: Signature received from screen
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            InvalidSignatureError: If signature is invalid
        """
        expected_signature = ScreenSecurity.generate_signature(
            secret_key, payload, timestamp, nonce
        )
        
        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected_signature, received_signature):
            raise InvalidSignatureError("Invalid HMAC signature")
        
        return True
    
    @staticmethod
    def validate_timestamp(message_timestamp):
        """
        Validate that message timestamp is within acceptable range.
        
        Args:
            message_timestamp: Unix timestamp from message
            
        Returns:
            bool: True if timestamp is valid
            
        Raises:
            TimestampExpiredError: If timestamp is too old
        """
        current_time = time.time()
        time_difference = abs(current_time - message_timestamp)
        
        if time_difference > ScreenSecurity.TIMESTAMP_TOLERANCE:
            raise TimestampExpiredError(
                f"Message timestamp is too old or too far in future. "
                f"Difference: {time_difference:.2f}s, max allowed: {ScreenSecurity.TIMESTAMP_TOLERANCE}s"
            )
        
        return True
    
    @staticmethod
    def check_nonce(screen_id, nonce):
        """
        Check if nonce has been used before (replay protection).
        
        Args:
            screen_id: Screen UUID string
            nonce: Nonce string to check
            
        Returns:
            bool: True if nonce is valid (not used before)
            
        Raises:
            ReplayAttackError: If nonce has been used before
        """
        cache_key = f"screen_nonce:{screen_id}:{nonce}"
        
        # Check if nonce exists in cache
        if cache.get(cache_key):
            raise ReplayAttackError(f"Nonce {nonce} has been used before (replay attack detected)")
        
        # Store nonce in cache
        cache.set(cache_key, True, ScreenSecurity.NONCE_CACHE_TIMEOUT)
        
        return True
    
    @staticmethod
    def check_rate_limit(screen_id):
        """
        Check rate limiting for screen.
        
        Args:
            screen_id: Screen UUID string
            
        Returns:
            bool: True if within rate limit
            
        Raises:
            SecurityError: If rate limit exceeded
        """
        cache_key = f"screen_rate_limit:{screen_id}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= ScreenSecurity.RATE_LIMIT_COMMANDS_PER_MINUTE:
            raise SecurityError(
                f"Rate limit exceeded for screen {screen_id}. "
                f"Max {ScreenSecurity.RATE_LIMIT_COMMANDS_PER_MINUTE} commands per minute."
            )
        
        # Increment counter (expires in 60 seconds)
        cache.set(cache_key, current_count + 1, 60)
        
        return True
    
    @staticmethod
    def validate_message(secret_key, screen_id, payload, timestamp, nonce, signature):
        """
        Comprehensive message validation.
        
        Validates:
        - HMAC signature
        - Timestamp
        - Nonce (replay protection)
        - Rate limiting
        
        Args:
            secret_key: Screen's secret key
            screen_id: Screen UUID string
            payload: Command payload (dict)
            timestamp: Unix timestamp
            nonce: Unique nonce string
            signature: HMAC signature
            
        Returns:
            bool: True if all validations pass
            
        Raises:
            SecurityError: If any validation fails
        """
        # Validate signature
        ScreenSecurity.validate_signature(secret_key, payload, timestamp, nonce, signature)
        
        # Validate timestamp
        ScreenSecurity.validate_timestamp(timestamp)
        
        # Check nonce (replay protection)
        ScreenSecurity.check_nonce(screen_id, nonce)
        
        # Check rate limit
        ScreenSecurity.check_rate_limit(screen_id)
        
        return True
    
    @staticmethod
    def create_signed_payload(secret_key, payload):
        """
        Create a signed payload for sending to screen.
        
        Args:
            secret_key: Screen's secret key
            payload: Command payload (dict)
            
        Returns:
            dict: Payload with signature, timestamp, and nonce
        """
        import uuid
        
        timestamp = int(time.time())
        nonce = str(uuid.uuid4())
        
        signature = ScreenSecurity.generate_signature(
            secret_key, payload, timestamp, nonce
        )
        
        return {
            'payload': payload,
            'timestamp': timestamp,
            'nonce': nonce,
            'signature': signature
        }

