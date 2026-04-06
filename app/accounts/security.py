"""
Security utilities for user management.

Provides functions for account lockout, password validation, and security checks.
"""
import time
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Account lockout configuration
ACCOUNT_LOCKOUT_ENABLED = getattr(settings, 'ACCOUNT_LOCKOUT_ENABLED', True)
MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
LOCKOUT_DURATION = getattr(settings, 'LOCKOUT_DURATION', 900)  # 15 minutes in seconds


class AccountLockoutManager:
    """Manages account lockout after failed login attempts."""
    
    @staticmethod
    def get_lockout_key(identifier):
        """Generate cache key for lockout tracking."""
        return f'account_lockout:{identifier}'
    
    @staticmethod
    def get_attempt_key(identifier):
        """Generate cache key for login attempt tracking."""
        return f'login_attempts:{identifier}'

    @staticmethod
    def get_lockout_until_key(identifier):
        """Generate cache key for lockout expiry timestamp."""
        return f'account_lockout_until:{identifier}'
    
    @classmethod
    def record_failed_attempt(cls, identifier):
        """
        Record a failed login attempt.
        
        Args:
            identifier: User identifier (username, email, or IP address)
        
        Returns:
            tuple: (is_locked, remaining_attempts)
        """
        if not ACCOUNT_LOCKOUT_ENABLED:
            return False, 0
        
        attempt_key = cls.get_attempt_key(identifier)
        lockout_key = cls.get_lockout_key(identifier)
        lockout_until_key = cls.get_lockout_until_key(identifier)
        
        # Check if account is already locked
        if cache.get(lockout_key):
            return True, 0
        
        # Increment failed attempts
        attempts = cache.get(attempt_key, 0) + 1
        cache.set(attempt_key, attempts, timeout=LOCKOUT_DURATION)
        
        # Lock account if max attempts reached
        if attempts >= MAX_LOGIN_ATTEMPTS:
            cache.set(lockout_key, True, timeout=LOCKOUT_DURATION)
            lockout_until = int(time.time()) + LOCKOUT_DURATION
            cache.set(lockout_until_key, lockout_until, timeout=LOCKOUT_DURATION)
            logger.warning(f'Account locked due to failed login attempts: {identifier}')
            return True, 0
        
        remaining = MAX_LOGIN_ATTEMPTS - attempts
        return False, remaining
    
    @classmethod
    def clear_failed_attempts(cls, identifier):
        """Clear failed login attempts after successful login."""
        if not ACCOUNT_LOCKOUT_ENABLED:
            return
        
        attempt_key = cls.get_attempt_key(identifier)
        lockout_key = cls.get_lockout_key(identifier)
        lockout_until_key = cls.get_lockout_until_key(identifier)
        
        cache.delete(attempt_key)
        cache.delete(lockout_key)
        cache.delete(lockout_until_key)
    
    @classmethod
    def is_locked(cls, identifier):
        """Check if account is locked."""
        if not ACCOUNT_LOCKOUT_ENABLED:
            return False
        
        lockout_key = cls.get_lockout_key(identifier)
        return bool(cache.get(lockout_key))
    
    @classmethod
    def get_remaining_lockout_time(cls, identifier):
        """Get remaining lockout time in seconds."""
        if not ACCOUNT_LOCKOUT_ENABLED:
            return 0
        
        if not cls.is_locked(identifier):
            return 0

        lockout_until = cache.get(cls.get_lockout_until_key(identifier))
        if lockout_until is None:
            # Fallback when backend doesn't preserve custom timestamp.
            return LOCKOUT_DURATION

        try:
            remaining = int(lockout_until) - int(time.time())
        except (ValueError, TypeError):
            return LOCKOUT_DURATION

        return max(0, remaining)


class PasswordStrengthChecker:
    """Enhanced password strength checking."""
    
    @staticmethod
    def check_password_strength(password):
        """
        Check password strength and return score (0-4).
        
        Returns:
            dict: {
                'score': int (0-4),
                'feedback': list of str,
                'is_strong': bool
            }
        """
        score = 0
        feedback = []
        
        if not password:
            return {
                'score': 0,
                'feedback': ['Password cannot be empty'],
                'is_strong': False
            }
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append('Use at least 8 characters')
        
        if len(password) >= 12:
            score += 1
        
        # Character variety
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        
        if char_types >= 3:
            score += 1
        else:
            if not has_lower:
                feedback.append('Add lowercase letters')
            if not has_upper:
                feedback.append('Add uppercase letters')
            if not has_digit:
                feedback.append('Add numbers')
            if not has_special:
                feedback.append('Add special characters')
        
        if char_types == 4:
            score += 1
        
        # Common patterns check
        common_patterns = ['12345', 'abcde', 'qwerty', 'password', 'admin']
        password_lower = password.lower()
        if any(pattern in password_lower for pattern in common_patterns):
            feedback.append('Avoid common patterns')
        
        return {
            'score': min(score, 4),
            'feedback': feedback,
            'is_strong': score >= 3
        }


def sanitize_input(value):
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        value: Input value (string or None)
    
    Returns:
        Sanitized string
    """
    if not value:
        return value
    
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Trim whitespace
    value = value.strip()
    
    # Limit length (prevent DoS)
    max_length = 1000
    if len(value) > max_length:
        value = value[:max_length]
        logger.warning(f'Input truncated to {max_length} characters')
    
    return value


def prevent_user_enumeration():
    """
    Decorator/helper to prevent user enumeration attacks.
    
    Always returns the same response format for authentication failures,
    regardless of whether the user exists or not.
    """
    # This is handled in the serializer by not revealing user existence
    pass
