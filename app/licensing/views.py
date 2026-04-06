from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from setup.utils import is_installed

from .serializers import (
    LicenseActivateSerializer,
    LicenseStatusSerializer,
    LicenseRevalidateSerializer,
)
from .service import (
    activate_license,
    current_status_payload,
    get_or_create_state,
    validate_license,
)


class LicenseManagementPermission(BasePermission):
    """During setup (not installed), allow activation without auth. After install, Developer only."""

    message = "Only Developer users can manage license settings."

    def has_permission(self, request, view):
        if not is_installed():
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        user = request.user
        return bool(getattr(user, "is_developer", lambda: False)())


def _http_status_for_license(decision) -> int:
    if getattr(decision, "error_code", None) == "rate_limited":
        return status.HTTP_429_TOO_MANY_REQUESTS
    if decision.allow:
        return status.HTTP_200_OK
    return status.HTTP_400_BAD_REQUEST


def _license_response(decision):
    payload = current_status_payload(decision=decision)
    serializer = LicenseStatusSerializer(payload)
    resp = Response(serializer.data, status=_http_status_for_license(decision))
    if decision.error_code == "rate_limited" and getattr(decision, "retry_after", None):
        resp["Retry-After"] = str(decision.retry_after)
    return resp


class LicenseStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = current_status_payload()
        serializer = LicenseStatusSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LicenseActivateView(APIView):
    permission_classes = [LicenseManagementPermission]

    def post(self, request):
        serializer = LicenseActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        domain = data.get("domain") or request.get_host()
        override = data.get("codecanyon_product_id_override", "")
        decision = activate_license(
            purchase_code=data["purchase_code"],
            domain=domain,
            override_product_id=override,
        )
        return _license_response(decision)


class LicenseRevalidateView(APIView):
    permission_classes = [LicenseManagementPermission]

    def post(self, request):
        serializer = LicenseRevalidateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        decision = validate_license(force=serializer.validated_data.get("force", True))
        return _license_response(decision)


class LicenseProductOverrideView(APIView):
    permission_classes = [LicenseManagementPermission]

    def post(self, request):
        override_value = (request.data.get("codecanyon_product_id_override") or "").strip()
        state = get_or_create_state()
        state.codecanyon_product_id_override = override_value
        state.touch_signature()
        state.save(update_fields=["codecanyon_product_id_override", "validation_signature", "updated_at"])
        decision = validate_license(force=True)
        return _license_response(decision)
