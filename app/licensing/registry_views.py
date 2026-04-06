"""
Public HTTP API for self-hosted instances → operator license gateway (SaaS).
"""

from __future__ import annotations

import logging
import uuid

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .envato import EnvatoApiError
from .registry_service import (
    activate_installation,
    parse_positive_int,
    public_payload_for_installation,
    record_heartbeat,
    registry_enabled,
    resolve_installation_for_ticket_ingest,
    validate_by_token,
    validate_legacy_purchase_body,
)

logger = logging.getLogger(__name__)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _rate_allow(request, prefix: str, limit: int, window: int) -> bool:
    ip = _client_ip(request)
    key = f"licreg_rl:{prefix}:{ip}"
    n = cache.get(key, 0)
    if n >= limit:
        return False
    cache.set(key, n + 1, window)
    return True


class RegistryDisabledMixin:
    def dispatch(self, request, *args, **kwargs):
        if not registry_enabled():
            return JsonResponse(
                {"detail": "License registry API is not enabled on this deployment."},
                status=404,
            )
        return super().dispatch(request, *args, **kwargs)


class RegistryActivateView(RegistryDisabledMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        lim = int(getattr(settings, "LICENSE_REGISTRY_ACTIVATE_RATE_PER_MINUTE", 20) or 20)
        if not _rate_allow(request, "activate", lim, 60):
            return Response({"detail": "Too many requests"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        data = request.data or {}
        purchase_code = (data.get("purchase_code") or "").strip()
        domain = (data.get("domain") or request.get_host() or "").strip()
        product_id = (data.get("product_id") or "").strip()
        app_version = (data.get("app_version") or "").strip()
        sc = parse_positive_int(data.get("screen_count"))
        uc = parse_positive_int(data.get("user_count"))
        tz_name = (data.get("timezone") or data.get("tz") or "").strip()

        try:
            _inst, token, extra = activate_installation(
                purchase_code=purchase_code,
                domain=domain,
                product_id=product_id,
                app_version=app_version,
                client_ip=_client_ip(request),
                screen_count=sc,
                user_count=uc,
                tz_name=tz_name,
            )
        except EnvatoApiError as exc:
            code = exc.status_code or 502
            if code == 404:
                return Response(
                    {"valid": False, "status": "invalid", "message": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"valid": False, "status": "invalid", "message": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE if code == 503 else status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError as exc:
            return Response({"valid": False, "status": "invalid", "message": str(exc)}, status=400)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)

        return Response(
            {
                "valid": True,
                "status": "active",
                "activation_token": token,
                "message": "Activated",
                **extra,
            },
            status=status.HTTP_200_OK,
        )


class RegistryHeartbeatView(RegistryDisabledMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        lim = int(getattr(settings, "LICENSE_REGISTRY_HEARTBEAT_RATE_PER_MINUTE", 60) or 60)
        if not _rate_allow(request, "heartbeat", lim, 60):
            return Response({"detail": "Too many requests"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        auth = request.headers.get("Authorization") or ""
        token = ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
        if not token:
            return Response({"detail": "Bearer activation_token required"}, status=401)

        data = request.data or {}
        domain = (data.get("domain") or request.get_host() or "").strip()
        app_version = (data.get("app_version") or "").strip()
        sc = parse_positive_int(data.get("screen_count"))
        uc = parse_positive_int(data.get("user_count"))
        tz_name = (data.get("timezone") or data.get("tz") or "").strip()

        try:
            inst = record_heartbeat(
                token=token,
                domain=domain,
                app_version=app_version,
                client_ip=_client_ip(request),
                screen_count=sc,
                user_count=uc,
                tz_name=tz_name,
            )
        except LookupError:
            return Response({"ok": False, "message": "Unknown token"}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)

        body = {"ok": True, "message": "OK", **public_payload_for_installation(inst, app_version=app_version)}
        if inst.suspended:
            body["ok"] = False
            body["message"] = "License suspended by operator"
        return Response(body, status=status.HTTP_200_OK)


class RegistryValidateView(RegistryDisabledMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        lim = int(getattr(settings, "LICENSE_REGISTRY_VALIDATE_RATE_PER_MINUTE", 120) or 120)
        if not _rate_allow(request, "validate", lim, 60):
            return Response({"detail": "Too many requests"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        auth = request.headers.get("Authorization") or ""
        bearer = ""
        if auth.lower().startswith("bearer "):
            bearer = auth[7:].strip()

        data = request.data or {}
        domain = (data.get("domain") or "").strip()
        app_version = (data.get("app_version") or "").strip()

        if bearer:
            ok, payload = validate_by_token(bearer, domain=domain or None, app_version=app_version)
            return Response(payload, status=200 if ok else 200)

        purchase_code = (data.get("purchase_code") or "").strip()
        product_id = (data.get("product_id") or "").strip()
        if purchase_code:
            ok, payload = validate_legacy_purchase_body(
                purchase_code=purchase_code,
                domain=domain or request.get_host() or "",
                product_id=product_id,
            )
            return Response(payload, status=200 if ok else 200)

        return Response(
            {"valid": False, "status": "invalid", "message": "Provide Bearer token or purchase_code"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RegistryTicketIngestView(RegistryDisabledMixin, APIView):
    """Self-hosted → operator: mirror tickets into the platform super-admin queue."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        lim = int(settings.LICENSE_REGISTRY_TICKET_INGEST_RATE_PER_MINUTE or 30)
        if not _rate_allow(request, "ticket_ingest", lim, 60):
            return Response({"detail": "Too many requests"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        auth = request.headers.get("Authorization") or ""
        token = ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
        if not token:
            return Response({"detail": "Bearer activation_token required"}, status=401)

        data = request.data or {}
        domain = (data.get("domain") or "").strip()
        app_version = (data.get("app_version") or "").strip()

        try:
            inst = resolve_installation_for_ticket_ingest(
                token, domain=domain or None, app_version=app_version
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except LookupError as exc:
            return Response({"detail": str(exc)}, status=401)

        rid = data.get("remote_ticket_id")
        try:
            remote_uid = uuid.UUID(str(rid))
        except (TypeError, ValueError):
            return Response({"detail": "remote_ticket_id must be a UUID"}, status=400)

        body = (data.get("body") or "").strip()
        subject = (data.get("subject") or "").strip()
        category = (data.get("category") or "").strip()
        language = ((data.get("language") or "en").strip() or "en")[:8]
        priority = (data.get("priority") or "medium").strip() or "medium"
        requester_name = (data.get("requester_name") or "").strip()
        requester_email = (data.get("requester_email") or "").strip()
        client_version = (data.get("client_version") or "").strip()

        from tickets.services import ingest_remote_support_ticket

        try:
            ticket, event = ingest_remote_support_ticket(
                inst,
                remote_uid,
                body,
                subject=subject,
                priority=priority,
                category=category,
                language=language,
                requester_name=requester_name,
                requester_email=requester_email,
                client_version=client_version,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        code = status.HTTP_201_CREATED if event == "created" else status.HTTP_200_OK
        return Response(
            {"id": str(ticket.id), "number": ticket.number, "event": event},
            status=code,
        )
