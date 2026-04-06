"""
Helpdesk ticket domain models.

Multi-tenant SaaS ticketing with full lifecycle, SLA, queues,
conversation threads, attachments, CSAT, and audit trail.
"""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


# ---------------------------------------------------------------------------
# Queues & SLA policies (configured per-tenant)
# ---------------------------------------------------------------------------

class TicketQueue(models.Model):
    """Work queue that tickets are routed into (e.g. 'Billing', 'Technical')."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='ticket_queues',
    )
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=80)
    description = models.TextField(blank=True, default='')
    is_default = models.BooleanField(
        default=False, help_text='Auto-selected when no routing rule matches',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [('tenant', 'slug')]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return self.name


class TicketSlaPolicy(models.Model):
    """Service-level agreement definition scoped to a tenant."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='ticket_sla_policies',
    )
    name = models.CharField(max_length=128)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, db_index=True)
    first_response_minutes = models.PositiveIntegerField(
        help_text='Maximum minutes until first agent response',
    )
    resolution_minutes = models.PositiveIntegerField(
        help_text='Maximum minutes until ticket is resolved',
    )
    warning_threshold_pct = models.PositiveSmallIntegerField(
        default=80,
        help_text='Percentage of SLA time that triggers a warning (0-100)',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tenant', 'priority']
        unique_together = [('tenant', 'priority')]

    def __str__(self):
        return f'{self.name} ({self.get_priority_display()})'


# ---------------------------------------------------------------------------
# Core ticket
# ---------------------------------------------------------------------------

class Ticket(models.Model):
    """Primary helpdesk ticket."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    SOURCE_CHOICES = [
        ('web', 'Web'),
        ('email', 'Email'),
        ('api', 'API'),
        ('chat', 'Chat'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='tickets',
    )
    number = models.PositiveIntegerField(
        db_index=True,
        help_text='Human-readable ticket number, auto-incremented per tenant',
    )

    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='open', db_index=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default='web')

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='requested_tickets',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets',
    )
    queue = models.ForeignKey(
        TicketQueue, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets',
    )
    sla_policy = models.ForeignKey(
        TicketSlaPolicy, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets',
    )

    category = models.CharField(max_length=128, blank=True, default='')
    language = models.CharField(max_length=8, blank=True, default='en')
    client_version = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        help_text='Optional app version reported on the ticket (for support correlation)',
    )
    deployment_context = models.CharField(
        max_length=32,
        blank=True,
        default='',
        db_index=True,
        help_text='Optional: saas | self_hosted — how the customer runs the product',
    )

    first_response_due_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    first_responded_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    merged_into = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='merged_children',
    )
    is_deleted = models.BooleanField(default=False)

    registry_installation = models.ForeignKey(
        'licensing.LicenseRegistryInstallation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bridged_tickets',
        help_text='Operator registry row when this ticket was ingested from a self-hosted site',
    )
    remote_ticket_id = models.UUIDField(
        null=True,
        blank=True,
        help_text='Ticket UUID on the self-hosted instance (idempotency / replies)',
    )
    bridge_requester_name = models.CharField(max_length=255, blank=True, default='')
    bridge_requester_email = models.CharField(max_length=254, blank=True, default='')
    suppress_operator_bridge_outbound = models.BooleanField(
        default=False,
        help_text='When true, do not push this ticket or its customer replies to the operator bridge (avoids loops).',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('tenant', 'number')]
        constraints = [
            models.UniqueConstraint(
                fields=['registry_installation', 'remote_ticket_id'],
                condition=Q(registry_installation__isnull=False, remote_ticket_id__isnull=False),
                name='tickets_ticket_registry_install_remote_uid',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'assignee']),
            models.Index(fields=['tenant', 'priority']),
            models.Index(fields=['tenant', 'queue']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'first_response_due_at']),
            models.Index(fields=['tenant', 'resolution_due_at']),
            models.Index(fields=['requester', 'status']),
        ]

    def __str__(self):
        return f'#{self.number} {self.subject[:60]}'

    def save(self, *args, **kwargs):
        if not self.number:
            last = (
                Ticket.objects
                .filter(tenant=self.tenant)
                .order_by('-number')
                .values_list('number', flat=True)
                .first()
            )
            self.number = (last or 0) + 1
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Conversation & attachments
# ---------------------------------------------------------------------------

class TicketMessage(models.Model):
    """A message in the ticket conversation thread."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='ticket_messages',
    )
    body = models.TextField()
    body_html = models.TextField(blank=True, default='')
    is_internal = models.BooleanField(
        default=False, help_text='Internal notes visible only to agents',
    )
    source = models.CharField(max_length=16, choices=Ticket.SOURCE_CHOICES, default='web')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]

    def __str__(self):
        kind = 'note' if self.is_internal else 'reply'
        return f'[{kind}] {self.body[:60]}'


class TicketAttachment(models.Model):
    """File attached to a ticket or a specific message."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    message = models.ForeignKey(
        TicketMessage, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='attachments',
    )
    file = models.FileField(upload_to='tickets/attachments/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=128, blank=True, default='')
    size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.original_filename


# ---------------------------------------------------------------------------
# Relations (merge / link / split / parent-child)
# ---------------------------------------------------------------------------

class TicketRelation(models.Model):
    """Directed relationship between two tickets."""

    RELATION_TYPES = [
        ('merged_from', 'Merged From'),
        ('linked', 'Linked'),
        ('split_from', 'Split From'),
        ('parent', 'Parent'),
        ('child', 'Child'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='outgoing_relations')
    target = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='incoming_relations')
    relation_type = models.CharField(max_length=16, choices=RELATION_TYPES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('source', 'target', 'relation_type')]

    def __str__(self):
        return f'{self.source} --[{self.relation_type}]--> {self.target}'


# ---------------------------------------------------------------------------
# SLA tracking
# ---------------------------------------------------------------------------

class TicketSlaSnapshot(models.Model):
    """Point-in-time SLA state for a ticket."""

    SLA_METRIC_CHOICES = [
        ('first_response', 'First Response'),
        ('resolution', 'Resolution'),
    ]

    SLA_STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('warning', 'Warning'),
        ('breached', 'Breached'),
        ('achieved', 'Achieved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='sla_snapshots')
    metric = models.CharField(max_length=20, choices=SLA_METRIC_CHOICES)
    status = models.CharField(max_length=16, choices=SLA_STATUS_CHOICES, default='on_track')
    target_at = models.DateTimeField(help_text='Deadline for this SLA metric')
    achieved_at = models.DateTimeField(null=True, blank=True)
    breached_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('ticket', 'metric')]
        indexes = [
            models.Index(fields=['status', 'target_at']),
        ]

    def __str__(self):
        return f'{self.ticket} SLA:{self.metric} [{self.status}]'


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

class TicketAuditEvent(models.Model):
    """Immutable record of every state change on a ticket."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='audit_events')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True,
    )
    action = models.CharField(max_length=64, db_index=True)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]

    def __str__(self):
        return f'{self.action} on {self.ticket}'


# ---------------------------------------------------------------------------
# Role profiles (ticket-scope RBAC)
# ---------------------------------------------------------------------------

class TicketRoleProfile(models.Model):
    """
    Per-user ticket role grant within a tenant.

    Separates helpdesk roles from the global product role on User.
    A user can be an Employee in the product but an 'agent' in the ticket system.
    """

    TICKET_ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='ticket_role_profiles',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ticket_role_profiles',
    )
    role = models.CharField(max_length=16, choices=TICKET_ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('tenant', 'user')]
        indexes = [
            models.Index(fields=['tenant', 'role', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user} [{self.role}] @ {self.tenant}'


# ---------------------------------------------------------------------------
# Canned responses & tags
# ---------------------------------------------------------------------------

class TicketCannedResponse(models.Model):
    """Pre-written reply template for agents."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='ticket_canned_responses',
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    body_html = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class TicketTag(models.Model):
    """Tenant-scoped label/tag for tickets."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='ticket_tags',
    )
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=7, default='#6366f1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('tenant', 'name')]
        ordering = ['name']

    def __str__(self):
        return self.name


class TicketTagging(models.Model):
    """M2M through table for ticket<->tag."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='taggings')
    tag = models.ForeignKey(TicketTag, on_delete=models.CASCADE, related_name='taggings')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('ticket', 'tag')]


# ---------------------------------------------------------------------------
# CSAT
# ---------------------------------------------------------------------------

class TicketCsatRating(models.Model):
    """Customer satisfaction rating submitted after resolution."""

    SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='csat')
    score = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    comment = models.TextField(blank=True, default='')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'CSAT {self.score}/5 for {self.ticket}'


# ---------------------------------------------------------------------------
# Assignment / routing rules
# ---------------------------------------------------------------------------

class TicketRoutingRule(models.Model):
    """Configurable auto-assignment rule for a tenant queue."""

    STRATEGY_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('least_busy', 'Least Busy'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'saas_platform.Tenant', on_delete=models.CASCADE,
        related_name='ticket_routing_rules',
    )
    queue = models.ForeignKey(
        TicketQueue, on_delete=models.CASCADE,
        related_name='routing_rules',
    )
    strategy = models.CharField(max_length=16, choices=STRATEGY_CHOICES, default='round_robin')
    conditions = models.JSONField(
        default=dict, blank=True,
        help_text='Match criteria: priority, category, language, tags, etc.',
    )
    is_active = models.BooleanField(default=True)
    priority_order = models.PositiveSmallIntegerField(
        default=0, help_text='Lower number = higher precedence',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority_order']
        indexes = [
            models.Index(fields=['tenant', 'is_active', 'priority_order']),
        ]

    def __str__(self):
        return f'{self.queue.name} [{self.strategy}]'
