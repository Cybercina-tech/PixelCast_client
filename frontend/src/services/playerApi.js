import axios from 'axios'
import { getBackendOrigin } from '@/utils/mediaUrl'
import { normalizeApiError } from '@/utils/apiError'
import {
  getBrowserIotBaseUrl,
  normalizeApiBaseForBrowser,
  rewriteAxiosConfigIfDockerInternalHost,
} from '@/utils/apiBaseUrl'

/** Same-origin /iot unless overridden — Vite/nginx proxy to Django. */
const IOT_BASE_URL = normalizeApiBaseForBrowser(getBrowserIotBaseUrl(), { emptyFallback: '/iot' })

export const MEDIA_BASE_URL = import.meta.env.VITE_MEDIA_BASE_URL || getBackendOrigin()

const playerApi = axios.create({
  baseURL: IOT_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
  // Template endpoint may return 304 Not Modified (If-None-Match); treat as success.
  validateStatus: (status) => (status >= 200 && status < 300) || status === 304,
})

// Same as main api client: env may point at Docker-only hosts baked at module load time.
playerApi.interceptors.request.use((config) => {
  const next = normalizeApiBaseForBrowser(getBrowserIotBaseUrl(), { emptyFallback: '/iot' })
  config.baseURL = next
  playerApi.defaults.baseURL = next
  return rewriteAxiosConfigIfDockerInternalHost(config)
})

// Strip any JWT Authorization header; inject X-Device-Token instead
playerApi.interceptors.request.use((config) => {
  delete config.headers.Authorization
  delete config.headers.authorization
  if (deviceToken) {
    config.headers['X-Device-Token'] = deviceToken
  }
  return config
})

let screenId = null
let deviceToken = null

// ── Identity management ──────────────────────────────────────────

export const setDeviceIdentity = ({ screenId: sid, deviceToken: dt }) => {
  screenId = sid
  deviceToken = dt
}

export const getDeviceIdentity = () => ({ screenId, deviceToken })

export const clearDeviceIdentity = () => {
  screenId = null
  deviceToken = null
}

// Legacy compat — used by store during migration
export const setScreenId = (id) => { screenId = id }
export const getScreenId = () => screenId

// ── Helpers ──────────────────────────────────────────────────────

function resolveIdentity(override = {}) {
  const resolvedScreenId = override.screenId || screenId
  const resolvedDeviceToken = override.deviceToken || deviceToken
  if (!resolvedScreenId || !resolvedDeviceToken) {
    const err = new Error('Device not paired. screen_id and device_token are required.')
    err.code = 'DEVICE_NOT_PAIRED'
    throw err
  }
  return { screenId: resolvedScreenId, deviceToken: resolvedDeviceToken }
}

function wrapError(error) {
  if (error.response) {
    const normalized = normalizeApiError(error)
    const status = normalized.status
    const msg = normalized.userMessage || `HTTP ${status}`
    const wrapped = new Error(msg)
    wrapped.status = status
    wrapped.apiError = normalized
    wrapped.fieldErrors = normalized.fieldErrors
    if (status === 401) wrapped.code = 'DEVICE_AUTH_FAILED'
    throw wrapped
  }
  if (error.request) throw new Error('Network error: No response from server')
  throw new Error(error.message || 'Request failed')
}

// ── API methods ──────────────────────────────────────────────────

export const fetchTemplate = async (override = {}) => {
  const identity = resolveIdentity(override)
  const { ifNoneMatch } = override
  try {
    const response = await playerApi.get('/player/template/', {
      params: { screen_id: identity.screenId },
      headers: ifNoneMatch ? { 'If-None-Match': ifNoneMatch } : {},
    })
    if (response.status === 304) {
      return {
        status: 'not_modified',
        _timeSync: null,
        _etag: ifNoneMatch || response.headers?.etag || response.headers?.ETag || null,
      }
    }
    const data = response.data || {}
    const dateHeader = response.headers?.date
    let serverNowMs = null
    if (dateHeader) {
      const parsed = Date.parse(dateHeader)
      if (!Number.isNaN(parsed)) serverNowMs = parsed
    }
    const clientNowMs = Date.now()
    const etagHeader = response.headers?.etag || response.headers?.ETag || null
    return {
      ...data,
      _etag: etagHeader,
      _timeSync: serverNowMs != null ? { serverNowMs, clientNowMs } : null,
    }
  } catch (error) {
    wrapError(error)
  }
}

export const sendHeartbeat = async (systemInfo = {}, override = {}) => {
  const identity = resolveIdentity(override)
  try {
    const response = await playerApi.post('/screens/heartbeat/', {
      screen_id: identity.screenId,
      ...systemInfo,
    })
    return response.data
  } catch (error) {
    wrapError(error)
  }
}

export const fetchPendingCommands = async (override = {}) => {
  const identity = resolveIdentity(override)
  try {
    const response = await playerApi.get('/commands/pending/', {
      params: { screen_id: identity.screenId, limit: 10 },
    })
    return response.data
  } catch (error) {
    wrapError(error)
  }
}

export const updateCommandStatus = async (commandId, status, errorMessage = '', responsePayload = {}, override = {}) => {
  const identity = resolveIdentity(override)
  if (!commandId) throw new Error('command_id is required')
  try {
    const response = await playerApi.post('/commands/status/', {
      screen_id: identity.screenId,
      command_id: commandId,
      status,
      error_message: errorMessage,
      response_payload: responsePayload,
    })
    return response.data
  } catch (error) {
    wrapError(error)
  }
}

const playerAPI = {
  setDeviceIdentity,
  getDeviceIdentity,
  clearDeviceIdentity,
  setScreenId,
  getScreenId,
  fetchTemplate,
  sendHeartbeat,
  fetchPendingCommands,
  updateCommandStatus,
}

export default playerAPI
