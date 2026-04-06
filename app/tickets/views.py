"""
Ticket API views.

Two surfaces:
1. Requester API  (/api/tickets/...)          – tenant users manage own tickets
2. Platform API   (/api/platform/tickets/...)  – super-admin queue & settings
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Ticket, TicketAttachment, TicketCannedResponse, TicketCsatRating,
    TicketQueue, TicketRoleProfile, TicketRoutingRule, TicketSlaPolicy,
    TicketTag,
)
from .permissions import (
    CanManageTicketSettings, CanViewTicket, IsPlatformTicketAdmin,
    get_user_tenant, has_ticket_capability,
)
from .serializers import (
    PlatformTicketCreateSerializer, PlatformTicketListSerializer,
    TicketAssignSerializer,
    TicketAttachmentSerializer, TicketCannedResponseSerializer,
    TicketCreateSerializer, TicketCsatSerializer,
    TicketDetailSerializer, TicketListSerializer,
    TicketMergeSerializer, TicketQueueSerializer,
    TicketReplySerializer, TicketRoleProfileSerializer,
    TicketRoutingRuleSerializer, TicketSlaPolicySerializer,
    TicketTagSerializer, TicketTransitionSerializer,
)
from .services import (
    TicketTransitionError, add_reply, assign_ticket, close_ticket,
    create_ticket, escalate_ticket, merge_tickets, pend_ticket,
    reopen_ticket, resolve_ticket, start_progress,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ===================================================================
# Requester API
# ===================================================================

class RequesterTicketViewSet(viewsets.ViewSet):
    """Tenant user ticket operations."""

    permission_classes = [IsAuthenticated]

    def _tenant(self, request):
        return get_user_tenant(request.user)

    def _qs(self, request):
        tenant = self._tenant(request)
        if not tenant:
            return Ticket.objects.none()
        base = Ticket.objects.filter(tenant=tenant, is_deleted=False)
        if has_ticket_capability(request.user, tenant, 'ticket.view_all'):
            return base
        if has_ticket_capability(request.user, tenant, 'ticket.view_queue'):
            return base.filter(
                Q(requester=request.user) | Q(assignee=request.user)
            )
        return base.filter(requester=request.user)

    # -- list --
    def list(self, request):
        qs = self._qs(request).select_related('requester', 'assignee', 'tenant')
        st = request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)
        pri = request.query_params.get('priority')
        if pri:
            qs = qs.filter(priority=pri)
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(Q(subject__icontains=search) | Q(number__icontains=search))
        qs = qs[:100]
        return Response(TicketListSerializer(qs, many=True).data)

    # -- create --
    def create(self, request):
        tenant = self._tenant(request)
        if not tenant:
            return Response({'detail': 'No tenant associated with your account.'}, status=400)
        ser = TicketCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        ticket = create_ticket(
            tenant=tenant,
            requester=request.user,
            subject=d['subject'],
            body=d['body'],
            priority=d.get('priority', 'medium'),
            category=d.get('category', ''),
            language=d.get('language', 'en'),
        )
        return Response(
            TicketDetailSerializer(ticket, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    # -- retrieve --
    def retrieve(self, request, pk=None):
        ticket = get_object_or_404(self._qs(request), pk=pk)
        return Response(TicketDetailSerializer(ticket, context={'request': request}).data)

    # -- reply --
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = get_object_or_404(self._qs(request), pk=pk)
        ser = TicketReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        is_internal = d.get('is_internal', False)
        tenant = ticket.tenant
        if is_internal and not has_ticket_capability(request.user, tenant, 'ticket.internal_note'):
            return Response({'detail': 'No permission for internal notes.'}, status=403)
        msg = add_reply(
            ticket, request.user, d['body'],
            is_internal=is_internal,
            body_html=d.get('body_html', ''),
        )
        return Response({'id': str(msg.id)}, status=201)

    # -- upload attachment --
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None):
        ticket = get_object_or_404(self._qs(request), pk=pk)
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'file is required'}, status=400)
        MAX_SIZE = 20 * 1024 * 1024
        if f.size > MAX_SIZE:
            return Response({'detail': 'File too large (max 20 MB).'}, status=400)
        att = TicketAttachment.objects.create(
            ticket=ticket,
            file=f,
            original_filename=f.name[:255],
            content_type=f.content_type or '',
            size_bytes=f.size,
            uploaded_by=request.user,
        )
        return Response(TicketAttachmentSerializer(att).data, status=201)

    # -- CSAT --
    @action(detail=True, methods=['post'])
    def csat(self, request, pk=None):
        ticket = get_object_or_404(self._qs(request), pk=pk)
        if ticket.status not in ('resolved', 'closed'):
            return Response({'detail': 'CSAT can only be submitted for resolved/closed tickets.'}, status=400)
        if hasattr(ticket, 'csat') and ticket.csat:
            return Response({'detail': 'CSAT already submitted.'}, status=400)
        ser = TicketCsatSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        csat = TicketCsatRating.objects.create(
            ticket=ticket,
            score=ser.validated_data['score'],
            comment=ser.validated_data.get('comment', ''),
            submitted_by=request.user,
        )
        return Response(TicketCsatSerializer(csat).data, status=201)


# ===================================================================
# Platform / super-admin API
# ===================================================================

class PlatformTicketViewSet(viewsets.ViewSet):
    """Cross-tenant ticket queue for platform operators."""

    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]

    def _base_qs(self):
        return Ticket.objects.filter(is_deleted=False).select_related(
            'tenant', 'requester', 'assignee', 'queue', 'registry_installation',
        )

    # -- create on behalf of a user --
    def create(self, request):
        ser = PlatformTicketCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        from saas_platform.models import Tenant
        tenant = get_object_or_404(Tenant, pk=d['tenant_id'])
        requester = get_object_or_404(User, pk=d['requester_id'])
        ticket = create_ticket(
            tenant=tenant,
            requester=requester,
            subject=d['subject'],
            body=d['body'],
            priority=d.get('priority', 'medium'),
            category=d.get('category', ''),
            language=d.get('language', 'en'),
            client_version=d.get('client_version', ''),
            deployment_context=d.get('deployment_context', ''),
        )
        return Response(
            TicketDetailSerializer(ticket, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    # -- list users for assignment / ticket creation --
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Search users across tenants for the super-admin create/assign flows."""
        search = request.query_params.get('search', '').strip()
        tenant_id = request.query_params.get('tenant_id')
        qs = User.objects.filter(is_active=True).order_by('email')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if search:
            qs = qs.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search) | Q(username__icontains=search)
            )
        qs = qs[:50]
        return Response([
            {
                'id': u.id,
                'email': u.email,
                'name': u.full_name or u.username,
                'role': u.role,
                'tenant_id': str(u.tenant_id) if u.tenant_id else None,
                'tenant_name': u.tenant.name if u.tenant else None,
            }
            for u in qs.select_related('tenant')
        ])

    # -- list tenants for ticket creation --
    @action(detail=False, methods=['get'])
    def tenants(self, request):
        """List tenants for the create-ticket dropdown."""
        from saas_platform.models import Tenant
        search = request.query_params.get('search', '').strip()
        qs = Tenant.objects.all().order_by('name')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))
        qs = qs[:50]
        return Response([
            {'id': str(t.id), 'name': t.name, 'slug': t.slug}
            for t in qs
        ])

    # -- queue list with filters --
    def list(self, request):
        qs = self._base_qs()
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        st = request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)
        pri = request.query_params.get('priority')
        if pri:
            qs = qs.filter(priority=pri)
        assignee_id = request.query_params.get('assignee_id')
        if assignee_id:
            qs = qs.filter(assignee_id=assignee_id)
        queue_id = request.query_params.get('queue_id')
        if queue_id:
            qs = qs.filter(queue_id=queue_id)
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(subject__icontains=search) | Q(number__icontains=search)
            )
        qs = qs[:200]
        return Response(PlatformTicketListSerializer(qs, many=True).data)

    # -- detail --
    def retrieve(self, request, pk=None):
        ticket = get_object_or_404(self._base_qs(), pk=pk)
        return Response(TicketDetailSerializer(ticket, context={'request': request}).data)

    # -- assign --
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        ticket = get_object_or_404(self._base_qs(), pk=pk)
        ser = TicketAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        assignee = get_object_or_404(User, pk=ser.validated_data['assignee_id'])
        ticket = assign_ticket(ticket, assignee, request.user)
        return Response(TicketDetailSerializer(ticket, context={'request': request}).data)

    # -- transition --
    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        ticket = get_object_or_404(self._base_qs(), pk=pk)
        ser = TicketTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        act = ser.validated_data['action']
        reason = ser.validated_data.get('reason', '')
        dispatch = {
            'start_progress': start_progress,
            'pend': pend_ticket,
            'resolve': resolve_ticket,
            'close': close_ticket,
            'reopen': reopen_ticket,
            'escalate': escalate_ticket,
        }
        fn = dispatch.get(act)
        if not fn:
            return Response({'detail': f'Unknown action: {act}'}, status=400)
        try:
            if act in ('pend', 'resolve', 'close', 'reopen', 'escalate'):
                ticket = fn(ticket, request.user, reason=reason)
            else:
                ticket = fn(ticket, request.user)
        except TicketTransitionError as e:
            return Response({'detail': str(e)}, status=400)
        return Response(TicketDetailSerializer(ticket, context={'request': request}).data)

    # -- reply (including internal notes) --
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = get_object_or_404(self._base_qs(), pk=pk)
        ser = TicketReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        msg = add_reply(
            ticket, request.user, d['body'],
            is_internal=d.get('is_internal', False),
            body_html=d.get('body_html', ''),
        )
        return Response({'id': str(msg.id)}, status=201)

    # -- merge --
    @action(detail=True, methods=['post'])
    def merge(self, request, pk=None):
        source = get_object_or_404(self._base_qs(), pk=pk)
        ser = TicketMergeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target = get_object_or_404(Ticket, pk=ser.validated_data['target_ticket_id'])
        try:
            target = merge_tickets(source, target, request.user)
        except TicketTransitionError as e:
            return Response({'detail': str(e)}, status=400)
        return Response(TicketDetailSerializer(target, context={'request': request}).data)

    # -- upload attachment --
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None):
        ticket = get_object_or_404(self._base_qs(), pk=pk)
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'file is required'}, status=400)
        att = TicketAttachment.objects.create(
            ticket=ticket,
            file=f,
            original_filename=f.name[:255],
            content_type=f.content_type or '',
            size_bytes=f.size,
            uploaded_by=request.user,
        )
        return Response(TicketAttachmentSerializer(att).data, status=201)


# ===================================================================
# Platform settings CRUD
# ===================================================================

class PlatformQueueViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]
    serializer_class = TicketQueueSerializer

    def get_queryset(self):
        qs = TicketQueue.objects.all()
        tid = self.request.query_params.get('tenant_id')
        if tid:
            qs = qs.filter(tenant_id=tid)
        return qs

    def perform_create(self, serializer):
        tid = self.request.data.get('tenant_id')
        serializer.save(tenant_id=tid)


class PlatformSlaPolicyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]
    serializer_class = TicketSlaPolicySerializer

    def get_queryset(self):
        qs = TicketSlaPolicy.objects.all()
        tid = self.request.query_params.get('tenant_id')
        if tid:
            qs = qs.filter(tenant_id=tid)
        return qs

    def perform_create(self, serializer):
        tid = self.request.data.get('tenant_id')
        serializer.save(tenant_id=tid)


class PlatformRoutingRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]
    serializer_class = TicketRoutingRuleSerializer

    def get_queryset(self):
        qs = TicketRoutingRule.objects.select_related('queue').all()
        tid = self.request.query_params.get('tenant_id')
        if tid:
            qs = qs.filter(tenant_id=tid)
        return qs

    def perform_create(self, serializer):
        tid = self.request.data.get('tenant_id')
        serializer.save(tenant_id=tid)


class PlatformCannedResponseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]
    serializer_class = TicketCannedResponseSerializer

    def get_queryset(self):
        qs = TicketCannedResponse.objects.all()
        tid = self.request.query_params.get('tenant_id')
        if tid:
            qs = qs.filter(tenant_id=tid)
        return qs

    def perform_create(self, serializer):
        tid = self.request.data.get('tenant_id')
        serializer.save(tenant_id=tid, created_by=self.request.user)


class PlatformTagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]
    serializer_class = TicketTagSerializer

    def get_queryset(self):
        qs = TicketTag.objects.all()
        tid = self.request.query_params.get('tenant_id')
        if tid:
            qs = qs.filter(tenant_id=tid)
        return qs

    def perform_create(self, serializer):
        tid = self.request.data.get('tenant_id')
        serializer.save(tenant_id=tid)


class PlatformRoleProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformTicketAdmin]
    serializer_class = TicketRoleProfileSerializer

    def get_queryset(self):
        qs = TicketRoleProfile.objects.select_related('user').all()
        tid = self.request.query_params.get('tenant_id')
        if tid:
            qs = qs.filter(tenant_id=tid)
        return qs

    def perform_create(self, serializer):
        tid = self.request.data.get('tenant_id')
        serializer.save(tenant_id=tid)
