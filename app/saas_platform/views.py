"""Platform (super admin) API — tenants only (CodeCanyon-safe distribution)."""

from __future__ import annotations

import logging
import re

from django.conf import settings
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.audit import AuditLogger

from .models import Tenant, TenantAuditLog
from .permissions import IsDeveloper
from .serializers import (
    ManualOverrideSerializer,
    TenantAuditLogSerializer,
    TenantDetailSerializer,
    TenantListSerializer,
    TenantWriteSerializer,
)

logger = logging.getLogger(__name__)


def _saas_enabled():
    return bool(getattr(settings, 'PLATFORM_SAAS_ENABLED', False))


class PlatformSaaSViewSet(viewsets.ModelViewSet):
    """Base: 403 when PLATFORM_SAAS_ENABLED is False."""

    from rest_framework.permissions import IsAuthenticated

    permission_classes = [IsAuthenticated, IsDeveloper]

    def dispatch(self, request, *args, **kwargs):
        if not _saas_enabled():
            from django.http import JsonResponse

            return JsonResponse(
                {'detail': 'Platform SaaS features are disabled (set PLATFORM_SAAS_ENABLED=true).'},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)


class TenantViewSet(PlatformSaaSViewSet):
    queryset = Tenant.objects.all().order_by('name')
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TenantWriteSerializer
        if self.action == 'retrieve':
            return TenantDetailSerializer
        return TenantListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('search')
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(slug__icontains=q) | Q(organization_name_key__icontains=q)
            )
        st = self.request.query_params.get('status')
        if st:
            qs = qs.filter(subscription_status=st)
        alert = self.request.query_params.get('alert')
        if alert == 'payment_failed':
            qs = qs.exclude(last_payment_failed_at__isnull=True)
        return qs.distinct()

    def create(self, request, *args, **kwargs):
        ser = TenantWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tenant = ser.save()
        TenantAuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action='tenant_created',
            details={'name': tenant.name, 'slug': tenant.slug},
        )
        try:
            AuditLogger.log_action(
                action_type='create',
                user=request.user,
                resource=tenant,
                description=f'Created tenant {tenant.slug}',
                changes={'name': tenant.name},
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response(
            TenantDetailSerializer(tenant, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        tenant = self.get_object()
        partial = kwargs.pop('partial', False)
        ser = TenantWriteSerializer(tenant, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        tenant = ser.save()
        TenantAuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action='tenant_updated',
            details=ser.validated_data,
        )
        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=tenant,
                description=f'Updated tenant {tenant.slug}',
                changes=ser.validated_data,
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response(TenantDetailSerializer(tenant, context={'request': request}).data)

    def destroy(self, request, *args, **kwargs):
        tenant = self.get_object()
        tenant_name = tenant.name
        tenant_slug = tenant.slug
        tenant_id = str(tenant.id)
        tenant.delete()
        try:
            AuditLogger.log_action(
                action_type='delete',
                user=request.user,
                resource_type='Tenant',
                resource_name=f'{tenant_name} ({tenant_slug})',
                description=f'Deleted tenant {tenant_slug}',
                changes={'deleted_tenant_id': tenant_id},
                severity='critical',
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response({'status': 'deleted', 'id': tenant_id})

    @action(detail=True, methods=['post'], url_path='access-lock')
    def access_lock(self, request, pk=None):
        tenant = self.get_object()
        reason = (request.data.get('reason') or '').strip()[:255]
        lock_until = request.data.get('lock_until')
        tenant.access_locked = True
        tenant.access_lock_reason = reason
        if lock_until:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as tz

            parsed = parse_datetime(str(lock_until))
            if parsed:
                if tz.is_naive(parsed):
                    parsed = tz.make_aware(parsed, tz.get_current_timezone())
                tenant.access_lock_until = parsed
        tenant.save(update_fields=['access_locked', 'access_lock_reason', 'access_lock_until'])
        TenantAuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action='access_lock',
            details={'reason': reason},
        )
        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=tenant,
                description=f'Locked tenant access: {tenant.slug}',
                changes={'access_locked': True, 'reason': reason},
                severity='critical',
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response(TenantDetailSerializer(tenant, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='access-unlock')
    def access_unlock(self, request, pk=None):
        tenant = self.get_object()
        tenant.access_locked = False
        tenant.access_lock_reason = ''
        tenant.access_lock_until = None
        tenant.save(update_fields=['access_locked', 'access_lock_reason', 'access_lock_until'])
        TenantAuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action='access_unlock',
            details={},
        )
        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=tenant,
                description=f'Unlocked tenant access: {tenant.slug}',
                changes={'access_locked': False},
                severity='high',
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response(TenantDetailSerializer(tenant, context={'request': request}).data)

    @action(detail=True, methods=['get', 'put'], url_path='feature-flags')
    def feature_flags(self, request, pk=None):
        tenant = self.get_object()
        if request.method == 'GET':
            return Response(tenant.feature_flags or {})
        body = request.data
        if not isinstance(body, dict):
            return Response(
                {'detail': 'Request body must be a JSON object.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _FLAG_KEY_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        for key in body:
            if not _FLAG_KEY_RE.match(key):
                return Response(
                    {'detail': f'Invalid flag key: "{key}". Use snake_case alphanumeric.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        merged = {**(tenant.feature_flags or {}), **body}
        tenant.feature_flags = merged
        tenant.save(update_fields=['feature_flags'])
        TenantAuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action='feature_flags_update',
            details={'keys': list(body.keys())},
        )
        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=tenant,
                description=f'Updated feature flags for tenant {tenant.slug}',
                changes={'flags': body},
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response(merged)

    @action(detail=True, methods=['post'], url_path='manual-override')
    def manual_override(self, request, pk=None):
        tenant = self.get_object()
        ser = ManualOverrideSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if 'manual_access_until' in data:
            tenant.manual_access_until = data['manual_access_until']
        if 'device_limit' in data and data['device_limit'] is not None:
            tenant.device_limit = data['device_limit']
        if data.get('notes'):
            tenant.manual_notes = (tenant.manual_notes or '') + '\n' + data['notes']
        tenant.save()
        TenantAuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action='manual_override',
            details=data,
        )
        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=tenant,
                description=f'Manual billing override for tenant {tenant.slug}',
                changes=data,
                request=request,
            )
        except Exception as e:
            logger.error('audit log failed: %s', e)
        return Response(TenantDetailSerializer(tenant, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='audit-log')
    def audit_log(self, request, pk=None):
        tenant = self.get_object()
        logs = tenant.audit_logs.all()[:100]
        return Response(TenantAuditLogSerializer(logs, many=True).data)
