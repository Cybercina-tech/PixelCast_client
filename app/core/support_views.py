"""In-app support tickets."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SupportTicket


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def support_tickets(request):
    if request.method == 'GET':
        qs = SupportTicket.objects.filter(user=request.user)[:50]
        return Response(
            {
                'tickets': [
                    {
                        'id': str(t.id),
                        'subject': t.subject,
                        'status': t.status,
                        'created_at': t.created_at.isoformat(),
                    }
                    for t in qs
                ]
            }
        )

    subject = (request.data.get('subject') or '').strip()[:255]
    body = (request.data.get('body') or '').strip()
    if not subject or not body:
        return Response({'detail': 'subject and body required'}, status=status.HTTP_400_BAD_REQUEST)
    t = SupportTicket.objects.create(user=request.user, subject=subject, body=body)
    return Response({'id': str(t.id), 'status': t.status}, status=status.HTTP_201_CREATED)
