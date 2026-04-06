const FALLBACK_MESSAGES = {
  400: 'Invalid request. Please check your input.',
  401: 'Authentication required. Please log in.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  413: 'File too large. Please choose a smaller file.',
  415: 'Unsupported file type. Please choose a different file.',
  422: 'Validation error. Please check your input.',
  429: 'Too many requests. Please wait and try again.',
  500: 'Server error. Please try again later.',
  502: 'Service temporarily unavailable. Please try again later.',
  503: 'Service unavailable. Please try again later.',
  504: 'Request timeout. Please try again.',
}

const RESERVED_KEYS = new Set([
  'status',
  'error',
  'message',
  'detail',
  'details',
  'field_errors',
  'errors',
  'non_field_errors',
  '__all__',
  'code',
  'error_code',
  'success',
  'lockout_seconds',
])

function asList(value) {
  if (value === undefined || value === null) return []
  if (Array.isArray(value)) return value.map((v) => String(v))
  return [String(value)]
}

export function normalizeApiError(error) {
  const status = error?.response?.status ?? error?.status ?? 0
  const data = error?.response?.data || {}

  const fieldErrors = {}
  const explicitFieldErrors = data.field_errors || data.errors
  if (explicitFieldErrors && typeof explicitFieldErrors === 'object' && !Array.isArray(explicitFieldErrors)) {
    Object.entries(explicitFieldErrors).forEach(([key, value]) => {
      fieldErrors[key] = asList(value)
    })
  }

  if (data && typeof data === 'object') {
    Object.entries(data).forEach(([key, value]) => {
      if (RESERVED_KEYS.has(key)) return
      if (typeof value === 'string' || Array.isArray(value)) {
        fieldErrors[key] = asList(value)
      }
    })
  }

  const nonField = [
    ...asList(data.non_field_errors),
    ...asList(data.__all__),
  ]

  const rawMessage = data.message || data.detail || data.error
  let userMessage = String(
    rawMessage ||
      nonField[0] ||
      Object.values(fieldErrors)[0]?.[0] ||
      FALLBACK_MESSAGES[status] ||
      error?.message ||
      'An unexpected error occurred.'
  )
  // installation_required is handled by API interceptor redirect; avoid noisy duplicate copy here.

  return {
    status,
    code: data.error || data.code || 'request_error',
    formError: userMessage,
    userMessage,
    fieldErrors,
    isValidation: status === 400 || status === 422,
    raw: data,
  }
}

export function extractFieldError(envelope, fieldName) {
  const value = envelope?.fieldErrors?.[fieldName]
  if (!value) return ''
  return Array.isArray(value) ? value[0] : String(value)
}
