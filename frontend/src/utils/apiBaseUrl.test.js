import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  getBrowserApiBaseUrl,
  normalizeApiBaseForBrowser,
  isDockerServiceHostname,
  rewriteAxiosConfigIfDockerInternalHost,
} from './apiBaseUrl.js'

describe('isDockerServiceHostname', () => {
  it('treats compose service names as internal', () => {
    expect(isDockerServiceHostname('backend')).toBe(true)
    expect(isDockerServiceHostname('django')).toBe(true)
    expect(isDockerServiceHostname('web')).toBe(true)
    expect(isDockerServiceHostname('api')).toBe(true)
  })

  it('does not treat public API subdomains as internal', () => {
    expect(isDockerServiceHostname('api.example.com')).toBe(false)
    expect(isDockerServiceHostname('backend.example.com')).toBe(false)
  })
})

describe('normalizeApiBaseForBrowser', () => {
  it('rewrites https://backend:8000/api to same origin', () => {
    expect(normalizeApiBaseForBrowser('https://backend:8000/api')).toBe(
      'http://localhost:5173/api'
    )
  })

  it('rewrites protocol-relative //backend:8000/api', () => {
    expect(normalizeApiBaseForBrowser('//backend:8000/api')).toBe('http://localhost:5173/api')
  })
})

describe('getBrowserApiBaseUrl', () => {
  beforeEach(() => {
    vi.unstubAllEnvs()
  })

  it('rewrites VITE_API_BASE_URL=https://backend:8000/api to page origin /api', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://backend:8000/api')
    vi.resetModules()
    const { getBrowserApiBaseUrl: getUrl } = await import('./apiBaseUrl.js')
    expect(getUrl()).toBe('http://localhost:5173/api')
  })

  it('uses relative /api when VITE_API_BASE_URL is /api', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '/api')
    vi.resetModules()
    const { getBrowserApiBaseUrl: getUrl } = await import('./apiBaseUrl.js')
    expect(getUrl()).toBe('http://localhost:5173/api')
  })
})

describe('rewriteAxiosConfigIfDockerInternalHost', () => {
  it('rewrites axios config targeting backend:8000', () => {
    const config = {
      baseURL: 'https://backend:8000/api',
      url: 'auth/login/',
    }
    rewriteAxiosConfigIfDockerInternalHost(config)
    expect(config.baseURL).toBe('http://localhost:5173/api')
    expect(config.url).toMatch(/auth\/login/)
  })
})
