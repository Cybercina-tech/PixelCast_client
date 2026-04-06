"""
API for system-wide email (SMTP) configuration — Developer only.
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone

from core.email_errors import classify_email_send_error
from core.email_service import resolve_default_from_email, send_system_email
from core.models import SystemEmailSettings
from core.serializers import SystemEmailSettingsSerializer, SystemEmailTestSerializer
from core.audit import AuditLogger
from core.permissions import IsDeveloperPlatformAccess

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Core Infrastructure'],
    summary='Get system email settings',
    description='Returns SMTP configuration (password never exposed). Developer only.',
)
class SystemEmailSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsDeveloperPlatformAccess]

    def get(self, request):
        obj = SystemEmailSettings.get_solo()
        return Response(SystemEmailSettingsSerializer(obj).data)

    @extend_schema(
        summary='Update system email settings',
        request=SystemEmailSettingsSerializer,
    )
    def patch(self, request):
        obj = SystemEmailSettings.get_solo()
        ser = SystemEmailSettingsSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        try:
            AuditLogger.log_action(
                action_type='update',
                user=request.user,
                resource=obj,
                description='System email (SMTP) settings updated',
                request=request,
            )
        except Exception as e:
            logger.warning('Audit log failed for system email settings: %s', e)
        return Response(SystemEmailSettingsSerializer(obj).data)


@extend_schema(
    tags=['Core Infrastructure'],
    summary='Send test email',
    description='Sends a test message using the current system email configuration.',
    request=SystemEmailTestSerializer,
)
class SystemEmailTestView(APIView):
    permission_classes = [IsAuthenticated, IsDeveloperPlatformAccess]

    def post(self, request):
        ser = SystemEmailTestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        to = ser.validated_data['to']
        subject = 'PixelCast Signage — Email test'
        body = (
            'This is a test message from your PixelCast Signage system email configuration.\n\n'
            'If you received this, SMTP settings are working correctly.'
        )
        solo = SystemEmailSettings.get_solo()
        try:
            send_system_email(
                subject=subject,
                message=body,
                recipient_list=[to],
                from_email=resolve_default_from_email(),
            )
        except Exception as e:
            logger.exception('System email test failed')
            code, safe_msg = classify_email_send_error(e)
            solo.last_smtp_test_at = timezone.now()
            solo.last_smtp_test_ok = False
            solo.last_smtp_test_error_code = code
            solo.last_smtp_test_detail = safe_msg[:2000]
            solo.save(
                update_fields=[
                    'last_smtp_test_at',
                    'last_smtp_test_ok',
                    'last_smtp_test_error_code',
                    'last_smtp_test_detail',
                    'updated_at',
                ]
            )
            return Response(
                {
                    'success': False,
                    'error_code': code,
                    'detail': safe_msg,
                    'message': safe_msg,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        solo.last_smtp_test_at = timezone.now()
        solo.last_smtp_test_ok = True
        solo.last_smtp_test_error_code = ''
        solo.last_smtp_test_detail = ''
        solo.save(
            update_fields=[
                'last_smtp_test_at',
                'last_smtp_test_ok',
                'last_smtp_test_error_code',
                'last_smtp_test_detail',
                'updated_at',
            ]
        )
        return Response(
            {
                'success': True,
                'message': f'Test email sent to {to}.',
                'error_code': None,
            }
        )
