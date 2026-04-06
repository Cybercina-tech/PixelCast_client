"""
JSON Error Response Middleware

Ensures all API errors return JSON responses instead of HTML.
This is critical for enterprise-grade error handling.
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

NON_FIELD_KEYS = {'non_field_errors', '__all__'}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _normalize_error_payload(data):
    """
    Normalize DRF/custom error payloads to a stable API contract.
    """
    data = data if isinstance(data, dict) else {}
    field_errors = {}

    for key, value in data.items():
        if key in ('status', 'error', 'message', 'detail', 'details', 'field_errors'):
            continue
        if isinstance(value, (list, str)):
            field_errors[key] = _as_list(value)

    # Merge explicit field_errors/errors map if provided.
    explicit = data.get('field_errors') or data.get('errors')
    if isinstance(explicit, dict):
        for key, value in explicit.items():
            field_errors[key] = _as_list(value)

    # Promote non-field keys into message candidate list.
    non_field_messages = []
    for key in NON_FIELD_KEYS:
        if key in data:
            non_field_messages.extend(_as_list(data.get(key)))
            field_errors.pop(key, None)

    detail = data.get('detail')
    message = data.get('message')
    error = data.get('error')
    if isinstance(detail, list):
        detail = detail[0] if detail else None
    if isinstance(error, list):
        error = error[0] if error else None
    if isinstance(message, list):
        message = message[0] if message else None

    final_message = (
        message
        or detail
        or (non_field_messages[0] if non_field_messages else None)
        or (next(iter(field_errors.values()))[0] if field_errors else None)
        or 'An error occurred'
    )

    return {
        'status': 'error',
        'error': str(error or 'validation_error'),
        'message': str(final_message),
        'field_errors': field_errors,
        'details': data,
    }


class JSONErrorResponseMiddleware(MiddlewareMixin):
    """
    Middleware to ensure all API errors return JSON responses.
    
    This middleware catches exceptions and converts them to JSON responses
    with a consistent format:
    {
        "error": "error_code",
        "message": "Human-readable message",
        "details": {}
    }
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions and return JSON responses for API requests.
        """
        # Only handle API requests (those starting with /api/)
        if not request.path.startswith('/api/'):
            return None  # Let Django handle non-API errors normally
        
        # Handle DRF exceptions
        if isinstance(exception, APIException):
            detail = exception.detail if hasattr(exception, 'detail') else {}
            payload = _normalize_error_payload(
                detail if isinstance(detail, dict) else {'detail': detail}
            )
            payload['error'] = str(
                exception.get_codes() if hasattr(exception, 'get_codes') else payload['error']
            )
            return JsonResponse(payload, status=exception.status_code)
        
        # Handle other exceptions
        error_code = type(exception).__name__
        error_message = str(exception)
        
        # Log the error with context
        logger.error(
            f"API Error: {error_code} - {error_message}",
            exc_info=True,
            extra={
                'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                'endpoint': request.path,
                'method': request.method,
                'organization': getattr(request.user, 'organization', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                'action_type': 'api_error',
            }
        )
        
        # Return JSON error response
        return JsonResponse({
            'status': 'error',
            'error': error_code.lower().replace('exception', ''),
            'message': error_message or 'An unexpected error occurred',
            'field_errors': {},
            'details': {},
        }, status=500)


def drf_exception_handler(exc, context):
    """
    Custom DRF exception handler that ensures JSON responses.
    
    This is used by DRF's EXCEPTION_HANDLER setting.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Ensure response is JSON
        if hasattr(response, 'data'):
            response.data = _normalize_error_payload(response.data)
    
    return response

