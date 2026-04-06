"""
Signals for automatic cache invalidation and audit logging.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.cache import CacheManager
import logging

logger = logging.getLogger(__name__)


def invalidate_resource_cache(resource_type: str, resource_id: str):
    """Invalidate cache for a resource."""
    try:
        CacheManager.invalidate_resource(resource_type.lower(), resource_id)
        logger.debug(f"Cache invalidated for {resource_type}:{resource_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate cache for {resource_type}:{resource_id}: {e}")


@receiver(post_save)
def invalidate_cache_on_save(sender, instance, **kwargs):
    """
    Invalidate cache when a model is saved.
    
    Only invalidates cache for known resource types to avoid excessive cache clearing.
    """
    resource_type = instance.__class__.__name__
    
    if resource_type in ('Screen', 'Template', 'Content'):
        try:
            invalidate_resource_cache(resource_type, str(instance.pk))
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {resource_type}:{instance.pk}: {e}")


@receiver(post_delete)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate cache when a model is deleted.
    """
    resource_type = instance.__class__.__name__
    
    if resource_type in ('Screen', 'Template', 'Content'):
        try:
            invalidate_resource_cache(resource_type, str(instance.pk))
        except Exception as e:
            logger.error(f"Failed to invalidate cache for deleted {resource_type}:{instance.pk}: {e}")


# Note: Audit logging is typically done explicitly in views/serializers
# to have access to request context (user, IP, etc.)
# Signals can be added for automatic logging but will have limited context
