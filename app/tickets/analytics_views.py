"""
Platform ticket analytics and export endpoints.

Provides aggregated metrics for the super-admin dashboard:
volume, SLA compliance, agent performance, CSAT, and CSV export.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import timedelta

from django.db.models import Avg, Count, DurationField, F, Q
from django.db.models.expressions import ExpressionWrapper
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Ticket, TicketCsatRating, TicketMessage, TicketSlaSnapshot,
)
from .permissions import IsPlatformTicketAdmin

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformTicketAdmin])
def ticket_analytics(request):
    """
    Aggregated ticket metrics for the super-admin analytics dashboard.

    Query params:
        tenant_id   – scope to a single tenant (optional)
        days        – lookback window (default 30)
    """
    tenant_id = request.query_params.get('tenant_id')
    days = int(request.query_params.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    base = Ticket.objects.filter(is_deleted=False, created_at__gte=since)
    if tenant_id:
        base = base.filter(tenant_id=tenant_id)

    total = base.count()
    by_status = list(
        base.values('status').annotate(count=Count('id')).order_by('status')
    )
    by_priority = list(
        base.values('priority').annotate(count=Count('id')).order_by('priority')
    )

    open_count = base.filter(status__in=['open', 'assigned', 'in_progress', 'pending']).count()

    resolved = base.filter(resolved_at__isnull=False)
    avg_resolution_min = None
    if resolved.exists():
        avg_td = resolved.annotate(
            dur=F('resolved_at') - F('created_at')
        ).aggregate(avg=Avg('dur'))['avg']
        if avg_td:
            avg_resolution_min = avg_td.total_seconds() / 60

    responded = base.filter(first_responded_at__isnull=False)
    avg_first_response_min = None
    if responded.exists():
        avg_td = responded.annotate(
            dur=F('first_responded_at') - F('created_at')
        ).aggregate(avg=Avg('dur'))['avg']
        if avg_td:
            avg_first_response_min = avg_td.total_seconds() / 60

    sla_base = TicketSlaSnapshot.objects.filter(ticket__created_at__gte=since)
    if tenant_id:
        sla_base = sla_base.filter(ticket__tenant_id=tenant_id)
    total_sla = sla_base.count()
    achieved_sla = sla_base.filter(status='achieved').count()
    sla_compliance_pct = round(achieved_sla / total_sla * 100, 1) if total_sla else 0

    csat_base = TicketCsatRating.objects.filter(created_at__gte=since)
    if tenant_id:
        csat_base = csat_base.filter(ticket__tenant_id=tenant_id)
    avg_csat = csat_base.aggregate(avg=Avg('score'))['avg']
    csat_dist = {}
    for row in csat_base.values('score').annotate(count=Count('id')):
        csat_dist[row['score']] = row['count']

    by_tenant = []
    if not tenant_id:
        by_tenant = list(
            base.values('tenant__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )

    by_category = list(
        base.values('category').annotate(count=Count('id')).order_by('-count')[:40]
    )

    by_client_version = list(
        base.exclude(client_version='')
        .values('client_version')
        .annotate(count=Count('id'))
        .order_by('-count')[:30]
    )

    dur_expr = ExpressionWrapper(
        F('resolved_at') - F('created_at'),
        output_field=DurationField(),
    )
    resolved_with_dur = base.filter(resolved_at__isnull=False).annotate(dur=dur_expr)

    resolution_by_client_version = []
    rv_qs = (
        resolved_with_dur.exclude(client_version='')
        .values('client_version')
        .annotate(avg_resolution=Avg('dur'))
        .order_by('-avg_resolution')[:20]
    )
    for row in rv_qs:
        td = row['avg_resolution']
        mins = round(td.total_seconds() / 60, 1) if td else None
        resolution_by_client_version.append(
            {'client_version': row['client_version'], 'avg_resolution_min': mins}
        )

    resolution_by_deployment = []
    dep_qs = (
        resolved_with_dur.exclude(deployment_context='')
        .values('deployment_context')
        .annotate(avg_resolution=Avg('dur'))
        .order_by('deployment_context')
    )
    for row in dep_qs:
        td = row['avg_resolution']
        mins = round(td.total_seconds() / 60, 1) if td else None
        resolution_by_deployment.append(
            {'deployment_context': row['deployment_context'], 'avg_resolution_min': mins}
        )

    return Response({
        'total': total,
        'open_count': open_count,
        'by_status': by_status,
        'by_priority': by_priority,
        'by_category': by_category,
        'by_client_version': by_client_version,
        'resolution_by_client_version': resolution_by_client_version,
        'resolution_by_deployment': resolution_by_deployment,
        'avg_first_response_min': round(avg_first_response_min, 1) if avg_first_response_min else None,
        'avg_resolution_min': round(avg_resolution_min, 1) if avg_resolution_min else None,
        'sla_compliance_pct': sla_compliance_pct,
        'avg_csat': round(avg_csat, 2) if avg_csat else None,
        'csat_distribution': csat_dist,
        'by_tenant': by_tenant,
        'days': days,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformTicketAdmin])
def ticket_export_csv(request):
    """Export tickets as CSV."""
    tenant_id = request.query_params.get('tenant_id')
    days = int(request.query_params.get('days', 90))
    since = timezone.now() - timedelta(days=days)

    qs = Ticket.objects.filter(
        is_deleted=False, created_at__gte=since,
    ).select_related('tenant', 'requester', 'assignee', 'queue')
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'Number', 'Subject', 'Status', 'Priority', 'Tenant',
        'Requester', 'Assignee', 'Queue', 'Created', 'Resolved', 'Closed',
    ])
    for t in qs.iterator():
        writer.writerow([
            t.number,
            t.subject,
            t.status,
            t.priority,
            t.tenant.name if t.tenant else '',
            t.requester.email if t.requester else '',
            t.assignee.email if t.assignee else '',
            t.queue.name if t.queue else '',
            t.created_at.isoformat() if t.created_at else '',
            t.resolved_at.isoformat() if t.resolved_at else '',
            t.closed_at.isoformat() if t.closed_at else '',
        ])

    response = HttpResponse(buf.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tickets_export.csv"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPlatformTicketAdmin])
def agent_performance(request):
    """Agent workload and performance metrics."""
    days = int(request.query_params.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    assigned = (
        Ticket.objects.filter(
            is_deleted=False, assignee__isnull=False, created_at__gte=since,
        )
        .values('assignee__email', 'assignee__full_name', 'assignee__username')
        .annotate(
            total=Count('id'),
            open=Count('id', filter=Q(status__in=['open', 'assigned', 'in_progress', 'pending'])),
            resolved=Count('id', filter=Q(status='resolved')),
            closed=Count('id', filter=Q(status='closed')),
        )
        .order_by('-total')[:50]
    )

    agents = []
    for row in assigned:
        name = row['assignee__full_name'] or row['assignee__username'] or row['assignee__email']
        agents.append({
            'email': row['assignee__email'],
            'name': name,
            'total': row['total'],
            'open': row['open'],
            'resolved': row['resolved'],
            'closed': row['closed'],
        })

    return Response({'agents': agents, 'days': days})
