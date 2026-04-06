import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .jwt_tokens import verify_domain_binding_jwt
from .models import LicenseState
from .service import (
    heartbeat_stale_contact_tier,
    invalidate_license_cache,
    validate_license,
)

logger = logging.getLogger(__name__)


def _verify_domain_binding(request):
    """Ensure locally issued domain JWT matches Host (registry token is separate)."""
    if not bool(getattr(settings, "LICENSE_DOMAIN_BINDING_ENABLED", True)):
        return True
    if not bool(getattr(settings, "LICENSE_ENFORCEMENT_ENABLED", False)):
        return True

    state = LicenseState.get_solo()
    if state.license_status not in (LicenseState.STATUS_ACTIVE, LicenseState.STATUS_GRACE):
        return True

    host = request.get_host()
    tok = (state.domain_binding_jwt or "").strip()
    if not tok:
        from .jwt_tokens import issue_domain_binding_jwt

        dom = (state.activated_domain or "").strip()
        if dom:
            state.domain_binding_jwt = issue_domain_binding_jwt(dom, state.plan_type or "")
            state.save(update_fields=["domain_binding_jwt", "validation_signature", "updated_at"])
            tok = (state.domain_binding_jwt or "").strip()

    ok, reason = verify_domain_binding_jwt(tok, host)
    if ok:
        return True
    if reason == "expired" and not getattr(request, "_license_jwt_refresh_tried", False):
        request._license_jwt_refresh_tried = True
        invalidate_license_cache()
        validate_license(force=True)
        state.refresh_from_db()
        tok2 = (state.domain_binding_jwt or "").strip()
        ok2, _ = verify_domain_binding_jwt(tok2, host)
        return ok2
    return False


class LicenseEnforcementMiddleware(MiddlewareMixin):
    EXEMPT_PREFIXES = (
        "/api/setup/",
        "/api/auth/login/",
        "/api/auth/signup/",
        "/api/auth/token/",
        "/api/auth/token/refresh/",
        "/api/license/",
        "/api/license-registry/",
        "/api/schema/",
        "/api/docs/",
        "/api/redoc/",
    )

    def process_request(self, request):
        if not bool(getattr(settings, "LICENSE_ENFORCEMENT_ENABLED", False)):
            return None

        path = request.path
        if not path.startswith("/api/"):
            return None

        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            # Enforcement begins after authentication for protected API use.
            return None

        decision = validate_license(force=False)
        if decision.allow:
            if not _verify_domain_binding(request):
                return JsonResponse(
                    {
                        "error": "license_domain_mismatch",
                        "message": (
                            "This license is bound to another domain. "
                            "Re-validate the license on this host or contact support."
                        ),
                        "license_status": decision.status,
                        "grace_until": decision.grace_until.isoformat()
                        if decision.grace_until
                        else None,
                    },
                    status=403,
                )
            if decision.status == "grace":
                request.META["HTTP_X_LICENSE_STATUS"] = "grace"
            else:
                tier = heartbeat_stale_contact_tier()
                if tier == "warn":
                    request.META["HTTP_X_LICENSE_HEARTBEAT_STALE"] = "warn"
                elif tier == "readonly":
                    if request.method not in ("GET", "HEAD", "OPTIONS"):
                        return JsonResponse(
                            {
                                "error": "license_readonly",
                                "message": (
                                    "License gateway contact is stale; only read operations are allowed "
                                    "until validation or heartbeat succeeds."
                                ),
                                "license_heartbeat_stale_tier": tier,
                            },
                            status=403,
                        )
                elif tier == "admin_only":
                    if not user.is_developer():
                        return JsonResponse(
                            {
                                "error": "license_admin_only",
                                "message": (
                                    "License gateway contact is overdue; only Developer users may use the API "
                                    "until connectivity is restored."
                                ),
                                "license_heartbeat_stale_tier": tier,
                            },
                            status=403,
                        )
            return None

        logger.warning(
            "License denied request path=%s user=%s status=%s",
            path,
            getattr(user, "id", None),
            decision.status,
        )

        return JsonResponse(
            {
                "error": decision.error_code or "license_invalid",
                "message": decision.message,
                "license_status": decision.status,
                "grace_until": decision.grace_until.isoformat()
                if decision.grace_until
                else None,
            },
            status=403,
        )
