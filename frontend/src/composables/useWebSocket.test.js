import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useWebSocket } from './useWebSocket'

class MockWebSocket {
  static OPEN = 1
  static instances = []

  constructor(url) {
    this.url = url
    this.readyState = MockWebSocket.OPEN
    this.onopen = null
    this.onclose = null
    this.onmessage = null
    this.onerror = null
    MockWebSocket.instances.push(this)
  }

  close(code = 1000, reason = 'closed') {
    this.readyState = 3
    this.onclose?.({ code, reason })
  }

  send() {}
}

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.stubGlobal('window', {
      location: { protocol: 'http:', host: 'localhost:5173' },
    })
  })

  it('removes all handlers when off is called without handler', () => {
    const ws = useWebSocket()
    const handler = vi.fn()

    ws.on('screen_status_update', handler)
    ws.off('screen_status_update')
    ws.connect('token')

    const sock = MockWebSocket.instances[0]
    sock.onmessage?.({
      data: JSON.stringify({ type: 'screen_status_update', data: { ok: true } }),
    })
    expect(handler).not.toHaveBeenCalled()
  })

  it('does not reconnect after intentional disconnect', () => {
    const ws = useWebSocket()
    ws.connect('token')

    const sock = MockWebSocket.instances[0]
    ws.disconnect()
    sock.onclose?.({ code: 1006, reason: 'network' })
    vi.advanceTimersByTime(31_000)

    expect(MockWebSocket.instances.length).toBe(1)
  })
})
