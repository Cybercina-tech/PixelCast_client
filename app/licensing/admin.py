from django.contrib import admin

from .models import (
    LicenseRegistryHeartbeatLog,
    LicenseRegistryInstallation,
    LicenseRegistryPurchase,
    LicenseState,
)


@admin.register(LicenseRegistryPurchase)
class LicenseRegistryPurchaseAdmin(admin.ModelAdmin):
    list_display = ("code_fingerprint", "buyer_username", "envato_item_id", "sold_at", "updated_at")
    search_fields = ("buyer_username", "code_fingerprint")


@admin.register(LicenseRegistryInstallation)
class LicenseRegistryInstallationAdmin(admin.ModelAdmin):
    list_display = ("domain", "purchase", "suspended", "suspicious", "last_heartbeat_at", "app_version")
    list_filter = ("suspended", "suspicious")
    search_fields = ("domain", "notes")


@admin.register(LicenseRegistryHeartbeatLog)
class LicenseRegistryHeartbeatLogAdmin(admin.ModelAdmin):
    list_display = ("installation", "received_at", "app_version", "ip_address")


@admin.register(LicenseState)
class LicenseStateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "license_status",
        "activated_domain",
        "masked_code",
        "last_successful_validation_at",
        "grace_until",
        "updated_at",
    )
    readonly_fields = (
        "validation_signature",
        "last_validation_at",
        "last_successful_validation_at",
        "created_at",
        "updated_at",
    )
    fields = (
        "purchase_code",
        "activated_domain",
        "activated_at",
        "license_status",
        "codecanyon_product_id_override",
        "last_validation_at",
        "last_successful_validation_at",
        "grace_until",
        "last_error",
        "validation_signature",
        "created_at",
        "updated_at",
    )

    def masked_code(self, obj):
        return obj.masked_purchase_code()

    masked_code.short_description = "Purchase code"
