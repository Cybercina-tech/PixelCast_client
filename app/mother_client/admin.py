from django.contrib import admin

from mother_client.models import MotherClientState


@admin.register(MotherClientState)
class MotherClientStateAdmin(admin.ModelAdmin):
    list_display = ("id", "instance_id", "registered_at", "last_heartbeat_ok_at", "last_usage_report_ok_at")
    readonly_fields = ("id", "instance_id", "api_key_encrypted", "registered_at", "last_heartbeat_ok_at", "last_usage_report_ok_at", "updated_at")
