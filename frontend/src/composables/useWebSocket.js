/**
 * WebSocket composable for real-time dashboard updates.
 * 
 * Provides:
 * - Auto-connect on login
 * - Auto-reconnect with exponential backoff
 * - Graceful disconnect on logout
 * - Real-time event handling
 */
import { ref } from 'vue'
import { isDockerServiceHostname } from '@/utils/apiBaseUrl'

/**
 * Base WebSocket origin (no path): ws(s)://host[:port]
 * - Prefer VITE_WS_URL if set (may be full URL; path is stripped).
 * - Otherwise use the current page origin so dev traffic goes through the Vite proxy
 *   (see vite.config.js proxy `/ws`) instead of requiring a published backend port :8000.
 */
function getWebSocketOrigin() {
  const raw = import.meta.env.VITE_WS_URL
  if (raw && String(raw).trim()) {
    try {
      const s = String(raw).trim()
      const u = new URL(s.includes('://') ? s : `http://${s}`)
      if (isDockerServiceHostname(u.hostname)) {
        /* browser cannot resolve Docker service names */
      } else {
        const proto =
          u.protocol === 'https:' || u.protocol === 'wss:' ? 'wss:' : 'ws:'
        return `${proto}//${u.host}`
      }
    } catch {
      /* fall through */
    }
  }
  if (typeof window !== 'undefined' && window.location?.host) {
    return `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
  }
  return 'ws://127.0.0.1:8000'
}

const RECONNECT_DELAY = 1000
const MAX_RECONNECT_DELAY = 30000
const PING_INTERVAL = 30000

export function useWebSocket() {
  const socket = ref(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const reconnectTimer = ref(null)
  const pingTimer = ref(null)
  const eventHandlers = ref(new Map())

  const connect = (token) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    try {
      const wsUrl = `${getWebSocketOrigin()}/ws/dashboard/?token=${encodeURIComponent(token)}`
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        console.log('WebSocket connected')
        isConnected.value = true
        reconnectAttempts.value = 0
        
        // Start ping interval
        startPingInterval()
        
        // Emit connection event
        emit('connected', { timestamp: new Date().toISOString() })
      }

      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      socket.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        emit('error', { error: 'WebSocket connection error' })
      }

      socket.value.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason)
        isConnected.value = false
        stopPingInterval()
        
        // Emit disconnection event
        emit('disconnected', { code: event.code, reason: event.reason })
        
        // Auto-reconnect if not intentional close
        if (event.code !== 1000) {
          scheduleReconnect(token)
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      scheduleReconnect(token)
    }
  }

  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
    
    stopPingInterval()
    
    if (socket.value) {
      socket.value.close(1000, 'User logout')
      socket.value = null
    }
    
    isConnected.value = false
    reconnectAttempts.value = 0
  }

  const scheduleReconnect = (token) => {
    if (reconnectTimer.value) {
      return // Already scheduled
    }

    const delay = Math.min(
      RECONNECT_DELAY * Math.pow(2, reconnectAttempts.value),
      MAX_RECONNECT_DELAY
    )

    reconnectAttempts.value++
    console.log(`Scheduling WebSocket reconnect in ${delay}ms (attempt ${reconnectAttempts.value})`)

    reconnectTimer.value = setTimeout(() => {
      reconnectTimer.value = null
      connect(token)
    }, delay)
  }

  const startPingInterval = () => {
    stopPingInterval()
    
    pingTimer.value = setInterval(() => {
      if (socket.value && socket.value.readyState === WebSocket.OPEN) {
        send({ type: 'ping' })
      }
    }, PING_INTERVAL)
  }

  const stopPingInterval = () => {
    if (pingTimer.value) {
      clearInterval(pingTimer.value)
      pingTimer.value = null
    }
  }

  const handleMessage = (data) => {
    const { type } = data

    // Handle connection confirmation
    if (type === 'connection_confirmed') {
      console.log('WebSocket connection confirmed:', data)
      emit('connection_confirmed', data)
      return
    }

    // Handle pong
    if (type === 'pong') {
      return
    }

    // Handle error
    if (type === 'error') {
      console.error('WebSocket error:', data.message)
      emit('error', data)
      return
    }

    // Route to registered handlers
    emit(type, data.data || data)
  }

  const send = (data) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(data))
    } else {
      console.warn('Cannot send message: WebSocket not connected')
    }
  }

  const on = (eventType, handler) => {
    if (!eventHandlers.value.has(eventType)) {
      eventHandlers.value.set(eventType, [])
    }
    eventHandlers.value.get(eventType).push(handler)
  }

  const off = (eventType, handler) => {
    if (eventHandlers.value.has(eventType)) {
      const handlers = eventHandlers.value.get(eventType)
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  const emit = (eventType, data) => {
    if (eventHandlers.value.has(eventType)) {
      eventHandlers.value.get(eventType).forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error(`Error in event handler for ${eventType}:`, error)
        }
      })
    }
  }

  const subscribeScreen = (screenId) => {
    send({
      type: 'subscribe_screen',
      screen_id: screenId
    })
  }

  const unsubscribeScreen = (screenId) => {
    send({
      type: 'unsubscribe_screen',
      screen_id: screenId
    })
  }

  const subscribeCommand = (commandId) => {
    send({
      type: 'subscribe_command',
      command_id: commandId
    })
  }

  return {
    socket,
    isConnected,
    connect,
    disconnect,
    send,
    on,
    off,
    subscribeScreen,
    unsubscribeScreen,
    subscribeCommand
  }
}
