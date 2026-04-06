"""
Device authentication utilities for screen/player endpoints.

All runtime IoT traffic (heartbeat, template fetch, command pull/response)
must present a valid ``X-Device-Token`` header alongside ``screen_id``.
"""
import logging
from django.http import JsonResponse
from .models import Screen

logger = logging.getLogger(__name__)

DEVICE_TOKEN_HEADER = 'HTTP_X_DEVICE_TOKEN'


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def authenticate_device_request(request):
    """
    Extract ``screen_id`` and device token from the request and verify them.

    The device token is read from the ``X-Device-Token`` header.
    ``screen_id`` comes from query params (GET) or body (POST).

    Returns:
        (Screen, None) on success.
        (None, JsonResponse) on failure — caller should return the response.
    """
    # --- extract screen_id ---
    screen_id = (
        request.GET.get('screen_id')
        or (request.data.get('screen_id') if hasattr(request, 'data') and isinstance(request.data, dict) else None)
    )
    if not screen_id:
        return None, _error_response('screen_id is required', 400)

    # --- extract device token ---
    raw_token = request.META.get(DEVICE_TOKEN_HEADER)
    if not raw_token:
        return None, _error_response(
            'Device token is required. Send X-Device-Token header.', 401,
        )

    # --- authenticate ---
    screen = Screen.authenticate_device(screen_id, raw_token)
    if screen is None:
        ip = _get_client_ip(request)
        logger.warning(
            'Device auth failed for screen_id=%s from IP=%s', screen_id, ip,
        )
        return None, _error_response('Invalid screen_id or device token', 401)

    return screen, None


def _error_response(message, status_code):
    resp = JsonResponse({'error': message}, status=status_code)
    resp['Access-Control-Allow-Origin'] = '*'
    resp['Access-Control-Allow-Headers'] = 'Content-Type, X-Device-Token'
    return resp
