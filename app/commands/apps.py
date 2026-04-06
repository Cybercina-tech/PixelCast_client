from django.apps import AppConfig


class CommandsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commands'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import commands.signals  # noqa
