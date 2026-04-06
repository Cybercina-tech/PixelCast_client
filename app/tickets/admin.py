from django.contrib import admin
from .models import (
    Ticket, TicketMessage, TicketAttachment, TicketRelation,
    TicketAuditEvent, TicketQueue, TicketSlaPolicy, TicketSlaSnapshot,
    TicketRoleProfile, TicketCannedResponse, TicketTag, TicketCsatRating,
    TicketRoutingRule,
)

admin.site.register(Ticket)
admin.site.register(TicketMessage)
admin.site.register(TicketAttachment)
admin.site.register(TicketRelation)
admin.site.register(TicketAuditEvent)
admin.site.register(TicketQueue)
admin.site.register(TicketSlaPolicy)
admin.site.register(TicketSlaSnapshot)
admin.site.register(TicketRoleProfile)
admin.site.register(TicketCannedResponse)
admin.site.register(TicketTag)
admin.site.register(TicketCsatRating)
admin.site.register(TicketRoutingRule)
