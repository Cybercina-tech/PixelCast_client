"""
Unified rate limiting system for PixelCast Signage.

Provides:
- Middleware for automatic rate limiting
- Configurable limits per user, IP, role, or endpoint
- HTTP 429 responses for rate limit violations
- Redis-based rate limiting with sliding window
"""
import time
from typing import Optional, Dict, Tuple
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """
    Centralized rate limiting utility with support for multiple strategies.
    """

    # Default limits
    DEFAULT_PER_MINUTE = 60
    DEFAULT_PER_HOUR = 1000
    DEFAULT_PER_DAY = 10000

    # Rate limit strategies
    STRATEGY_USER = 'user'
    STRATEGY_IP = 'ip'
    STRATEGY_ROLE = 'role'
    STRATEGY_ENDPOINT = 'endpoint'
    STRATEGY_COMBINED = 'combined'  # User + IP + Endpoint

    @classmethod
    def get_client_identifier(cls, request) -> Tuple[str, Optional[int], Optional[str]]:
        """
        Extract client identifier (IP, user, role) from request.

        Returns:
            Tuple of (ip_address, user_id, user_role)
        """
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')

        # Get user info
        user_id = None
        user_role = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            user_role = getattr(request.user, 'role', None)

        return ip, user_id, user_role

    @classmethod
    def get_rate_limit_key(
        cls,
        strategy: str,
        identifier: str,
        endpoint: Optional[str] = None,
        window: str = 'minute'
    ) -> str:
        """
        Generate cache key for rate limiting.

        Args:
            strategy: Rate limit strategy (user, ip, role, endpoint, combined)
            identifier: Identifier value (user_id, ip, role name, endpoint path)
            endpoint: Optional endpoint path
            window: Time window (minute, hour, day)

        Returns:
            Cache key string
        """
        window_seconds = {
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }.get(window, 60)

        timestamp = int(time.time() // window_seconds)

        if strategy == cls.STRATEGY_COMBINED and endpoint:
            return f"rate_limit:{strategy}:{identifier}:{endpoint}:{window}:{timestamp}"
        else:
            return f"rate_limit:{strategy}:{identifier}:{window}:{timestamp}"

    @classmethod
    def check_rate_limit(
        cls,
        request,
        endpoint: Optional[str] = None,
        strategy: str = STRATEGY_COMBINED,
        limit_per_minute: Optional[int] = None,
        limit_per_hour: Optional[int] = None,
        limit_per_day: Optional[int] = None,
        per_role_limits: Optional[Dict[str, Dict[str, int]]] = None
    ) -> Tuple[bool, Optional[Dict[str, int]]]:
        """
        Check if request is within rate limits.

        Args:
            request: Django request object
            endpoint: Optional endpoint path for endpoint-based limiting
            strategy: Rate limiting strategy
            limit_per_minute: Limit per minute (default from settings)
            limit_per_hour: Limit per hour (default from settings)
            limit_per_day: Limit per day (default from settings)
            per_role_limits: Optional dict mapping role to limits

        Returns:
            Tuple of (is_allowed, remaining_counts)
            remaining_counts: Dict with 'minute', 'hour', 'day' keys
        """
        ip, user_id, user_role = cls.get_client_identifier(request)

        # Get default limits from settings or use class defaults
        settings_config = getattr(settings, 'RATE_LIMITING', {})
        limit_per_minute = limit_per_minute or settings_config.get('DEFAULT_PER_MINUTE', cls.DEFAULT_PER_MINUTE)
        limit_per_hour = limit_per_hour or settings_config.get('DEFAULT_PER_HOUR', cls.DEFAULT_PER_HOUR)
        limit_per_day = limit_per_day or settings_config.get('DEFAULT_PER_DAY', cls.DEFAULT_PER_DAY)

        # Check role-specific limits
        if per_role_limits and user_role and user_role in per_role_limits:
            role_limits = per_role_limits[user_role]
            limit_per_minute = role_limits.get('per_minute', limit_per_minute)
            limit_per_hour = role_limits.get('per_hour', limit_per_hour)
            limit_per_day = role_limits.get('per_day', limit_per_day)

        # Determine identifier based on strategy
        if strategy == cls.STRATEGY_USER:
            if not user_id:
                return True, None  # No user, no rate limiting
            identifier = str(user_id)
        elif strategy == cls.STRATEGY_IP:
            identifier = ip
        elif strategy == cls.STRATEGY_ROLE:
            if not user_role:
                return True, None
            identifier = user_role
        elif strategy == cls.STRATEGY_ENDPOINT:
            identifier = endpoint or request.path
        elif strategy == cls.STRATEGY_COMBINED:
            # Combined: user:ip:endpoint
            parts = []
            if user_id:
                parts.append(f"user:{user_id}")
            parts.append(f"ip:{ip}")
            if endpoint:
                parts.append(f"endpoint:{endpoint}")
            identifier = ":".join(parts) if parts else ip
        else:
            identifier = ip  # Default to IP

        # Check all time windows
        windows = [
            ('minute', limit_per_minute, 60),
            ('hour', limit_per_hour, 3600),
            ('day', limit_per_day, 86400)
        ]

        remaining = {}
        is_allowed = True

        for window_name, limit, window_seconds in windows:
            key = cls.get_rate_limit_key(strategy, identifier, endpoint, window_name)

            try:
                current_count = cache.get(key, 0)

                if current_count >= limit:
                    is_allowed = False
                    remaining[window_name] = 0
                else:
                    remaining[window_name] = max(0, limit - current_count)

                # Increment counter
                cache.set(key, current_count + 1, window_seconds)

            except Exception as e:
                logger.error(f"Rate limit check error for key {key}: {e}")
                # On error, allow request (fail open)
                is_allowed = True
                remaining[window_name] = limit

        return is_allowed, remaining

    @classmethod
    def get_rate_limit_headers(cls, remaining: Optional[Dict[str, int]], limits: Dict[str, int]) -> Dict[str, str]:
        """
        Generate HTTP headers for rate limit information.

        Args:
            remaining: Dict with remaining counts
            limits: Dict with limit values

        Returns:
            Dict of HTTP headers
        """
        headers = {}

        if remaining:
            # X-RateLimit-Limit headers
            headers['X-RateLimit-Limit-Minute'] = str(limits.get('minute', 0))
            headers['X-RateLimit-Limit-Hour'] = str(limits.get('hour', 0))
            headers['X-RateLimit-Limit-Day'] = str(limits.get('day', 0))

            # X-RateLimit-Remaining headers
            headers['X-RateLimit-Remaining-Minute'] = str(remaining.get('minute', 0))
            headers['X-RateLimit-Remaining-Hour'] = str(remaining.get('hour', 0))
            headers['X-RateLimit-Remaining-Day'] = str(remaining.get('day', 0))

            # Retry-After header (if any limit exceeded)
            if any(count == 0 for count in remaining.values()):
                # Find the window with the least time remaining (simplified to 60 seconds)
                headers['Retry-After'] = '60'

        return headers


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to enforce rate limiting on all requests.
    """

    def process_request(self, request):
        """Check rate limit before processing request."""
        # THE IoT ESCAPE PLAN: Explicitly exclude IoT endpoints at the VERY START of process_request
        # This ensures these requests bypass ALL rate limiting checks before any other logic
        # Whitelist /iot/ namespace completely to bypass all security filters
        if (request.path.startswith('/iot/') or  # NEW: Complete /iot/ namespace bypass
            request.path.startswith('/ws/') or  # WebSocket upgrades (if ever routed through Django middleware)
            request.path.startswith('/api/screens/heartbeat/') or 
            request.path.startswith('/api/player/template/') or
            request.path.startswith('/public-iot/screens/heartbeat/') or
            request.path.startswith('/public-iot/player/template/') or
            request.path.startswith('/admin/') or 
            request.path.startswith('/static/')):
            return None  # Return None to skip rate limiting and continue to next middleware/view

        # Get rate limit configuration
        rate_limit_config = getattr(settings, 'RATE_LIMITING', {})
        enabled = rate_limit_config.get('ENABLED', True)

        if not enabled:
            return None

        # Get endpoint-specific config
        endpoint_config = rate_limit_config.get('ENDPOINTS', {}).get(request.path, {})
        strategy = endpoint_config.get('strategy', rate_limit_config.get('STRATEGY', RateLimiter.STRATEGY_COMBINED))
        limits = endpoint_config.get('limits', {})
        per_role_limits = rate_limit_config.get('PER_ROLE_LIMITS', {})

        # Check rate limit
        is_allowed, remaining = RateLimiter.check_rate_limit(
            request,
            endpoint=request.path,
            strategy=strategy,
            limit_per_minute=limits.get('per_minute'),
            limit_per_hour=limits.get('per_hour'),
            limit_per_day=limits.get('per_day'),
            per_role_limits=per_role_limits
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded: {request.method} {request.path} "
                f"from {RateLimiter.get_client_identifier(request)[0]}"
            )

            # Generate headers
            limit_headers = RateLimiter.get_rate_limit_headers(
                remaining,
                {
                    'minute': limits.get('per_minute', RateLimiter.DEFAULT_PER_MINUTE),
                    'hour': limits.get('per_hour', RateLimiter.DEFAULT_PER_HOUR),
                    'day': limits.get('per_day', RateLimiter.DEFAULT_PER_DAY)
                }
            )

            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'detail': 'Too many requests. Please try again later.',
                    'retry_after': 60
                },
                status=429,
                headers=limit_headers
            )

        return None


def rate_limit(
    strategy: str = RateLimiter.STRATEGY_COMBINED,
    limit_per_minute: Optional[int] = None,
    limit_per_hour: Optional[int] = None,
    limit_per_day: Optional[int] = None
):
    """
    Decorator to apply rate limiting to a view function.

    Usage:
        @rate_limit(strategy='user', limit_per_minute=100)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            is_allowed, remaining = RateLimiter.check_rate_limit(
                request,
                endpoint=request.path,
                strategy=strategy,
                limit_per_minute=limit_per_minute,
                limit_per_hour=limit_per_hour,
                limit_per_day=limit_per_day
            )

            if not is_allowed:
                headers = RateLimiter.get_rate_limit_headers(remaining, {
                    'minute': limit_per_minute or RateLimiter.DEFAULT_PER_MINUTE,
                    'hour': limit_per_hour or RateLimiter.DEFAULT_PER_HOUR,
                    'day': limit_per_day or RateLimiter.DEFAULT_PER_DAY
                })

                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'detail': 'Too many requests. Please try again later.'
                    },
                    status=429,
                    headers=headers
                )

            response = view_func(request, *args, **kwargs)

            # Add rate limit headers to response
            if remaining:
                headers = RateLimiter.get_rate_limit_headers(remaining, {
                    'minute': limit_per_minute or RateLimiter.DEFAULT_PER_MINUTE,
                    'hour': limit_per_hour or RateLimiter.DEFAULT_PER_HOUR,
                    'day': limit_per_day or RateLimiter.DEFAULT_PER_DAY
                })
                for key, value in headers.items():
                    response[key] = value

            return response

        return wrapper
    return decorator


class RateLimitMixin:
    """
    Mixin for DRF views to add rate limiting.
    """

    rate_limit_strategy = RateLimiter.STRATEGY_COMBINED
    rate_limit_per_minute = None
    rate_limit_per_hour = None
    rate_limit_per_day = None

    def dispatch(self, request, *args, **kwargs):
        """Check rate limit before dispatching."""
        is_allowed, remaining = RateLimiter.check_rate_limit(
            request,
            endpoint=request.path,
            strategy=self.rate_limit_strategy,
            limit_per_minute=self.rate_limit_per_minute,
            limit_per_hour=self.rate_limit_per_hour,
            limit_per_day=self.rate_limit_per_day
        )

        if not is_allowed:
            headers = RateLimiter.get_rate_limit_headers(remaining, {
                'minute': self.rate_limit_per_minute or RateLimiter.DEFAULT_PER_MINUTE,
                'hour': self.rate_limit_per_hour or RateLimiter.DEFAULT_PER_HOUR,
                'day': self.rate_limit_per_day or RateLimiter.DEFAULT_PER_DAY
            })

            return Response(
                {
                    'error': 'Rate limit exceeded',
                    'detail': 'Too many requests. Please try again later.'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=headers
            )

        response = super().dispatch(request, *args, **kwargs)

        # Add rate limit headers
        if remaining:
            headers = RateLimiter.get_rate_limit_headers(remaining, {
                'minute': self.rate_limit_per_minute or RateLimiter.DEFAULT_PER_MINUTE,
                'hour': self.rate_limit_per_hour or RateLimiter.DEFAULT_PER_HOUR,
                'day': self.rate_limit_per_day or RateLimiter.DEFAULT_PER_DAY
            })
            for key, value in headers.items():
                response[key] = value

        return response
