import uuid

from django.db import models
from django.utils import timezone


class ClientConfig(models.Model):
    """
    Single-row config for Pixelcast client (single-tenant) deployments.
    Points to the fixed Tenant created during installation.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    tenant = models.OneToOneField(
        'saas_platform.Tenant',
        on_delete=models.CASCADE,
        related_name='pixelcast_client_config',
    )
    deployment_mode = models.CharField(
        max_length=32,
        default='client',
        help_text='Mirrors DEPLOYMENT_MODE for DB lookups without relying on env alone',
    )
    installed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Pixelcast client config'

    def __str__(self) -> str:
        return 'ClientConfig'

    @classmethod
    def get_solo(cls) -> 'ClientConfig | None':
        return cls.objects.filter(pk=1).first()
