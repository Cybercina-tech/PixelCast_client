"""Ticket DRF serializers for requester and platform APIs."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    Ticket, TicketAttachment, TicketAuditEvent, TicketCannedResponse,
    TicketCsatRating, TicketMessage, TicketQueue, TicketRelation,
    TicketRoleProfile, TicketRoutingRule, TicketSlaPolicy,
    TicketSlaSnapshot, TicketTag, TicketTagging,
)


class TicketPriorityField(serializers.ChoiceField):
    """Accepts API codes plus UI aliases: normal→medium, urgent→critical."""

    def __init__(self, **kwargs):
        kwargs.setdefault('choices', Ticket.PRIORITY_CHOICES)
        kwargs.setdefault('default', 'medium')
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str):
            key = data.strip().lower()
            if key == 'normal':
                data = 'medium'
            elif key == 'urgent':
                data = 'critical'
        return super().to_internal_value(data)


# ---------------------------------------------------------------
# Shared / nested
# ---------------------------------------------------------------

class TicketMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = [
            'id', 'ticket', 'author', 'author_name', 'body', 'body_html',
            'is_internal', 'source', 'created_at',
        ]
        read_only_fields = ['id', 'author', 'author_name', 'ticket', 'created_at']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.full_name or obj.author.username
        return None


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = [
            'id', 'ticket', 'message', 'file', 'original_filename',
            'content_type', 'size_bytes', 'uploaded_by', 'created_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'size_bytes', 'content_type', 'created_at']


class TicketSlaSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSlaSnapshot
        fields = ['id', 'metric', 'status', 'target_at', 'achieved_at', 'breached_at']
        read_only_fields = fields


class TicketAuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketAuditEvent
        fields = ['id', 'actor', 'actor_name', 'action', 'changes', 'created_at']
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.full_name or obj.actor.username
        return None


class TicketRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketRelation
        fields = ['id', 'source', 'target', 'relation_type', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class TicketTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTag
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']


class TicketCsatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCsatRating
        fields = ['id', 'ticket', 'score', 'comment', 'submitted_by', 'created_at']
        read_only_fields = ['id', 'submitted_by', 'ticket', 'created_at']


# ---------------------------------------------------------------
# Requester-facing ticket
# ---------------------------------------------------------------

class TicketListSerializer(serializers.ModelSerializer):
    requester_name = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'number', 'subject', 'status', 'priority', 'source',
            'requester', 'requester_name', 'assignee', 'assignee_name',
            'category', 'client_version', 'deployment_context',
            'created_at', 'updated_at', 'last_message_at',
            'first_response_due_at', 'resolution_due_at', 'tags',
        ]
        read_only_fields = fields

    def get_requester_name(self, obj):
        if obj.requester:
            return obj.requester.full_name or obj.requester.username
        if getattr(obj, 'registry_installation_id', None) and (
            (obj.bridge_requester_name or '').strip() or (obj.bridge_requester_email or '').strip()
        ):
            name = (obj.bridge_requester_name or '').strip()
            em = (obj.bridge_requester_email or '').strip()
            if name and em:
                return f'{name} <{em}>'
            return name or em or None
        return None

    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.full_name or obj.assignee.username
        return None

    def get_tags(self, obj):
        return list(
            obj.taggings.select_related('tag').values_list('tag__name', flat=True)
        )


class TicketDetailSerializer(TicketListSerializer):
    messages = serializers.SerializerMethodField()
    sla_snapshots = TicketSlaSnapshotSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    csat = TicketCsatSerializer(read_only=True)

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + [
            'resolved_at', 'closed_at', 'merged_into', 'language',
            'messages', 'sla_snapshots', 'attachments', 'csat',
        ]

    def get_messages(self, obj):
        request = self.context.get('request')
        qs = obj.messages.select_related('author').all()
        if request and not self._is_staff(request.user, obj.tenant):
            qs = qs.filter(is_internal=False)
        return TicketMessageSerializer(qs, many=True).data

    @staticmethod
    def _is_staff(user, tenant):
        if user.is_superuser or getattr(user, 'role', '') == 'Developer':
            return True
        from .permissions import get_ticket_role
        return get_ticket_role(user, tenant) in ('agent', 'supervisor', 'admin')


class TicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    priority = TicketPriorityField()
    category = serializers.CharField(max_length=128, required=False, default='')
    language = serializers.CharField(max_length=8, required=False, default='en')


class PlatformTicketCreateSerializer(serializers.Serializer):
    """Super-admin creates a ticket on behalf of any tenant user."""
    tenant_id = serializers.UUIDField()
    requester_id = serializers.IntegerField()
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    priority = TicketPriorityField()
    category = serializers.CharField(max_length=128, required=False, default='')
    language = serializers.CharField(max_length=8, required=False, default='en')
    client_version = serializers.CharField(max_length=64, required=False, default='')
    deployment_context = serializers.CharField(max_length=32, required=False, default='')


class TicketReplySerializer(serializers.Serializer):
    body = serializers.CharField()
    body_html = serializers.CharField(required=False, default='')
    is_internal = serializers.BooleanField(required=False, default=False)


# ---------------------------------------------------------------
# Platform / super-admin
# ---------------------------------------------------------------

class PlatformTicketListSerializer(TicketListSerializer):
    tenant_name = serializers.SerializerMethodField()
    registry_install_domain = serializers.SerializerMethodField()

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + ['tenant_name', 'queue', 'registry_install_domain']

    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None

    def get_registry_install_domain(self, obj):
        inst = getattr(obj, 'registry_installation', None)
        if inst is not None:
            return inst.domain or ''
        return ''


class TicketAssignSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField()


class TicketTransitionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[
        'start_progress', 'pend', 'resolve', 'close', 'reopen', 'escalate',
    ])
    reason = serializers.CharField(required=False, default='')


class TicketMergeSerializer(serializers.Serializer):
    target_ticket_id = serializers.UUIDField()


# ---------------------------------------------------------------
# Settings objects
# ---------------------------------------------------------------

class TicketQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketQueue
        fields = ['id', 'name', 'slug', 'description', 'is_default', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class TicketSlaPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSlaPolicy
        fields = [
            'id', 'name', 'priority', 'first_response_minutes',
            'resolution_minutes', 'warning_threshold_pct', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_priority(self, value):
        if value in (None, ''):
            return value
        key = str(value).strip().lower()
        if key == 'normal':
            value = 'medium'
        elif key == 'urgent':
            value = 'critical'
        else:
            value = key
        allowed = {c[0] for c in TicketSlaPolicy.PRIORITY_CHOICES}
        if value not in allowed:
            raise serializers.ValidationError(
                f'"{value}" is not a valid choice.',
            )
        return value


class TicketRoutingRuleSerializer(serializers.ModelSerializer):
    queue_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketRoutingRule
        fields = [
            'id', 'queue', 'queue_name', 'strategy', 'conditions',
            'is_active', 'priority_order', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_queue_name(self, obj):
        return obj.queue.name if obj.queue else None


class TicketCannedResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCannedResponse
        fields = ['id', 'title', 'body', 'body_html', 'is_active', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class TicketRoleProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketRoleProfile
        fields = ['id', 'user', 'user_email', 'user_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.full_name or obj.user.username
        return None
