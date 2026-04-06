"""
Central license registry logic (SaaS-only). Self-hosted instances call these via HTTP.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .envato import EnvatoApiError, fetch_sale_by_purchase_code, parse_sale_item_id
from .models import (
    LicenseRegistryHeartbeatLog,
    LicenseRegistryInstallation,
    LicenseRegistryPurchase,
)
from .plan_features import (
    PLAN_BASIC,
    PLAN_SAAS,
    features_for_plan,
    features_snapshot_list,
    normalize_plan_type,
)

def purchase_code_fingerprint(code: str) -> str:
    normalized = (code or "").strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_activation_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def registry_enabled() -> bool:
    return bool(getattr(settings, "PLATFORM_SAAS_ENABLED", False)) and bool(
        getattr(settings, "LICENSE_REGISTRY_API_ENABLED", True)
    )


def envato_configured() -> bool:
    return bool((getattr(settings, "CODECANYON_TOKEN", None) or "").strip())


def expected_envato_item_ids() -> set[str]:
    raw = (getattr(settings, "CODECANYON_PRODUCT_ID", None) or "").strip()
    if not raw:
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}


def item_id_allowed(item_id: int | None) -> bool:
    allowed = expected_envato_item_ids()
    if not allowed:
        return True
    if item_id is None:
        return False
    return str(item_id) in allowed


def parse_comma_id_set(raw: str | None) -> set[str]:
    return {x.strip() for x in (raw or "").split(",") if x.strip()}


def resolve_plan_type_for_item_id(item_id: int | None) -> str:
    """Map Envato item id to basic | saas using explicit lists or default."""
    basic_ids = parse_comma_id_set(getattr(settings, "CODECANYON_BASIC_ITEM_IDS", ""))
    saas_ids = parse_comma_id_set(getattr(settings, "CODECANYON_SAAS_ITEM_IDS", ""))
    sid = str(item_id) if item_id is not None else ""
    if sid and sid in saas_ids:
        return PLAN_SAAS
    if sid and sid in basic_ids:
        return PLAN_BASIC
    default = (getattr(settings, "CODECANYON_DEFAULT_SELF_HOSTED_PLAN_TYPE", "") or PLAN_SAAS).strip().lower()
    if default not in (PLAN_BASIC, PLAN_SAAS):
        default = PLAN_SAAS
    if basic_ids or saas_ids:
        return default
    return default


def effective_plan_type_for_installation(inst: LicenseRegistryInstallation) -> str:
    o = normalize_plan_type(inst.plan_type_override)
    if o:
        return o
    p = normalize_plan_type(inst.purchase.plan_type)
    if p:
        return p
    return resolve_plan_type_for_item_id(inst.purchase.envato_item_id)


def _version_tuple(v: str) -> tuple[int, ...]:
    out: list[int] = []
    for part in (v or "").strip().split("."):
        acc = ""
        for c in part:
            if c.isdigit():
                acc += c
            else:
                break
        out.append(int(acc) if acc else 0)
    pad = out + [0, 0, 0]
    return tuple(pad[:4])


def compute_update_available(client_version: str) -> bool:
    latest = (getattr(settings, "LICENSE_REGISTRY_LATEST_VERSION", None) or "").strip()
    cv = (client_version or "").strip()
    if not latest or not cv:
        return False
    return _version_tuple(cv) < _version_tuple(latest)


def public_payload_for_installation(
    inst: LicenseRegistryInstallation,
    *,
    app_version: str = "",
) -> dict:
    plan = effective_plan_type_for_installation(inst)
    feats = features_for_plan(plan)
    derived = compute_display_status(inst)
    status_str = (
        "active" if derived == LicenseRegistryInstallation.STATUS_ACTIVE else derived
    )
    return {
        "plan_type": plan,
        "features": feats,
        "features_snapshot": features_snapshot_list(plan),
        "update_available": compute_update_available(app_version),
        "registry_status": derived,
        "status": status_str,
    }


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, timezone.datetime):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    try:
        from dateutil import parser as date_parser

        dt = date_parser.isoparse(str(value))
        return dt if timezone.is_aware(dt) else timezone.make_aware(dt)
    except Exception:
        return None


def parse_positive_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def _country_from_ip(ip: str | None) -> str:
    if not ip or ip in ("127.0.0.1", "::1", "unknown"):
        return ""
    path = (getattr(settings, "GEOIP2_COUNTRY_DATABASE", None) or "").strip()
    if not path:
        return ""
    try:
        import geoip2.errors
        import geoip2.database
    except ImportError:
        return ""
    try:
        with geoip2.database.Reader(path) as reader:
            rec = reader.country(ip)
            return (rec.country.iso_code or "")[:2].upper()
    except (geoip2.errors.AddressNotFoundError, ValueError, OSError):
        return ""


def _telemetry_update_fields(
    inst: LicenseRegistryInstallation,
    *,
    screen_count: int | None,
    user_count: int | None,
    tz_name: str,
    client_ip: str | None,
) -> list[str]:
    now = timezone.now()
    fields: list[str] = []
    if screen_count is not None:
        inst.last_screen_count = min(screen_count, 2_000_000_000)
        fields.append("last_screen_count")
    if user_count is not None:
        inst.last_user_count = min(user_count, 2_000_000_000)
        fields.append("last_user_count")
    tz = (tz_name or "").strip()[:64]
    if tz:
        inst.last_timezone = tz
        fields.append("last_timezone")
    cc = _country_from_ip(client_ip)
    if cc:
        inst.last_reported_country = cc
        fields.append("last_reported_country")
    if fields:
        inst.telemetry_at = now
        fields.append("telemetry_at")
    return fields


def _mark_suspicious_siblings(purchase: LicenseRegistryPurchase, domain: str) -> None:
    qs = LicenseRegistryInstallation.objects.filter(purchase=purchase).exclude(domain=domain)
    if qs.exists():
        LicenseRegistryInstallation.objects.filter(purchase=purchase).update(suspicious=True)


@transaction.atomic
def activate_installation(
    purchase_code: str,
    domain: str,
    product_id: str = "",
    app_version: str = "",
    client_ip: str | None = None,
    *,
    screen_count: int | None = None,
    user_count: int | None = None,
    tz_name: str = "",
) -> tuple[LicenseRegistryInstallation, str, dict]:
    """
    Verify with Envato, upsert purchase + installation, return (installation, plaintext_token, response_extra).
    """
    if not registry_enabled():
        raise PermissionError("License registry API is disabled")
    if not envato_configured():
        raise EnvatoApiError("License gateway is not configured (missing CODECANYON_TOKEN)", status_code=503)

    domain = (domain or "").strip().lower()
    if not domain:
        raise ValueError("domain is required")

    sale = fetch_sale_by_purchase_code(purchase_code)
    item_id = parse_sale_item_id(sale)
    if not item_id_allowed(item_id):
        raise ValueError("This purchase is not for a permitted Envato item ID")

    pid = (product_id or "").strip()
    if pid and item_id is not None and str(item_id) != pid:
        raise ValueError("Purchase code does not match the configured product ID")

    fingerprint = purchase_code_fingerprint(purchase_code)
    buyer = (sale.get("buyer") or sale.get("buyer_username") or "") if isinstance(sale, dict) else ""
    if isinstance(buyer, dict):
        buyer = buyer.get("username") or buyer.get("name") or ""

    resolved_plan = resolve_plan_type_for_item_id(item_id)
    purchase, _ = LicenseRegistryPurchase.objects.update_or_create(
        code_fingerprint=fingerprint,
        defaults={
            "envato_item_id": item_id,
            "buyer_username": str(buyer)[:191] if buyer else "",
            "sold_at": _parse_dt(sale.get("sold_at")),
            "support_until": _parse_dt(sale.get("support_until")),
            "license_type": str(sale.get("license") or "")[:64],
            "plan_type": resolved_plan,
            "raw_sale": sale if isinstance(sale, dict) else {},
        },
    )

    _mark_suspicious_siblings(purchase, domain)

    token = secrets.token_urlsafe(48)
    th = hash_activation_token(token)

    existing = LicenseRegistryInstallation.objects.select_for_update().filter(
        purchase=purchase, domain=domain
    ).first()

    if existing:
        existing.token_hash = th
        existing.app_version = (app_version or "")[:128]
        existing.last_heartbeat_at = timezone.now()
        existing.suspended = False
        existing.suspended_reason = ""
        extra_tf = _telemetry_update_fields(
            existing,
            screen_count=screen_count,
            user_count=user_count,
            tz_name=tz_name,
            client_ip=client_ip,
        )
        existing.save(
            update_fields=[
                "token_hash",
                "app_version",
                "last_heartbeat_at",
                "suspended",
                "suspended_reason",
                "updated_at",
                *extra_tf,
            ]
        )
        inst = existing
    else:
        inst = LicenseRegistryInstallation.objects.create(
            purchase=purchase,
            domain=domain,
            token_hash=th,
            app_version=(app_version or "")[:128],
            last_heartbeat_at=timezone.now(),
        )
        extra_tf = _telemetry_update_fields(
            inst,
            screen_count=screen_count,
            user_count=user_count,
            tz_name=tz_name,
            client_ip=client_ip,
        )
        if extra_tf:
            inst.save(update_fields=[*extra_tf, "updated_at"])

    LicenseRegistryHeartbeatLog.objects.create(
        installation=inst,
        app_version=(app_version or "")[:128],
        ip_address=client_ip or None,
    )

    extra = {
        "buyer_username": purchase.buyer_username,
        "envato_item_id": purchase.envato_item_id,
        **public_payload_for_installation(inst, app_version=app_version),
    }
    return inst, token, extra


def record_heartbeat(
    token: str,
    domain: str,
    app_version: str = "",
    client_ip: str | None = None,
    *,
    screen_count: int | None = None,
    user_count: int | None = None,
    tz_name: str = "",
) -> LicenseRegistryInstallation:
    if not registry_enabled():
        raise PermissionError("License registry API is disabled")

    th = hash_activation_token(token)
    try:
        inst = LicenseRegistryInstallation.objects.select_related("purchase").get(token_hash=th)
    except LicenseRegistryInstallation.DoesNotExist as exc:
        raise LookupError("Unknown activation token") from exc

    domain = (domain or "").strip().lower()
    if domain and inst.domain != domain:
        inst.suspicious = True
        _mark_suspicious_siblings(inst.purchase, domain)

    inst.last_heartbeat_at = timezone.now()
    if app_version:
        inst.app_version = app_version[:128]
    extra_tf = _telemetry_update_fields(
        inst,
        screen_count=screen_count,
        user_count=user_count,
        tz_name=tz_name,
        client_ip=client_ip,
    )
    update_fields = ["last_heartbeat_at", "app_version", "suspicious", "updated_at", *extra_tf]
    inst.save(update_fields=update_fields)

    LicenseRegistryHeartbeatLog.objects.create(
        installation=inst,
        app_version=(app_version or "")[:128],
        ip_address=client_ip or None,
    )
    return inst


def validate_by_token(
    token: str,
    domain: str | None = None,
    *,
    app_version: str = "",
) -> tuple[bool, dict]:
    """
    Return (is_valid, payload_dict) for self-hosted validate call.
    """
    if not registry_enabled():
        return False, {"valid": False, "status": "invalid", "message": "Registry disabled"}

    th = hash_activation_token(token)
    try:
        inst = LicenseRegistryInstallation.objects.select_related("purchase").get(token_hash=th)
    except LicenseRegistryInstallation.DoesNotExist:
        return False, {"valid": False, "status": "invalid", "message": "Unknown activation token"}

    pub = public_payload_for_installation(inst, app_version=app_version)

    if inst.suspended:
        return False, {
            "valid": False,
            "status": "suspended",
            "message": "License suspended by operator",
            **{k: pub[k] for k in ("plan_type", "features", "features_snapshot") if k in pub},
        }

    if domain and (domain or "").strip().lower() != inst.domain:
        return False, {"valid": False, "status": "invalid", "message": "Domain mismatch"}

    max_age = int(getattr(settings, "LICENSE_REGISTRY_HEARTBEAT_MAX_AGE_HOURS", 0) or 0)
    if max_age > 0 and inst.last_heartbeat_at:
        cutoff = timezone.now() - timedelta(hours=max_age)
        if inst.last_heartbeat_at < cutoff:
            return False, {
                "valid": False,
                "status": "inactive",
                "message": "No recent heartbeat; renew contact with license gateway",
            }

    derived = compute_display_status(inst)
    return True, {
        "valid": True,
        "status": "active" if derived == LicenseRegistryInstallation.STATUS_ACTIVE else derived,
        "license_status": derived,
        "message": "OK",
        **pub,
    }


def resolve_installation_for_ticket_ingest(
    token: str,
    domain: str | None = None,
    *,
    app_version: str = "",
) -> LicenseRegistryInstallation:
    """
    Resolve registry installation for self-hosted ticket ingest (Bearer activation token).

    Raises PermissionError if registry disabled or license suspended.
    Raises LookupError if the token is unknown or validation fails.
    """
    if not registry_enabled():
        raise PermissionError("License registry API is disabled")
    ok, payload = validate_by_token(token, domain=domain or None, app_version=app_version)
    if not ok:
        msg = (payload or {}).get("message") or "Invalid token"
        st = (payload or {}).get("status") or ""
        if st == "suspended":
            raise PermissionError(msg)
        raise LookupError(msg)
    th = hash_activation_token(token)
    return LicenseRegistryInstallation.objects.select_related("purchase").get(token_hash=th)


def compute_display_status(inst: LicenseRegistryInstallation) -> str:
    if inst.suspended:
        return LicenseRegistryInstallation.STATUS_SUSPENDED
    if inst.suspicious:
        return LicenseRegistryInstallation.STATUS_SUSPICIOUS

    inactive_hours = int(getattr(settings, "LICENSE_REGISTRY_INACTIVE_AFTER_HOURS", 72) or 72)
    now = timezone.now()
    last = inst.last_heartbeat_at
    if not last:
        return LicenseRegistryInstallation.STATUS_PENDING
    if last < now - timedelta(hours=inactive_hours):
        return LicenseRegistryInstallation.STATUS_INACTIVE
    return LicenseRegistryInstallation.STATUS_ACTIVE


def validate_legacy_purchase_body(
    purchase_code: str,
    domain: str,
    product_id: str = "",
) -> tuple[bool, dict]:
    """
    Expensive path: verify purchase code with Envato on each call (legacy self-hosted client).
    """
    if not registry_enabled():
        return False, {"valid": False, "status": "invalid", "message": "Registry disabled"}
    if not envato_configured():
        return False, {"valid": False, "status": "invalid", "message": "Gateway not configured"}

    try:
        sale = fetch_sale_by_purchase_code(purchase_code)
    except EnvatoApiError as exc:
        return False, {"valid": False, "status": "invalid", "message": str(exc)}

    item_id = parse_sale_item_id(sale)
    if not item_id_allowed(item_id):
        return False, {"valid": False, "status": "invalid", "message": "Item not permitted"}

    pid = (product_id or "").strip()
    if pid and item_id is not None and str(item_id) != pid:
        return False, {"valid": False, "status": "invalid", "message": "Product mismatch"}

    return True, {"valid": True, "status": "active", "message": "OK", "domain": (domain or "").strip()}
