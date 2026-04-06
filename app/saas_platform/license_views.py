"""Platform tenant license management — Developer only."""

from __future__ import annotations

import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from licensing.models import LicenseEnforcementLog, TenantLicenseState
from .models import Tenant
from .permissions import IsDeveloper

logger = logging.getLogger(__name__)


def _saas():
    return bool(getattr(settings, 'PLATFORM_SAAS_ENABLED', False))


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsDeveloper])
def tenant_license_view(request, tenant_id):
    if not _saas():
        return Response({'detail': 'SaaS not enabled.'}, status=403)
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    state, _ = TenantLicenseState.objects.get_or_create(tenant=tenant)

    if request.method == 'GET':
        return Response(_serialize(state))

    data = request.data
    changed = []
    if 'license_key' in data:
        state.license_key = (data['license_key'] or '').strip()[:128]
        changed.append('license_key')
    if 'license_status' in data:
        new_status = data['license_status']
        valid = {c[0] for c in TenantLicenseState.STATUS_CHOICES}
        if new_status not in valid:
            return Response({'detail': f'Invalid status. Choose from {sorted(valid)}'}, status=400)
        state.license_status = new_status
        changed.append('license_status')
        if new_status == 'active' and not state.activated_at:
            state.activated_at = timezone.now()
            changed.append('activated_at')
    if 'offline_grace_hours' in data:
        state.offline_grace_hours = max(0, int(data['offline_grace_hours']))
        changed.append('offline_grace_hours')

    if changed:
        state.save()
        LicenseEnforcementLog.objects.create(
            tenant=tenant, action='license_updated', decision='manual',
            details={'changed_fields': changed, 'actor': request.user.username},
        )

    return Response(_serialize(state))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDeveloper])
def tenant_license_enforcement_logs(request, tenant_id):
    if not _saas():
        return Response({'detail': 'SaaS not enabled.'}, status=403)
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    logs = LicenseEnforcementLog.objects.filter(tenant=tenant)[:200]
    return Response({
        'results': [
            {
                'id': str(l.id),
                'action': l.action,
                'decision': l.decision,
                'details': l.details,
                'created_at': l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    })


def _serialize(state):
    return {
        'id': str(state.id),
        'tenant_id': str(state.tenant_id),
        'license_key': state.license_key,
        'license_status': state.license_status,
        'activated_at': state.activated_at.isoformat() if state.activated_at else None,
        'last_validation_at': state.last_validation_at.isoformat() if state.last_validation_at else None,
        'grace_until': state.grace_until.isoformat() if state.grace_until else None,
        'offline_grace_hours': state.offline_grace_hours,
        'is_entitled': state.is_entitled(),
        'last_error': state.last_error,
        'created_at': state.created_at.isoformat() if state.created_at else None,
        'updated_at': state.updated_at.isoformat() if state.updated_at else None,
    }
