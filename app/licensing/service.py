import logging
import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .client import (
    LicenseServerError,
    license_gateway_base_url,
    license_validate_url,
    post_gateway_activate,
    post_license_validation,
)
from .models import LicenseState
from .plan_features import normalize_plan_type

logger = logging.getLogger(__name__)
PURCHASE_CODE_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


@dataclass
class LicenseDecision:
    allow: bool
    status: str
    error_code: str
    message: str
    grace_until: object = None
    retry_after: int | None = None


def _cache_key() -> str:
    return "licensing:decision:v1"


def invalidate_license_cache() -> None:
    cache.delete(_cache_key())


def _apply_domain_binding(state: LicenseState) -> None:
    """Issue or clear HS256 domain-binding JWT (registry token stays separate)."""
    dom = (state.activated_domain or "").strip()
    if state.license_status in (LicenseState.STATUS_ACTIVE, LicenseState.STATUS_GRACE) and dom:
        from .jwt_tokens import issue_domain_binding_jwt

        state.domain_binding_jwt = issue_domain_binding_jwt(dom, state.plan_type or "")
    else:
        state.domain_binding_jwt = ""


def resolve_product_id(state: LicenseState):
    env_product_id = (getattr(settings, "CODECANYON_PRODUCT_ID", "") or "").strip()
    if env_product_id:
        return env_product_id, "env"

    db_product_id = (state.codecanyon_product_id_override or "").strip()
    if db_product_id:
        return db_product_id, "db"

    return "", "temporary"


def _purchase_code_shape_valid(code: str) -> bool:
    return bool(PURCHASE_CODE_RE.match((code or "").strip()))


def _normalize_status(is_valid: bool, data: dict) -> str:
    if is_valid:
        return LicenseState.STATUS_ACTIVE

    st = str(data.get("status", "") or data.get("license_status", "")).lower()
    if st in {"invalid", "expired", "revoked", "suspended", "inactive"}:
        return LicenseState.STATUS_INVALID

    return LicenseState.STATUS_INVALID


def _build_payload(state: LicenseState):
    product_id, product_source = resolve_product_id(state)
    payload = {
        "purchase_code": state.purchase_code,
        "product_id": product_id,
        "domain": state.activated_domain,
    }
    return payload, product_source


def get_or_create_state() -> LicenseState:
    return LicenseState.get_solo()


def merge_gateway_license_payload(state: LicenseState, data: dict, *, touch_contact: bool = True) -> None:
    """Apply plan_type / features / last contact from license gateway JSON."""
    if touch_contact:
        state.last_gateway_contact_at = timezone.now()
    pt = normalize_plan_type(data.get("plan_type"))
    if pt:
        state.plan_type = pt
    feat = data.get("features")
    if feat is None:
        feat = data.get("features_snapshot")
    if isinstance(feat, dict):
        state.features_snapshot = feat
    elif isinstance(feat, list):
        state.features_snapshot = {str(k): True for k in feat}
    state.touch_signature()


def apply_heartbeat_gateway_response(state: LicenseState, data: dict) -> None:
    if not data.get("ok", True):
        return
    merge_gateway_license_payload(state, data, touch_contact=True)
    _apply_domain_binding(state)
    state.save(
        update_fields=[
            "plan_type",
            "features_snapshot",
            "last_gateway_contact_at",
            "domain_binding_jwt",
            "validation_signature",
            "updated_at",
        ]
    )
    cache.delete(_cache_key())


def heartbeat_stale_contact_tier() -> str | None:
    """warn | readonly | admin_only based on last successful gateway sync (active licenses only)."""
    if not bool(getattr(settings, "LICENSE_ENFORCEMENT_ENABLED", False)):
        return None
    if not bool(getattr(settings, "LICENSE_STALE_CONTACT_ENFORCEMENT_ENABLED", True)):
        return None
    state = LicenseState.get_solo()
    if state.license_status != LicenseState.STATUS_ACTIVE:
        return None
    contact = state.last_gateway_contact_at
    if contact is None:
        return None
    days = (timezone.now() - contact).total_seconds() / 86400.0
    warn_end = float(getattr(settings, "LICENSE_STALE_CONTACT_WARN_DAYS", 7) or 7)
    ro_end = float(getattr(settings, "LICENSE_STALE_CONTACT_READONLY_DAYS", 14) or 14)
    if days <= 0:
        return None
    if days <= warn_end:
        return "warn"
    if days <= ro_end:
        return "readonly"
    return "admin_only"


def _masked_token_preview(token: str) -> str:
    t = (token or "").strip()
    if len(t) <= 12:
        return "****" if t else ""
    return f"{t[:4]}…{t[-4:]}"


def activate_license(purchase_code: str, domain: str = "", override_product_id: str = ""):
    state = get_or_create_state()
    code = (purchase_code or "").strip()
    if override_product_id is not None:
        state.codecanyon_product_id_override = (override_product_id or "").strip()
    if domain:
        state.activated_domain = domain.strip()
    state.activated_at = timezone.now()
    state.license_status = LicenseState.STATUS_INACTIVE
    state.last_error = ""
    cache.delete(_cache_key())

    base = license_gateway_base_url()
    if base:
        if not _purchase_code_shape_valid(code):
            state.last_error = "Purchase code format is invalid"
            _apply_domain_binding(state)
            state.touch_signature()
            state.save()
            return LicenseDecision(
                allow=False,
                status=LicenseState.STATUS_INVALID,
                error_code="license_invalid",
                message="Purchase code format is invalid",
            )

        product_id, _ = resolve_product_id(state)
        app_version = (getattr(settings, "SCREENGRAM_APP_VERSION", "") or "").strip()
        try:
            data = post_gateway_activate(
                base,
                {
                    "purchase_code": code,
                    "domain": state.activated_domain or "",
                    "product_id": product_id,
                    "app_version": app_version,
                },
            )
        except LicenseServerError as exc:
            logger.warning("License gateway activation failed: %s", exc)
            state.purchase_code = code
            state.activation_token = ""
            state.last_error = str(exc)
            _apply_domain_binding(state)
            state.touch_signature()
            state.save()
            if getattr(exc, "status_code", None) == 429:
                return LicenseDecision(
                    allow=False,
                    status=LicenseState.STATUS_INACTIVE,
                    error_code="rate_limited",
                    message=str(exc),
                    retry_after=getattr(exc, "retry_after", None) or 60,
                )
            return LicenseDecision(
                allow=False,
                status=LicenseState.STATUS_INACTIVE,
                error_code="license_activation_failed",
                message=str(exc),
            )

        token = (data.get("activation_token") or "").strip()
        if not token:
            state.purchase_code = code
            state.activation_token = ""
            state.last_error = data.get("message") or "Gateway did not return an activation token"
            _apply_domain_binding(state)
            state.touch_signature()
            state.save()
            return LicenseDecision(
                allow=False,
                status=LicenseState.STATUS_INACTIVE,
                error_code="license_activation_failed",
                message=state.last_error,
            )

        state.purchase_code = ""
        state.activation_token = token
        state.last_error = ""
        merge_gateway_license_payload(state, data, touch_contact=True)
        state.touch_signature()
        state.save()
        cache.delete(_cache_key())
        return validate_license(force=True)

    state.purchase_code = code
    state.activation_token = ""
    state.touch_signature()
    state.save()
    return validate_license(force=True)


def current_status_payload(decision=None):
    state = get_or_create_state()
    product_id, source = resolve_product_id(state)
    gw = bool(license_gateway_base_url())
    raw_feat = state.features_snapshot or {}
    feat = dict(raw_feat) if isinstance(raw_feat, dict) else {}
    if decision is not None:
        valid = bool(decision.allow)
        err = decision.error_code or ""
        retry = getattr(decision, "retry_after", None)
        top_status = "success" if decision.allow else "error"
        msg = decision.message
    else:
        valid = state.license_status in (
            LicenseState.STATUS_ACTIVE,
            LicenseState.STATUS_GRACE,
        )
        err = ""
        retry = None
        top_status = "success"
        msg = "License status fetched"
    return {
        "status": top_status,
        "message": msg,
        "valid": valid,
        "error_code": err,
        "error": err,
        "retry_after": retry,
        "license_status": state.license_status,
        "grace_until": state.grace_until,
        "activated_domain": state.activated_domain,
        "product_id": product_id,
        "product_id_source": source,
        "last_validation_at": state.last_validation_at,
        "last_successful_validation_at": state.last_successful_validation_at,
        "enforcement_enabled": bool(
            getattr(settings, "LICENSE_ENFORCEMENT_ENABLED", False)
        ),
        "license_gateway_configured": gw,
        "uses_activation_token": bool((state.activation_token or "").strip()),
        "masked_activation_token": _masked_token_preview(state.activation_token),
        "masked_purchase_code": state.masked_purchase_code(),
        "plan_type": state.plan_type or "",
        "features": feat,
        "features_snapshot": feat,
        "last_gateway_contact_at": state.last_gateway_contact_at,
        "heartbeat_stale_tier": heartbeat_stale_contact_tier() or "",
    }


def validate_license(force: bool = False) -> LicenseDecision:
    cache_ttl = int(getattr(settings, "LICENSE_CACHE_TTL_SECONDS", 900))
    grace_hours = int(getattr(settings, "LICENSE_OFFLINE_GRACE_HOURS", 72))

    if not force:
        cached = cache.get(_cache_key())
        if cached:
            return cached

    state = get_or_create_state()
    now = timezone.now()
    token_secret = (state.activation_token or "").strip()
    purchase = (state.purchase_code or "").strip()

    if not token_secret and not purchase:
        state.license_status = LicenseState.STATUS_INACTIVE
        state.last_error = "Purchase code or activation token is not set"
        state.last_validation_at = now
        _apply_domain_binding(state)
        state.touch_signature()
        state.save(
            update_fields=[
                "license_status",
                "last_error",
                "last_validation_at",
                "domain_binding_jwt",
                "validation_signature",
                "updated_at",
            ]
        )
        decision = LicenseDecision(
            allow=False,
            status=state.license_status,
            error_code="license_required",
            message="Activate your license with a purchase code",
        )
        cache.set(_cache_key(), decision, cache_ttl)
        return decision

    timeout_seconds = int(getattr(settings, "LICENSE_SERVER_TIMEOUT_SECONDS", 8))
    app_version = (getattr(settings, "SCREENGRAM_APP_VERSION", "") or "").strip()

    try:
        if token_secret:
            vurl = license_validate_url()
            if not vurl:
                raise LicenseServerError("LICENSE_GATEWAY_BASE_URL or LICENSE_SERVER_URL is not configured")

            is_valid, data = post_license_validation(
                license_server_url=vurl,
                payload={
                    "domain": state.activated_domain or "",
                    "app_version": app_version,
                },
                auth_bearer=token_secret,
                timeout_seconds=timeout_seconds,
            )
            product_source = "gateway_token"
        else:
            if not _purchase_code_shape_valid(purchase):
                state.license_status = LicenseState.STATUS_INVALID
                state.last_error = "Purchase code format is invalid"
                state.last_validation_at = now
                _apply_domain_binding(state)
                state.touch_signature()
                state.save(
                    update_fields=[
                        "license_status",
                        "last_error",
                        "last_validation_at",
                        "domain_binding_jwt",
                        "validation_signature",
                        "updated_at",
                    ]
                )
                decision = LicenseDecision(
                    allow=False,
                    status=state.license_status,
                    error_code="license_invalid",
                    message="Purchase code format is invalid",
                )
                cache.set(_cache_key(), decision, cache_ttl)
                return decision

            payload, product_source = _build_payload(state)
            codecanyon_token = getattr(settings, "CODECANYON_TOKEN", "")
            url = license_validate_url()
            if not url:
                raise LicenseServerError("LICENSE_SERVER_URL is not configured")

            is_valid, data = post_license_validation(
                license_server_url=url,
                payload=payload,
                token=codecanyon_token,
                timeout_seconds=timeout_seconds,
            )

        mapped_status = _normalize_status(is_valid, data)
        state.license_status = mapped_status
        state.last_validation_at = now
        state.last_error = ""

        if mapped_status == LicenseState.STATUS_ACTIVE:
            state.last_successful_validation_at = now
            state.grace_until = now + timedelta(hours=grace_hours)
            dom = (data.get("domain") or "").strip()
            if not state.activated_domain and dom:
                state.activated_domain = dom
            merge_gateway_license_payload(state, data, touch_contact=True)
        else:
            state.grace_until = now

        _apply_domain_binding(state)
        state.touch_signature()
        state.save()

        if mapped_status == LicenseState.STATUS_ACTIVE:
            decision = LicenseDecision(
                allow=True,
                status=mapped_status,
                error_code="",
                message=f"License is active ({product_source})",
                grace_until=state.grace_until,
            )
        else:
            decision = LicenseDecision(
                allow=False,
                status=mapped_status,
                error_code="license_invalid",
                message=data.get("message", "License is invalid"),
                grace_until=state.grace_until,
            )

        cache.set(_cache_key(), decision, cache_ttl)
        return decision

    except LicenseServerError as exc:
        logger.warning("License server unavailable: %s", exc)
        is_rate_limited = getattr(exc, "status_code", None) == 429
        retry_after = (
            getattr(exc, "retry_after", None) if is_rate_limited else None
        )

        state.last_validation_at = now
        state.last_error = str(exc)

        if state.last_successful_validation_at:
            grace_until = state.last_successful_validation_at + timedelta(hours=grace_hours)
            state.grace_until = grace_until
            if now <= grace_until:
                state.license_status = LicenseState.STATUS_GRACE
                _apply_domain_binding(state)
                state.touch_signature()
                state.save(
                    update_fields=[
                        "license_status",
                        "last_validation_at",
                        "last_error",
                        "grace_until",
                        "domain_binding_jwt",
                        "validation_signature",
                        "updated_at",
                    ]
                )
                decision = LicenseDecision(
                    allow=True,
                    status=LicenseState.STATUS_GRACE,
                    error_code="",
                    message="License server unavailable; running in grace mode",
                    grace_until=grace_until,
                    retry_after=retry_after,
                )
                cache.set(_cache_key(), decision, cache_ttl)
                return decision

        state.license_status = LicenseState.STATUS_INVALID
        _apply_domain_binding(state)
        state.touch_signature()
        state.save(
            update_fields=[
                "license_status",
                "last_validation_at",
                "last_error",
                "domain_binding_jwt",
                "validation_signature",
                "updated_at",
            ]
        )
        if is_rate_limited:
            decision = LicenseDecision(
                allow=False,
                status=state.license_status,
                error_code="rate_limited",
                message=str(exc),
                grace_until=state.grace_until,
                retry_after=retry_after or 60,
            )
        else:
            decision = LicenseDecision(
                allow=False,
                status=state.license_status,
                error_code="grace_expired",
                message="License server unavailable and grace period has expired",
                grace_until=state.grace_until,
            )
        cache.set(_cache_key(), decision, cache_ttl)
        return decision
