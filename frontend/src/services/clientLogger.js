/**
 * Remote Client Logging Service
 * 
 * Sends critical JavaScript errors from the Player/Editor back to the Django backend
 * for debugging screens that are physically far away (the "Black Box").
 */

import api from './api.js'

/**
 * Log levels
 */
const LOG_LEVELS = {
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  DEBUG: 'debug',
}

/**
 * Queue for storing logs when offline
 */
let logQueue = []
let isOnline = navigator.onLine

/**
 * Initialize client-side error logging
 */
export function initClientLogger() {
  // Listen for online/offline events
  window.addEventListener('online', () => {
    isOnline = true
    flushLogQueue()
  })
  
  window.addEventListener('offline', () => {
    isOnline = false
  })
  
  // Global error handler
  window.addEventListener('error', (event) => {
    logClientError({
      level: LOG_LEVELS.ERROR,
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error?.stack,
      timestamp: new Date().toISOString(),
    })
  })
  
  // Unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    logClientError({
      level: LOG_LEVELS.ERROR,
      message: `Unhandled Promise Rejection: ${event.reason}`,
      stack: event.reason?.stack,
      timestamp: new Date().toISOString(),
    })
  })
  
  // Console error interceptor (optional, for debugging)
  if (import.meta.env.DEV) {
    const originalError = console.error
    console.error = (...args) => {
      originalError.apply(console, args)
      // Only log to backend in production or if explicitly enabled
      if (import.meta.env.VITE_ENABLE_CLIENT_LOGGING === 'true') {
        logClientError({
          level: LOG_LEVELS.ERROR,
          message: args.map(arg => String(arg)).join(' '),
          timestamp: new Date().toISOString(),
        })
      }
    }
  }
}

/**
 * Log a client-side error to the backend
 * 
 * @param {Object} logData - Error log data
 * @param {string} logData.level - Log level (error, warning, info, debug)
 * @param {string} logData.message - Error message
 * @param {string} [logData.filename] - Source file name
 * @param {number} [logData.lineno] - Line number
 * @param {number} [logData.colno] - Column number
 * @param {string} [logData.stack] - Stack trace
 * @param {string} [logData.timestamp] - ISO timestamp
 * @param {Object} [logData.metadata] - Additional metadata
 */
export async function logClientError(logData) {
  const payload = {
    level: logData.level || LOG_LEVELS.ERROR,
    message: logData.message || 'Unknown error',
    filename: logData.filename || window.location.href,
    lineno: logData.lineno || null,
    colno: logData.colno || null,
    stack: logData.stack || null,
    user_agent: navigator.userAgent,
    url: window.location.href,
    timestamp: logData.timestamp || new Date().toISOString(),
    metadata: {
      ...(logData.metadata || {}),
      screen_id: getScreenId(),
      template_id: getTemplateId(),
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
    },
  }
  
  // If offline, queue the log
  if (!isOnline) {
    logQueue.push(payload)
    // Limit queue size to prevent memory issues
    if (logQueue.length > 100) {
      logQueue.shift()
    }
    return
  }
  
  // During setup, backend intentionally returns 503 for most APIs; skip noisy client-log posts.
  if (window.location.pathname.startsWith('/install')) {
    return
  }

  // Send to backend
  try {
    await api.post('/logs/client/', payload)
  } catch (error) {
    // Suppress expected pre-install failures.
    const status = error?.response?.status
    const code = error?.response?.data?.error
    if (status === 503 && code === 'installation_required') {
      return
    }

    // If sending fails, queue it for later
    console.warn('Failed to send client log to backend:', error)
    logQueue.push(payload)
    if (logQueue.length > 100) {
      logQueue.shift()
    }
  }
}

/**
 * Flush queued logs when connection is restored
 */
async function flushLogQueue() {
  if (logQueue.length === 0) return
  
  const logsToSend = [...logQueue]
  logQueue = []
  
  for (const log of logsToSend) {
    try {
      await api.post('/logs/client/', log)
    } catch (error) {
      // If still failing, re-queue
      logQueue.push(log)
    }
  }
}

/**
 * Get screen ID from URL or localStorage (for Player)
 */
function getScreenId() {
  // Try to get from route params (/player/:screenId, /screens/:id)
  const playerPathMatch = window.location.pathname.match(/\/player\/([^\/]+)/)
  if (playerPathMatch?.[1]) return playerPathMatch[1]

  const screenPathMatch = window.location.pathname.match(/\/screens\/([^\/]+)/)
  if (screenPathMatch?.[1]) return screenPathMatch[1]

  // Try to get from URL params
  const urlParams = new URLSearchParams(window.location.search)
  const screenId = urlParams.get('screen_id')
  if (screenId) return screenId
  
  // Try to get from localStorage (new and legacy keys)
  return (
    localStorage.getItem('player_screen_id') ||
    localStorage.getItem('screen_id') ||
    null
  )
}

/**
 * Get template ID from URL or localStorage (for Editor)
 */
function getTemplateId() {
  // Try to get from route params (Vue Router)
  if (window.__VUE_ROUTER__) {
    const route = window.__VUE_ROUTER__.currentRoute.value
    if (route?.params?.id) return route.params.id
  }
  
  // Try to get from URL
  const pathMatch = window.location.pathname.match(/\/templates\/([^\/]+)/)
  if (pathMatch) return pathMatch[1]
  
  return null
}

/**
 * Manual log function for explicit logging
 * 
 * @param {string} level - Log level
 * @param {string} message - Log message
 * @param {Object} [metadata] - Additional metadata
 */
export function log(level, message, metadata = {}) {
  logClientError({
    level,
    message,
    metadata,
  })
}

/**
 * Convenience functions
 */
export const clientLogger = {
  error: (message, metadata) => log(LOG_LEVELS.ERROR, message, metadata),
  warning: (message, metadata) => log(LOG_LEVELS.WARNING, message, metadata),
  info: (message, metadata) => log(LOG_LEVELS.INFO, message, metadata),
  debug: (message, metadata) => log(LOG_LEVELS.DEBUG, message, metadata),
}

