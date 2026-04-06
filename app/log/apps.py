from django.apps import AppConfig


class LogConfig(AppConfig):
    """
    Configuration for the log app.
    
    This app provides centralized logging for the Digital Signage system.
    All logs are written by backend services, not directly by screens.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'log'
    verbose_name = 'System Logs'
