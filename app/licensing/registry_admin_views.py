"""Super-admin (platform) API for self-hosted license registry rows."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from licensing.models import LicenseRegistryHeartbeatLog, LicenseRegistryInstallation
from licensing.registry_service import compute_display_status, effective_plan_type_for_installation
from core.permissions import IsDeveloperPlatformAccess


def _saas():
    return bool(getattr(settings, "PLATFORM_SAAS_ENABLED", False))


def _serialize_installation(inst: LicenseRegistryInstallation) -> dict:
    purchase = inst.purchase
    return {
        "id": str(inst.id),
        "domain": inst.domain,
        "app_version": inst.app_version,
        "last_heartbeat_at": inst.last_heartbeat_at.isoformat() if inst.last_heartbeat_at else None,
        "activated_at": inst.activated_at.isoformat() if inst.activated_at else None,
        "suspended": inst.suspended,
        "suspended_reason": inst.suspended_reason,
        "suspicious": inst.suspicious,
        "notes": inst.notes,
        "display_status": compute_display_status(inst),
        "last_screen_count": inst.last_screen_count,
        "last_user_count": inst.last_user_count,
        "last_timezone": inst.last_timezone or "",
        "telemetry_at": inst.telemetry_at.isoformat() if inst.telemetry_at else None,
        "last_reported_country": inst.last_reported_country or "",
        "plan_type": effective_plan_type_for_installation(inst),
        "plan_type_override": (inst.plan_type_override or "").strip(),
        "purchase": {
            "code_fingerprint": purchase.code_fingerprint,
            "buyer_username": purchase.buyer_username,
            "envato_item_id": purchase.envato_item_id,
            "sold_at": purchase.sold_at.isoformat() if purchase.sold_at else None,
            "support_until": purchase.support_until.isoformat() if purchase.support_until else None,
            "license_type": purchase.license_type,
            "plan_type": purchase.plan_type or "",
        },
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsDeveloperPlatformAccess])
def self_hosted_license_list(request):
    if not _saas():
        return Response({"detail": "SaaS not enabled."}, status=403)

    try:
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(500, max(1, int(request.query_params.get("page_size", 100))))
    except (TypeError, ValueError):
        page, page_size = 1, 100

    inactive_hours = int(getattr(settings, "LICENSE_REGISTRY_INACTIVE_AFTER_HOURS", 72) or 72)
    cutoff = timezone.now() - timedelta(hours=inactive_hours)

    qs = LicenseRegistryInstallation.objects.select_related("purchase").order_by(
        "-last_heartbeat_at", "-activated_at"
    )
    status_filter = (request.query_params.get("status") or "").strip().lower()
    if status_filter == "suspended":
        qs = qs.filter(suspended=True)
    elif status_filter == "suspicious":
        qs = qs.filter(suspicious=True)
    elif status_filter == "pending":
        qs = qs.filter(last_heartbeat_at__isnull=True, suspended=False)
    elif status_filter == "inactive":
        qs = qs.filter(last_heartbeat_at__lt=cutoff, suspended=False, suspicious=False)
    elif status_filter == "active":
        qs = qs.filter(last_heartbeat_at__gte=cutoff, suspended=False, suspicious=False)

    plan_filter = (request.query_params.get("plan") or "").strip().lower()
    if plan_filter in ("basic", "saas"):
        qs = qs.filter(
            Q(plan_type_override__iexact=plan_filter)
            | (Q(plan_type_override="") & Q(purchase__plan_type__iexact=plan_filter))
        )

    total = qs.count()
    start = (page - 1) * page_size
    slice_qs = qs[start : start + page_size]
    data = [_serialize_installation(x) for x in slice_qs]
    return Response(
        {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": data,
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsDeveloperPlatformAccess])
def self_hosted_license_detail(request, pk):
    if not _saas():
        return Response({"detail": "SaaS not enabled."}, status=403)
    inst = get_object_or_404(LicenseRegistryInstallation.objects.select_related("purchase"), pk=pk)
    if request.method == "GET":
        return Response(_serialize_installation(inst))

    if "plan_type_override" not in request.data:
        return Response(
            {"detail": "PATCH requires plan_type_override (use empty string to clear)."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    v = (request.data.get("plan_type_override") or "").strip().lower()
    if v not in ("", "basic", "saas"):
        return Response(
            {"detail": "plan_type_override must be '', 'basic', or 'saas'."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    inst.plan_type_override = v
    inst.save(update_fields=["plan_type_override", "updated_at"])
    return Response(_serialize_installation(inst))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsDeveloperPlatformAccess])
def self_hosted_license_suspend(request, pk):
    if not _saas():
        return Response({"detail": "SaaS not enabled."}, status=403)
    inst = get_object_or_404(LicenseRegistryInstallation, pk=pk)
    reason = (request.data.get("reason") or "").strip()[:2000]
    inst.suspended = True
    inst.suspended_reason = reason or "Suspended by operator"
    inst.save(update_fields=["suspended", "suspended_reason", "updated_at"])
    return Response(_serialize_installation(inst))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsDeveloperPlatformAccess])
def self_hosted_license_reactivate(request, pk):
    if not _saas():
        return Response({"detail": "SaaS not enabled."}, status=403)
    inst = get_object_or_404(LicenseRegistryInstallation, pk=pk)
    inst.suspended = False
    inst.suspended_reason = ""
    inst.save(update_fields=["suspended", "suspended_reason", "updated_at"])
    return Response(_serialize_installation(inst))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsDeveloperPlatformAccess])
def self_hosted_license_suspicious(request, pk):
    if not _saas():
        return Response({"detail": "SaaS not enabled."}, status=403)
    inst = get_object_or_404(LicenseRegistryInstallation, pk=pk)
    flag = request.data.get("suspicious")
    inst.suspicious = bool(flag) if flag is not None else not inst.suspicious
    inst.save(update_fields=["suspicious", "updated_at"])
    return Response(_serialize_installation(inst))


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsDeveloperPlatformAccess])
def self_hosted_license_heartbeats(request, pk):
    if not _saas():
        return Response({"detail": "SaaS not enabled."}, status=403)
    inst = get_object_or_404(LicenseRegistryInstallation, pk=pk)
    logs = LicenseRegistryHeartbeatLog.objects.filter(installation=inst).order_by("-received_at")[:100]
    return Response({
        "results": [
            {
                "id": str(l.id),
                "received_at": l.received_at.isoformat() if l.received_at else None,
                "app_version": l.app_version,
                "ip_address": l.ip_address,
            }
            for l in logs
        ]
    })
