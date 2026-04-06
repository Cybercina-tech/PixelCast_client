"""
When DEPLOYMENT_MODE=saas, /api/platform/* requires mother to allow feature "saas_mode".

Deny by default: missing credentials, mother unreachable, or allowed=false.
Caches successful mother responses for one hour (positive or negative).
"""

from __future__ import annotations

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from core.deployment import normalize_deployment_mode

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "mother_saas_feature:"
_CACHE_TTL = 3600


class MotherSaasPlatformEnforcementMiddleware(MiddlewareMixin):
    """Block platform API unless mother grants saas_mode for this instance."""

    def process_request(self, request):
        path = request.path or ""
        if not path.startswith("/api/platform/"):
            return None

        if normalize_deployment_mode(getattr(settings, "DEPLOYMENT_MODE", None)) != "saas":
            return None

        from mother_client.client import check_feature_allowed
        from mother_client.crypto import decrypt_api_key
        from mother_client.models import MotherClientState

        state = MotherClientState.get_solo()
        if not state.has_credentials():
            return JsonResponse(
                {"detail": "SaaS deployment mode requires registration with the mother platform (missing credentials)."},
                status=403,
            )

        try:
            raw_key = decrypt_api_key(state.api_key_encrypted)
        except Exception:
            logger.exception("mother_saas_enforcement: could not decrypt instance key")
            return JsonResponse({"detail": "Invalid mother platform credentials."}, status=403)

        cache_key = _CACHE_PREFIX + hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:40]
        cached = cache.get(cache_key)
        if cached is True:
            return None
        if cached is False:
            return JsonResponse(
                {"detail": "SaaS platform features are not licensed for this instance."},
                status=403,
            )

        allowed = check_feature_allowed(raw_key, "saas_mode")
        if allowed is None:
            return JsonResponse(
                {"detail": "Could not verify SaaS entitlement with the mother platform."},
                status=403,
            )

        cache.set(cache_key, bool(allowed), _CACHE_TTL)
        if not allowed:
            return JsonResponse(
                {"detail": "SaaS platform features are not licensed for this instance."},
                status=403,
            )
        return None
