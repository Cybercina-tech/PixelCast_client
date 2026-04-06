"""
Django app configuration for core infrastructure features.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Infrastructure'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import core.signals  # noqa
        except ImportError:
            # Signals may not be available during initial setup
            pass
