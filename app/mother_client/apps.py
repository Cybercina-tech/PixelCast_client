from django.apps import AppConfig


class MotherClientConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mother_client"
    verbose_name = "Mother server sync"
