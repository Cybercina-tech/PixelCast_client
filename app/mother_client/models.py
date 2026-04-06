from __future__ import annotations

import uuid

from django.db import models


class MotherClientState(models.Model):
    """
    Singleton (pk=1) holding gateway credentials for the mother platform.
    API key is stored encrypted (see mother_client.crypto).
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    instance_id = models.UUIDField(null=True, blank=True, editable=False)
    api_key_encrypted = models.TextField(blank=True, default="")
    registered_at = models.DateTimeField(null=True, blank=True)
    last_heartbeat_ok_at = models.DateTimeField(null=True, blank=True)
    last_usage_report_ok_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mother client state"

    def __str__(self) -> str:
        return "MotherClientState"

    @classmethod
    def get_solo(cls) -> MotherClientState:
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def has_credentials(self) -> bool:
        return bool(self.instance_id and self.api_key_encrypted)
