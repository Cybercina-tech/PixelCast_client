import axios from 'axios'
import { getNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'
import {
  getBrowserApiBaseUrl,
  ensureBrowserReachableApiBase,
  normalizeApiBaseForBrowser,
  rewriteAxiosConfigIfDockerInternalHost,
} from '@/utils/apiBaseUrl'

/** Avoid stacking identical "Too many requests" toasts when many API calls hit 429 at once */
let lastGlobal429ToastAt = 0
const GLOBAL_429_TOAST_COOLDOWN_MS = 5000

// API base URL — Docker-only hostnames (backend:8000) are rewritten for the browser (see apiBaseUrl.js)
const API_BASE_URL = normalizeApiBaseForBrowser(ensureBrowserReachableApiBase(getBrowserApiBaseUrl(), '/api'))

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Always resolve API base in the browser (env may wrongly point at Docker-only hosts like backend:8000)
api.interceptors.request.use((config) => {
  const next = normalizeApiBaseForBrowser(ensureBrowserReachableApiBase(getBrowserApiBaseUrl(), '/api'))
  config.baseURL = next
  api.defaults.baseURL = next
  return rewriteAxiosConfigIfDockerInternalHost(config)
})

// Request interceptor to add auth token and handle FormData
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // CRITICAL: Remove Content-Type header for FormData so axios can set it automatically with boundary
    // If we don't do this, the default 'application/json' header will break multipart/form-data uploads
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
      // axios will automatically set: Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const errorData = error.response?.data || {}

    if (status === 429) {
      const ra = error.response?.headers?.['retry-after'] ?? error.response?.headers?.['Retry-After']
      const headerSec = parseInt(ra, 10)
      let retrySec = Number.isFinite(headerSec) && headerSec > 0 ? headerSec : null
      if (errorData && typeof errorData === 'object' && errorData.retry_after != null) {
        const n = Number(errorData.retry_after)
        if (Number.isFinite(n) && n > 0) retrySec = n
      }
      error.retryAfterSeconds = retrySec
    }

    // Single retry for GET on 429 after backoff (bursts from list prefetch / UI loops)
    if (
      status === 429 &&
      originalRequest &&
      !originalRequest._retry429 &&
      String(originalRequest.method || 'get').toLowerCase() === 'get'
    ) {
      originalRequest._retry429 = true
      const ra = error.response?.headers?.['retry-after'] ?? error.response?.headers?.['Retry-After']
      const sec = parseInt(ra, 10)
      const delay = Number.isFinite(sec) && sec > 0 ? sec * 1000 : 1500
      await new Promise((r) => setTimeout(r, Math.min(delay, 10_000)))
      return api(originalRequest)
    }
    
    // Handle installation required (503 with installation_required error)
    if (status === 503 && (errorData.error === 'installation_required' || errorData.status === 'not_installed')) {
      // Redirect to install page if not already there.
      // Do not surface a global toast for this expected pre-install state.
      if (window.location.pathname !== '/install' && !originalRequest.url?.includes('/setup/')) {
        console.warn('Installation required - redirecting to /install')
        window.location.href = '/install'
      }
      return Promise.reject(error)
    }

    // Handle restriction payloads (user/tenant locked by admin)
    if (errorData.restriction) {
      try {
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()
        authStore.restriction = errorData.restriction
        const { getNotification } = await import('@/composables/useNotification')
        const notify = getNotification()
        if (notify) {
          notify.error(errorData.restriction.message || 'Access Restricted', { title: 'Access Restricted', duration: 6000 })
        }
        if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/403')) {
          window.location.href = '/403'
        }
      } catch {
        /* store not yet initialized */
      }
      return Promise.reject(error)
    }

    // Handle license enforcement responses
    if ((status === 402 || status === 403) && typeof errorData.error === 'string' && errorData.error.startsWith('license_')) {
      const params = new URLSearchParams(window.location.search)
      const onLicenseTab = window.location.pathname === '/settings' && params.get('tab') === 'license'
      if (!onLicenseTab) {
        window.location.href = '/settings?tab=license'
      }
      return Promise.reject(error)
    }
    
    // Don't try to refresh token for auth endpoints (login, signup, etc.)
    const isAuthEndpoint =
      originalRequest.url?.includes('/auth/login/') ||
      originalRequest.url?.includes('/auth/login/2fa/') ||
      originalRequest.url?.includes('/auth/signup/') ||
      originalRequest.url?.includes('/auth/token/')
    
    // Handle 401 - try to refresh token (but not for auth endpoints)
    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch(err => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')
      
      if (!refreshToken) {
        // No refresh token, clear everything and redirect to login
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        isRefreshing = false
        processQueue(new Error('No refresh token'), null)
        
        const notify = getNotification()
        notify.error('Session expired. Please log in again.')
        
        if (window.location.pathname !== '/login' && 
            window.location.pathname !== '/' &&
            !window.location.pathname.startsWith('/401')) {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }

      try {
        const response = await authAPI.refreshToken(refreshToken)
        const { access } = response.data
        
        localStorage.setItem('auth_token', access)
        if (response.data.refresh) {
          localStorage.setItem('refresh_token', response.data.refresh)
        }
        
        originalRequest.headers.Authorization = `Bearer ${access}`
        isRefreshing = false
        processQueue(null, access)
        
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        isRefreshing = false
        processQueue(refreshError, null)
        
        const notify = getNotification()
        notify.error('Session expired. Please log in again.')
        
        if (window.location.pathname !== '/login' && 
            window.location.pathname !== '/' &&
            !window.location.pathname.startsWith('/401')) {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }
    
    // Handle 4xx and 5xx errors with user-friendly notifications
    if (status && status >= 400) {
      const envelope = normalizeApiError(error)
      error.apiError = envelope
      error.fieldErrors = envelope.fieldErrors
      const userMessage = envelope.userMessage
      const errorData = envelope.raw || {}
      const shouldSuppressGlobalToast = Boolean(originalRequest?.meta?.suppressGlobalErrorToast)
      
      // Suppress screen_id errors - these are expected for global dashboard endpoints
      // and shouldn't be shown to users
      const isScreenIdError = userMessage?.includes('screen_id') || 
                              errorData?.message?.includes('screen_id') ||
                              errorData?.error?.includes('screen_id') ||
                              originalRequest.url?.includes('/screens/command-pull/') ||
                              originalRequest.url?.includes('/screens/health-check/')
      
      // Only show notification if it's not a suppressed screen_id error
      // and this request did not opt out.
      if (!isScreenIdError && !shouldSuppressGlobalToast) {
        const notify = getNotification()
        
        // Validation errors should be shown inline in forms, not as panic toasts.
        const hasFieldErrors = Object.keys(envelope.fieldErrors || {}).length > 0
        if (envelope.isValidation && hasFieldErrors) {
          // no global toast
        } else if (status >= 500) {
          notify.error(userMessage, { title: 'Server Error', duration: 5000 })
        } else if (status === 403) {
          notify.error(userMessage, { title: 'Access Denied', duration: 4000 })
          // Optional: opt-in redirect for specific calls (default: no redirect; router guards handle page-level 403).
          if (
            originalRequest?.meta?.redirectOn403 === true &&
            !window.location.pathname.startsWith('/403')
          ) {
            setTimeout(() => {
              window.location.href = '/403'
            }, 2000)
          }
        } else if (status === 401) {
          notify.error(userMessage, { title: 'Authentication Required', duration: 3000 })
        } else if (status === 429) {
          const now = Date.now()
          if (now - lastGlobal429ToastAt >= GLOBAL_429_TOAST_COOLDOWN_MS) {
            lastGlobal429ToastAt = now
            notify.error(userMessage, { title: 'Too many requests', duration: 4000 })
          }
        } else {
          // 4xx errors (400, 404, 413, 422, etc.)
          notify.error(userMessage, { title: 'Request Error', duration: 4000 })
        }
      } else {
        // Log suppressed error for debugging (but don't show to user)
        console.debug('Suppressed screen_id error:', {
          url: originalRequest.url,
          message: userMessage,
          error: errorData
        })
      }
    }
    
    return Promise.reject(error)
  }
)

// Authentication API
export const authAPI = {
  signup: (data) =>
    api.post('/auth/signup/', data, { meta: { suppressGlobalErrorToast: true } }),
  login: (credentials) =>
    api.post('/auth/login/', credentials, { meta: { suppressGlobalErrorToast: true } }),
  login2fa: (data) =>
    api.post('/auth/login/2fa/', data, { meta: { suppressGlobalErrorToast: true } }),
  passwordResetRequest: (data) =>
    api.post('/auth/password-reset/request/', data, { meta: { suppressGlobalErrorToast: true } }),
  passwordResetConfirm: (data) =>
    api.post('/auth/password-reset/confirm/', data, { meta: { suppressGlobalErrorToast: true } }),
  twofaSetupStart: () => api.post('/auth/2fa/setup/start/'),
  twofaSetupConfirm: (data) => api.post('/auth/2fa/setup/confirm/', data),
  twofaDisable: (data) => api.post('/auth/2fa/disable/', data),
  revokeSession: (outstandingId) =>
    api.post('/auth/sessions/revoke/', { outstanding_id: outstandingId }),
  logout: (data) => api.post('/auth/logout/', data),
  logoutAll: () => api.post('/auth/logout-all/'),
  sessions: () => api.get('/auth/sessions/'),
  token: (credentials) => api.post('/auth/token/', credentials),
  refreshToken: (refresh) => {
    // Use a separate axios instance without interceptors to avoid infinite loop
    const refreshApi = axios.create({
      baseURL: normalizeApiBaseForBrowser(ensureBrowserReachableApiBase(getBrowserApiBaseUrl(), '/api')),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return refreshApi.post('/auth/token/refresh/', { refresh })
  },
}

// Users API
export const teamAPI = {
  invitations: () => api.get('/team/invitations/'),
  createInvitation: (data) => api.post('/team/invitations/', data),
  acceptInvitation: (data) => api.post('/team/invitations/accept/', data),
}

export const supportAPI = {
  tickets: () => api.get('/core/support/tickets/'),
  createTicket: (data) => api.post('/core/support/tickets/', data),
}

export const ticketsAPI = {
  list: (params) => api.get('/tickets/', { params }),
  detail: (id) => api.get(`/tickets/${id}/`),
  create: (data) => api.post('/tickets/', data),
  reply: (id, data) => api.post(`/tickets/${id}/reply/`, data),
  upload: (id, formData) => api.post(`/tickets/${id}/upload/`, formData),
  csat: (id, data) => api.post(`/tickets/${id}/csat/`, data),
}

export const platformTicketsAPI = {
  list: (params) => api.get('/platform/tickets/queue/', { params }),
  detail: (id) => api.get(`/platform/tickets/queue/${id}/`),
  create: (data) => api.post('/platform/tickets/queue/', data),
  users: (params) => api.get('/platform/tickets/queue/users/', { params }),
  tenants: (params) => api.get('/platform/tickets/queue/tenants/', { params }),
  assign: (id, data) => api.post(`/platform/tickets/queue/${id}/assign/`, data),
  transition: (id, data) => api.post(`/platform/tickets/queue/${id}/transition/`, data),
  reply: (id, data) => api.post(`/platform/tickets/queue/${id}/reply/`, data),
  merge: (id, data) => api.post(`/platform/tickets/queue/${id}/merge/`, data),
  upload: (id, formData) => api.post(`/platform/tickets/queue/${id}/upload/`, formData),

  queues: (params) => api.get('/platform/tickets/queues/', { params }),
  createQueue: (data) => api.post('/platform/tickets/queues/', data),
  updateQueue: (id, data) => api.patch(`/platform/tickets/queues/${id}/`, data),
  deleteQueue: (id) => api.delete(`/platform/tickets/queues/${id}/`),

  slaPolicies: (params) => api.get('/platform/tickets/sla-policies/', { params }),
  createSlaPolicy: (data) => api.post('/platform/tickets/sla-policies/', data),
  updateSlaPolicy: (id, data) => api.patch(`/platform/tickets/sla-policies/${id}/`, data),
  deleteSlaPolicy: (id) => api.delete(`/platform/tickets/sla-policies/${id}/`),

  routingRules: (params) => api.get('/platform/tickets/routing-rules/', { params }),
  createRoutingRule: (data) => api.post('/platform/tickets/routing-rules/', data),
  updateRoutingRule: (id, data) => api.patch(`/platform/tickets/routing-rules/${id}/`, data),
  deleteRoutingRule: (id) => api.delete(`/platform/tickets/routing-rules/${id}/`),

  cannedResponses: (params) => api.get('/platform/tickets/canned-responses/', { params }),
  createCannedResponse: (data) => api.post('/platform/tickets/canned-responses/', data),
  updateCannedResponse: (id, data) => api.patch(`/platform/tickets/canned-responses/${id}/`, data),
  deleteCannedResponse: (id) => api.delete(`/platform/tickets/canned-responses/${id}/`),

  tags: (params) => api.get('/platform/tickets/tags/', { params }),
  createTag: (data) => api.post('/platform/tickets/tags/', data),
  deleteTag: (id) => api.delete(`/platform/tickets/tags/${id}/`),

  roles: (params) => api.get('/platform/tickets/roles/', { params }),
  createRole: (data) => api.post('/platform/tickets/roles/', data),
  updateRole: (id, data) => api.patch(`/platform/tickets/roles/${id}/`, data),
  deleteRole: (id) => api.delete(`/platform/tickets/roles/${id}/`),

  analytics: (params) => api.get('/platform/tickets/analytics/', { params }),
  agentPerformance: (params) => api.get('/platform/tickets/agent-performance/', { params }),
  exportCsv: (params) => api.get('/platform/tickets/export.csv', { params, responseType: 'blob' }),
}

export const usersAPI = {
  list: (params) => api.get('/users/', { params }),
  detail: (id) => api.get(`/users/${id}/`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.put(`/users/${id}/`, data),
  patch: (id, data) => api.patch(`/users/${id}/`, data),
  delete: (id) => api.delete(`/users/${id}/`),
  me: () => api.get('/users/me/'),
  updateMe: (data) => api.patch('/users/me/', data),
  changePasswordMe: (data) => api.post('/users/change_password_me/', data),
  activityLogs: (params) => api.get('/users/activity_logs/', { params }),
  changePassword: (id, data) => api.post(`/users/${id}/change_password/`, data),
  changeRole: (id, data) => api.post(`/users/${id}/change_role/`, data),
  sendVerificationEmail: () => api.post('/send-verification-email/'),
  verifyEmail: (data) => api.post('/verify-email/', data),
  sidebarItems: () =>
    api.get('/sidebar-items/', { meta: { suppressGlobalErrorToast: true } }),
  lock: (id, data) => api.post(`/users/${id}/lock/`, data),
  unlock: (id) => api.post(`/users/${id}/unlock/`),
  revokeSessions: (id) => api.post(`/users/${id}/revoke_sessions/`),
  adminSetPassword: (id, data) => api.post(`/users/${id}/admin_set_password/`, data),
  setTenant: (id, data) => api.post(`/users/${id}/set_tenant/`, data),
}

// Roles API
export const rolesAPI = {
  list: () => api.get('/roles/'),
  create: (data) => api.post('/roles/create/', data),
}

// Screens API
export const screensAPI = {
  list: (params) => api.get('/screens/', { params }),
  detail: (id) => api.get(`/screens/${id}/`),
  create: (data) => api.post('/screens/', data),
  update: (id, data) => api.put(`/screens/${id}/`, data),
  patch: (id, data) => api.patch(`/screens/${id}/`, data),
  delete: (id) => api.delete(`/screens/${id}/`),
  heartbeat: (id, data) => api.post(`/screens/${id}/heartbeat/`, data),
  revokeToken: (id) => api.post(`/screens/${id}/revoke-token/`),
  regenerateToken: (id) => api.post(`/screens/${id}/regenerate-token/`),
  // Standalone endpoints (for screen clients)
  heartbeatStandalone: (data) => api.post('/screens/heartbeat/', data),
  commandPull: (params) => api.get('/screens/command-pull/', { params }),
  commandResponse: (data) => api.post('/screens/command-response/', data),
  contentSync: (data) => api.post('/screens/content-sync/', data),
  healthCheck: (params) => api.get('/screens/health-check/', { params }),
}

// Pairing API (public player — errors handled inline in PairingFlow; suppress spam toasts on poll)
export const pairingAPI = {
  generate: () => api.post('/pairing/generate/'),
  status: (params) =>
    api.get('/pairing/status/', {
      params,
      meta: { suppressGlobalErrorToast: true },
    }),
  bind: (data) => api.post('/pairing/bind/', data),
}

// Templates API
/** Deduplicate concurrent GET /templates/:id/ (list prefetch + card previews). */
const _templateDetailInflight = new Map()

export const templatesAPI = {
  list: (params) => api.get('/templates/', { params }),
  detail: (id) => {
    const key = String(id)
    if (_templateDetailInflight.has(key)) {
      return _templateDetailInflight.get(key)
    }
    const req = api.get(`/templates/${id}/`)
    _templateDetailInflight.set(key, req)
    req.finally(() => _templateDetailInflight.delete(key))
    return req
  },
  create: (data) => api.post('/templates/', data),
  update: (id, data) => api.put(`/templates/${id}/`, data),
  patch: (id, data) => api.patch(`/templates/${id}/`, data),
  delete: (id) => api.delete(`/templates/${id}/`),
  activateOnScreen: (id, data) => api.post(`/templates/${id}/activate_on_screen/`, data),
}

// Layers API
export const layersAPI = {
  list: (params) => api.get('/layers/', { params }),
  detail: (id) => api.get(`/layers/${id}/`),
  create: (data) => api.post('/layers/', data),
  update: (id, data) => api.put(`/layers/${id}/`, data),
  patch: (id, data) => api.patch(`/layers/${id}/`, data),
  delete: (id) => api.delete(`/layers/${id}/`),
}

// Widgets API
export const widgetsAPI = {
  list: (params) => api.get('/widgets/', { params }),
  detail: (id) => api.get(`/widgets/${id}/`),
  create: (data) => api.post('/widgets/', data),
  update: (id, data) => api.put(`/widgets/${id}/`, data),
  patch: (id, data) => api.patch(`/widgets/${id}/`, data),
  delete: (id) => api.delete(`/widgets/${id}/`),
}

export const qrActionsAPI = {
  links: {
    list: (params) => api.get('/qr-action-links/', { params }),
    detail: (id) => api.get(`/qr-action-links/${id}/`),
    create: (data) => api.post('/qr-action-links/', data),
    update: (id, data) => api.put(`/qr-action-links/${id}/`, data),
    patch: (id, data) => api.patch(`/qr-action-links/${id}/`, data),
    delete: (id) => api.delete(`/qr-action-links/${id}/`),
    analytics: (params) => api.get('/qr-action-links/analytics/', { params }),
  },
  rules: {
    list: (params) => api.get('/qr-action-rules/', { params }),
    create: (data) => api.post('/qr-action-rules/', data),
    update: (id, data) => api.put(`/qr-action-rules/${id}/`, data),
    patch: (id, data) => api.patch(`/qr-action-rules/${id}/`, data),
    delete: (id) => api.delete(`/qr-action-rules/${id}/`),
  },
  scans: {
    list: (params) => api.get('/qr-scan-events/', { params }),
    detail: (id) => api.get(`/qr-scan-events/${id}/`),
  },
}

// Contents API
export const contentsAPI = {
  list: (params) => api.get('/contents/', { params }),
  detail: (id) => api.get(`/contents/${id}/`),
  create: (data) => api.post('/contents/', data),
  update: (id, data) => api.put(`/contents/${id}/`, data),
  patch: (id, data) => api.patch(`/contents/${id}/`, data),
  delete: (id) => api.delete(`/contents/${id}/`),
  storageStats: () => api.get('/contents/storage_stats/'),
  downloadToScreen: (id, data) => api.post(`/contents/${id}/download_to_screen/`, data),
  retryDownload: (id, data) => api.post(`/contents/${id}/retry_download/`, data),
  upload: (id, file, data = {}) => {
    console.log('[API] uploadContent called', {
      contentId: id,
      fileName: file?.name,
      fileSize: file?.size,
      fileType: file?.type,
      additionalData: data
    })
    
    // Validate file
    if (!file) {
      console.error('[API] uploadContent: No file provided')
      return Promise.reject(new Error('No file provided'))
    }
    
    const formData = new FormData()
    formData.append('file', file)
    
    // Append additional data if provided
    Object.keys(data).forEach(key => {
      formData.append(key, data[key])
      console.log(`[API] uploadContent: Added form field "${key}":`, data[key])
    })
    
    // Log FormData contents (for debugging)
    console.log('[API] uploadContent: FormData prepared', {
      hasFile: formData.has('file'),
      fileInFormData: file,
      formDataKeys: Array.from(formData.keys())
    })
    
    // DO NOT set Content-Type manually - let axios set it with boundary
    // Setting it manually breaks multipart/form-data boundary
    return api.post(`/contents/${id}/upload/`, formData, {
      // Remove manual Content-Type header - axios will set it automatically with boundary
      // headers: { 'Content-Type': 'multipart/form-data' }, // ❌ WRONG - breaks boundary
    })
  },
  download: (id, params) => api.get(`/contents/${id}/download/`, { params }),
  verifyIntegrity: (id, data) => api.post(`/contents/${id}/verify_integrity/`, data),
}

// Schedules API
export const schedulesAPI = {
  list: (params) => api.get('/schedules/', { params }),
  detail: (id) => api.get(`/schedules/${id}/`),
  create: (data) => api.post('/schedules/', data),
  update: (id, data) => api.put(`/schedules/${id}/`, data),
  patch: (id, data) => api.patch(`/schedules/${id}/`, data),
  delete: (id) => api.delete(`/schedules/${id}/`),
  execute: (id, data) => api.post(`/schedules/${id}/execute/`, data),
  dueSchedules: (params) => api.get('/schedules/due_schedules/', { params }),
  conflicting: (params) => api.get('/schedules/conflicting/', { params }),
}

// Commands API
export const commandsAPI = {
  list: (params) => api.get('/commands/', { params }),
  detail: (id) => api.get(`/commands/${id}/`),
  create: (data) => api.post('/commands/', data),
  update: (id, data) => api.put(`/commands/${id}/`, data),
  patch: (id, data) => api.patch(`/commands/${id}/`, data),
  delete: (id) => api.delete(`/commands/${id}/`),
  execute: (id, data = {}) => api.post(`/commands/${id}/execute/`, data),
  retry: (id) => api.post(`/commands/${id}/retry/`),
  status: (params) => api.get('/commands/status/', { params }),
  pending: (params) => api.get('/commands/pending/', { params }),
}

// Logs API
export const logsAPI = {
  screenStatus: {
    list: (params) => api.get('/logs/screen-status/', { params }),
    detail: (id) => api.get(`/logs/screen-status/${id}/`),
    summary: (params) => api.get('/logs/screen-status/summary/', { params }),
  },
  contentDownload: {
    list: (params) => api.get('/logs/content-download/', { params }),
    detail: (id) => api.get(`/logs/content-download/${id}/`),
    summary: (params) => api.get('/logs/content-download/summary/', { params }),
  },
  commandExecution: {
    list: (params) => api.get('/logs/command-execution/', { params }),
    detail: (id) => api.get(`/logs/command-execution/${id}/`),
    summary: (params) => api.get('/logs/command-execution/summary/', { params }),
  },
}

// Analytics API
export const analyticsAPI = {
  screenStatistics: (params) => api.get('/analytics/screens/', { params }),
  screenDetail: (id) => api.get(`/analytics/screens/${id}/`),
  commandStatistics: (params) => api.get('/analytics/commands/', { params }),
  contentStatistics: (params) => api.get('/analytics/content/', { params }),
  templateStatistics: (params) => api.get('/analytics/templates/', { params }),
  activityTrends: (params) => api.get('/analytics/activity/', { params }),
}

// Core Infrastructure API
export const coreAPI = {
  systemEmail: {
    get: () => api.get('/core/system-email-settings/'),
    patch: (data) => api.patch('/core/system-email-settings/', data),
    test: (to) => api.post('/core/system-email-settings/test/', { to }),
  },
  // Audit Logs
  auditLogs: {
    list: (params) => api.get('/core/audit-logs/', { params }),
    detail: (id) => api.get(`/core/audit-logs/${id}/`),
    summary: (params) => api.get('/core/audit-logs/summary/', { params }),
  },
  // Backups
  backups: {
    list: (params) => api.get('/core/backups/', { params }),
    detail: (id) => api.get(`/core/backups/${id}/`),
    trigger: (data) => api.post('/core/backups/trigger/', data),
    verify: (id) => api.post(`/core/backups/${id}/verify/`),
    cleanup: () => api.post('/core/backups/cleanup/'),
  },
  tvCatalog: {
    list: (params) =>
      api.get('/core/tv-brands/', {
        params,
        meta: { suppressGlobalErrorToast: true },
      }),
    detail: (id) =>
      api.get(`/core/tv-brands/${id}/`, {
        meta: { suppressGlobalErrorToast: true },
      }),
  },
}

export const tvCatalogAPI = {
  list: (params) =>
    api.get('/core/tv-brands/', {
      params,
      meta: { suppressGlobalErrorToast: true },
    }),
  detail: (id) =>
    api.get(`/core/tv-brands/${id}/`, {
      meta: { suppressGlobalErrorToast: true },
    }),
}

// Notification Center API
export const notificationCenterAPI = {
  list: (params) =>
    api.get('/core/notifications/', {
      params,
      meta: { suppressGlobalErrorToast: true },
    }),
  markAsRead: (id) => api.post(`/core/notifications/${id}/mark_as_read/`),
  markAllAsRead: () => api.post('/core/notifications/mark_all_as_read/'),
  dismiss: (id) => api.delete(`/core/notifications/${id}/dismiss/`),
  clear: () => api.delete('/core/notifications/clear/'),
  getPreferences: () => api.get('/core/notification-preferences/me/'),
  savePreferences: (data) => api.put('/core/notification-preferences/me/', data),
}

// Platform (minimal — tenants + license registry; CodeCanyon-safe)
export const platformAPI = {
  tenants: {
    list: (params) => api.get('/platform/tenants/', { params }),
    retrieve: (id) => api.get(`/platform/tenants/${id}/`),
    create: (data) => api.post('/platform/tenants/', data),
    update: (id, data) => api.put(`/platform/tenants/${id}/`, data),
    patch: (id, data) => api.patch(`/platform/tenants/${id}/`, data),
    remove: (id) => api.delete(`/platform/tenants/${id}/`),
    manualOverride: (id, data) => api.post(`/platform/tenants/${id}/manual-override/`, data),
    auditLog: (id) => api.get(`/platform/tenants/${id}/audit-log/`),
    accessLock: (id, data) => api.post(`/platform/tenants/${id}/access-lock/`, data),
    accessUnlock: (id) => api.post(`/platform/tenants/${id}/access-unlock/`),
  },
  tenantFeatureFlags: {
    get: (tenantId) => api.get(`/platform/tenants/${tenantId}/feature-flags/`),
    update: (tenantId, data) => api.put(`/platform/tenants/${tenantId}/feature-flags/`, data),
  },
  tenantLicense: {
    get: (tenantId) => api.get(`/platform/tenants/${tenantId}/license/`),
    update: (tenantId, data) => api.put(`/platform/tenants/${tenantId}/license/`, data),
    enforcementLogs: (tenantId) => api.get(`/platform/tenants/${tenantId}/license/enforcement-logs/`),
  },
  selfHostedLicenses: {
    list: (params) => api.get('/platform/self-hosted-licenses/', { params }),
    detail: (id) => api.get(`/platform/self-hosted-licenses/${id}/`),
    patch: (id, data) => api.patch(`/platform/self-hosted-licenses/${id}/`, data),
    suspend: (id, data) => api.post(`/platform/self-hosted-licenses/${id}/suspend/`, data || {}),
    reactivate: (id) => api.post(`/platform/self-hosted-licenses/${id}/reactivate/`),
    setSuspicious: (id, data) => api.post(`/platform/self-hosted-licenses/${id}/suspicious/`, data || {}),
    heartbeats: (id) => api.get(`/platform/self-hosted-licenses/${id}/heartbeats/`),
  },
}

// Licensing API
export const licenseAPI = {
  status: () => api.get('/license/status/'),
  activate: (data) => api.post('/license/activate/', data),
  revalidate: (data = { force: true }) => api.post('/license/revalidate/', data),
  setProductIdOverride: (data) => api.post('/license/product-id-override/', data),
}

// Admin API (SuperAdmin only)
export const adminAPI = {
  // Error Logs
  errors: {
    list: (params) => api.get('/admin/errors/', { params }),
    detail: (id) => api.get(`/admin/errors/${id}/`),
    resolve: (id) => api.patch(`/admin/errors/${id}/resolve/`),
    stats: (params) => api.get('/admin/errors/stats/', { params }),
  },
}

// Public (no auth) — download URLs for player apps + deployment flags
export const publicAPI = {
  downloads: () =>
    api.get('/public/downloads/', {
      meta: { suppressGlobalErrorToast: true },
    }),
  deployment: () =>
    axios.get(`${normalizeApiBaseForBrowser(ensureBrowserReachableApiBase(getBrowserApiBaseUrl(), '/api'))}/public/deployment/`, {
      headers: { 'Content-Type': 'application/json' },
    }),
  pricing: () =>
    api.get('/public/pricing/', {
      meta: { suppressGlobalErrorToast: true },
    }),
}

// Setup/Installation API
export const setupAPI = {
  status: () => api.get('/setup/status/'),
  testDb: (data) => api.post('/setup/db-check/', data),
  runMigrations: () => api.post('/setup/run-migrations/'),
  seedAssets: () => api.post('/setup/seed-assets/'),
  createAdmin: (data) => api.post('/setup/create-admin/', data),
  finalize: (data = {}) => api.post('/setup/finalize/', data),
}

// WebSocket URL helper
export const getWebSocketURL = (path, token = null) => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsHost = import.meta.env.VITE_WS_HOST || window.location.host
  const baseURL = `${wsProtocol}//${wsHost}`
  const url = `${baseURL}${path}`
  return token ? `${url}?token=${token}` : url
}

export default api
