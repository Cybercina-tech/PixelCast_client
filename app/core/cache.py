"""
Centralized caching system for PixelCast Signage.

Provides:
- Cache decorators for views and functions
- Cache key generation utilities
- Cache invalidation strategies
- Security-aware caching (excludes sensitive data)
"""
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional, Dict, List
from django.core.cache import cache
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache manager with security and performance optimizations.
    """

    # Cache key prefixes
    PREFIX_SCREEN = "screen:"
    PREFIX_TEMPLATE = "template:"
    PREFIX_CONTENT = "content:"
    PREFIX_COMMAND = "command:"
    PREFIX_SCHEDULE = "schedule:"
    PREFIX_USER = "user:"
    PREFIX_ANALYTICS = "analytics:"
    PREFIX_LIST = "list:"

    # Default timeouts (in seconds)
    TIMEOUT_SHORT = 60  # 1 minute
    TIMEOUT_MEDIUM = 300  # 5 minutes
    TIMEOUT_LONG = 3600  # 1 hour
    TIMEOUT_VERY_LONG = 86400  # 24 hours

    # Fields to exclude from cache keys (sensitive data)
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'key', 'auth', 'credential',
        'access_token', 'refresh_token', 'api_key'
    }

    @classmethod
    def generate_key(
        cls,
        prefix: str,
        identifier: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> str:
        """
        Generate a cache key from components.

        Args:
            prefix: Cache key prefix
            identifier: Resource identifier (ID, slug, etc.)
            params: Additional parameters to include in key
            user_id: Optional user ID for user-specific caching

        Returns:
            Cache key string
        """
        key_parts = [prefix]

        if identifier:
            key_parts.append(str(identifier))

        if params:
            # Sort params for consistency and exclude sensitive fields
            safe_params = {
                k: v for k, v in params.items()
                if not any(sensitive in k.lower() for sensitive in cls.SENSITIVE_FIELDS)
            }
            if safe_params:
                # Create hash of params for shorter keys
                params_str = json.dumps(safe_params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                key_parts.append(params_hash)

        if user_id:
            key_parts.append(f"user:{user_id}")

        return ":".join(key_parts)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            return cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    @classmethod
    def set(
        cls,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        version: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        try:
            if timeout is None:
                timeout = cls.TIMEOUT_MEDIUM
            cache.set(key, value, timeout, version)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    @classmethod
    def delete(cls, key: str, version: Optional[int] = None) -> bool:
        """Delete key from cache."""
        try:
            return cache.delete(key, version)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    @classmethod
    def invalidate_pattern(cls, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Note: This requires Redis backend. Falls back to no-op if not available.
        For LocMemCache, we cannot efficiently match patterns, so this is a no-op.
        """
        try:
            # Try to use Redis pattern matching (django-redis)
            if hasattr(cache, 'delete_pattern'):
                return cache.delete_pattern(pattern)
            elif hasattr(cache, '_cache') and hasattr(cache._cache, 'delete_pattern'):
                return cache._cache.delete_pattern(pattern)
            elif hasattr(cache, 'iter_keys'):
                # Django Redis backend (built-in)
                deleted = 0
                for key in cache.iter_keys(pattern):
                    if cache.delete(key):
                        deleted += 1
                return deleted
            else:
                # LocMemCache or other backends don't support pattern matching
                # This is expected and not an error - just log at debug level
                logger.debug("Pattern-based cache invalidation not available with current cache backend. "
                           "For pattern-based invalidation, use Redis cache backend (set USE_REDIS_CACHE=True).")
                return 0
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            return 0

    @classmethod
    def invalidate_resource(cls, resource_type: str, resource_id: str) -> None:
        """Invalidate all cache entries for a specific resource."""
        prefix_by_type = {
            'screen': cls.PREFIX_SCREEN,
            'template': cls.PREFIX_TEMPLATE,
            'content': cls.PREFIX_CONTENT,
            'command': cls.PREFIX_COMMAND,
            'user': cls.PREFIX_USER,
        }
        if resource_type in prefix_by_type:
            cache.delete(cls.generate_key(prefix_by_type[resource_type], resource_id))

        patterns = [
            f"{resource_type}:{resource_id}:*",
            f"{resource_type}:{resource_id}",
            f"*:{resource_type}:{resource_id}:*",
            f"list:{resource_type}:*",  # Invalidate list caches
        ]
        for pattern in patterns:
            cls.invalidate_pattern(pattern)

    @classmethod
    def get_or_set(
        cls,
        key: str,
        callable_func: Callable,
        timeout: Optional[int] = None
    ) -> Any:
        """Get from cache or call function and cache result."""
        try:
            return cache.get_or_set(key, callable_func, timeout or cls.TIMEOUT_MEDIUM)
        except Exception as e:
            logger.error(f"Cache get_or_set error for key {key}: {e}")
            # Fallback to calling function directly
            return callable_func()


def cached_view(timeout: int = CacheManager.TIMEOUT_MEDIUM, key_func: Optional[Callable] = None):
    """
    Decorator to cache a view function's response.

    Args:
        timeout: Cache timeout in seconds
        key_func: Optional function to generate custom cache key from request
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                # Default: use URL path and query params
                path = request.path
                query_params = request.GET.urlencode()
                params_hash = hashlib.md5(
                    f"{path}?{query_params}".encode()
                ).hexdigest()[:8]
                cache_key = f"view:{path}:{params_hash}"

            # Check cache
            cached_response = CacheManager.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for view: {cache_key}")
                return cached_response

            # Call view and cache response
            response = view_func(request, *args, **kwargs)
            if isinstance(response, Response) and response.status_code == 200:
                # Only cache successful responses
                CacheManager.set(cache_key, response, timeout)
                logger.debug(f"Cached view response: {cache_key}")

            return response

        return wrapper
    return decorator


def cached_method(timeout: int = CacheManager.TIMEOUT_MEDIUM):
    """
    Decorator to cache method results.

    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Generate cache key from method name and arguments
            method_name = method.__name__
            class_name = self.__class__.__name__
            args_str = json.dumps(
                [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()],
                sort_keys=True
            )
            args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
            cache_key = f"method:{class_name}.{method_name}:{args_hash}"

            # Check cache
            cached_result = CacheManager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for method: {cache_key}")
                return cached_result

            # Call method and cache result
            result = method(self, *args, **kwargs)
            CacheManager.set(cache_key, result, timeout)
            logger.debug(f"Cached method result: {cache_key}")

            return result

        return wrapper
    return decorator


# Convenience functions for common resource types
def get_screen_cache(screen_id: str, params: Optional[Dict] = None) -> str:
    """Generate cache key for screen resource."""
    return CacheManager.generate_key(CacheManager.PREFIX_SCREEN, screen_id, params)


def get_template_cache(template_id: str, params: Optional[Dict] = None) -> str:
    """Generate cache key for template resource."""
    return CacheManager.generate_key(CacheManager.PREFIX_TEMPLATE, template_id, params)


def get_content_cache(content_id: str, params: Optional[Dict] = None) -> str:
    """Generate cache key for content resource."""
    return CacheManager.generate_key(CacheManager.PREFIX_CONTENT, content_id, params)


def get_analytics_cache(endpoint: str, params: Optional[Dict] = None, user_id: Optional[int] = None) -> str:
    """Generate cache key for analytics endpoint."""
    return CacheManager.generate_key(
        CacheManager.PREFIX_ANALYTICS + endpoint,
        params=params,
        user_id=user_id
    )


def invalidate_screen_cache(screen_id: str) -> None:
    """Invalidate all cache entries for a screen."""
    CacheManager.invalidate_resource("screen", screen_id)


def invalidate_template_cache(template_id: str) -> None:
    """Invalidate all cache entries for a template."""
    CacheManager.invalidate_resource("template", template_id)


def invalidate_content_cache(content_id: str) -> None:
    """Invalidate all cache entries for content."""
    CacheManager.invalidate_resource("content", content_id)
