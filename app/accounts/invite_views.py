"""Team invitations."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from core.email_service import send_system_email

from .models import User, UserInvitation


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def team_invitations(request):
    if not getattr(settings, 'PLATFORM_SAAS_ENABLED', False):
        return Response({'detail': 'SaaS not enabled.'}, status=403)
    tenant = getattr(request.user, 'tenant', None)
    if not tenant:
        return Response({'detail': 'No tenant.'}, status=400)
    if not (request.user.is_developer() or request.user.is_manager()):
        return Response({'detail': 'Forbidden.'}, status=403)

    if request.method == 'GET':
        qs = UserInvitation.objects.filter(tenant=tenant, accepted_at__isnull=True)[:100]
        return Response(
            {
                'invitations': [
                    {
                        'id': str(i.id),
                        'email': i.email,
                        'role': i.role,
                        'expires_at': i.expires_at.isoformat(),
                    }
                    for i in qs
                ]
            }
        )

    email = (request.data.get('email') or '').strip().lower()
    role = (request.data.get('role') or 'Employee').strip()
    if not email:
        return Response({'detail': 'email required'}, status=400)
    if role not in ('Employee', 'Visitor') and not request.user.is_developer():
        role = 'Employee'

    inv = UserInvitation.objects.create(
        email=email,
        role=role,
        tenant=tenant,
        invited_by=request.user,
    )
    base = getattr(settings, 'PUBLIC_WEB_APP_URL', 'http://localhost:5173').rstrip('/')
    link = f'{base}/signup?invite={inv.token}'
    try:
        send_system_email(
            subject='You are invited to PixelCast',
            message=f'Accept your invitation:\n{link}\n',
            recipient_list=[email],
        )
    except Exception:
        pass

    return Response({'id': str(inv.id), 'token': inv.token, 'invite_url': link}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def accept_invitation(request):
    token = (request.data.get('token') or '').strip()
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    if not token or not password:
        return Response({'detail': 'token and password required'}, status=400)
    inv = UserInvitation.objects.filter(token=token).first()
    if not inv or not inv.is_valid():
        return Response({'detail': 'Invalid or expired invitation.'}, status=400)
    if User.objects.filter(email__iexact=inv.email).exists():
        return Response({'detail': 'An account with this email already exists.'}, status=400)

    user = User.objects.create_user(
        username=username or inv.email.split('@')[0],
        email=inv.email,
        password=password,
        role=inv.role,
        tenant=inv.tenant,
        organization_name=inv.tenant.organization_name_key or '',
    )
    inv.accepted_at = timezone.now()
    inv.save(update_fields=['accepted_at'])
    return Response({'status': 'ok', 'user_id': str(user.id)})
