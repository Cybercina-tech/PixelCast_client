from rest_framework import status
from rest_framework.response import Response


RESERVED_KEYS = {
    'status', 'error', 'message', 'detail', 'details', 'field_errors',
    'errors', 'non_field_errors', '__all__', 'code',
}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def normalize_error_payload(data, default_message='An error occurred', default_code='validation_error'):
    raw = data if isinstance(data, dict) else {'detail': data}
    field_errors = {}

    explicit = raw.get('field_errors') or raw.get('errors')
    if isinstance(explicit, dict):
        for key, value in explicit.items():
            field_errors[key] = _as_list(value)

    for key, value in raw.items():
        if key in RESERVED_KEYS:
            continue
        if isinstance(value, (list, str)):
            field_errors[key] = _as_list(value)

    non_field = _as_list(raw.get('non_field_errors')) + _as_list(raw.get('__all__'))
    message = raw.get('message') or raw.get('detail') or raw.get('error')
    if isinstance(message, list):
        message = message[0] if message else None

    if not message:
        if non_field:
            message = non_field[0]
        elif field_errors:
            message = next(iter(field_errors.values()))[0]
        else:
            message = default_message

    return {
        'status': 'error',
        'error': str(raw.get('error') or default_code),
        'message': str(message),
        'field_errors': field_errors,
        'details': raw,
    }


def error_response(data, http_status=status.HTTP_400_BAD_REQUEST, default_message='An error occurred', default_code='validation_error'):
    return Response(
        normalize_error_payload(data, default_message=default_message, default_code=default_code),
        status=http_status,
    )
