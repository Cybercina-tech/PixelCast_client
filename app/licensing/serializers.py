from rest_framework import serializers

PURCHASE_CODE_RE = (
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class LicenseStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    valid = serializers.BooleanField(required=False)
    message = serializers.CharField()
    error_code = serializers.CharField(required=False, allow_blank=True)
    error = serializers.CharField(required=False, allow_blank=True)
    retry_after = serializers.IntegerField(required=False, allow_null=True)
    license_status = serializers.CharField()
    grace_until = serializers.DateTimeField(allow_null=True)
    activated_domain = serializers.CharField(allow_blank=True)
    product_id = serializers.CharField(allow_blank=True)
    product_id_source = serializers.CharField()
    last_validation_at = serializers.DateTimeField(allow_null=True)
    last_successful_validation_at = serializers.DateTimeField(allow_null=True)
    enforcement_enabled = serializers.BooleanField()
    license_gateway_configured = serializers.BooleanField(required=False)
    uses_activation_token = serializers.BooleanField(required=False)
    masked_activation_token = serializers.CharField(required=False, allow_blank=True)
    masked_purchase_code = serializers.CharField(required=False, allow_blank=True)
    plan_type = serializers.CharField(required=False, allow_blank=True)
    features = serializers.JSONField(required=False)
    features_snapshot = serializers.JSONField(required=False)
    last_gateway_contact_at = serializers.DateTimeField(allow_null=True, required=False)
    heartbeat_stale_tier = serializers.CharField(required=False, allow_blank=True)


class LicenseActivateSerializer(serializers.Serializer):
    purchase_code = serializers.RegexField(
        regex=PURCHASE_CODE_RE,
        max_length=128,
        error_messages={"invalid": "Purchase code must be a valid UUID format."},
    )
    domain = serializers.CharField(max_length=255, required=False, allow_blank=True)
    codecanyon_product_id_override = serializers.CharField(
        max_length=64, required=False, allow_blank=True
    )


class LicenseRevalidateSerializer(serializers.Serializer):
    force = serializers.BooleanField(required=False, default=True)
