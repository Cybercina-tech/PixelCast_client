/**
 * Docker Compose service names are not DNS-resolvable in the user's browser.
 * Env often wrongly sets VITE_API_BASE_URL=https://backend:8000/api — axios + fetch then
 * target a host the browser cannot resolve. We strip Docker-only hosts and use the
 * current page origin so Vite/nginx proxy paths (/api, /iot) always work.
 */
const INTERNAL_DOCKER_HOSTS = new Set(['backend', 'django', 'web', 'api'])

export function isDockerServiceHostname(hostname) {
  if (!hostname) return false
  const h = String(hostname)
    .toLowerCase()
    .trim()
    .replace(/\u200b/g, '')
  return INTERNAL_DOCKER_HOSTS.has(h)
}

function browserOrigin() {
  if (typeof window === 'undefined') return ''
  const o = window.location.origin
  if (!o || o === 'null') return ''
  return o
}

/**
 * Last line of defense: never hand the browser a URL whose host only exists on Docker networks.
 * Handles protocol-relative //host:port/path and scheme-less host:port/path from misconfigured .env.
 */
/**
 * Final axios baseURL for the browser: never keep Docker-internal hosts (e.g. https://backend:8000/api).
 * Handles strings that slip past env rewriting (stale builds, odd .env, or URL edge cases).
 * @param {string} base
 * @param {{ emptyFallback?: string }} [options] - default path when base is empty (default '/api'; use '/iot' for player API)
 */
export function normalizeApiBaseForBrowser(base, options = {}) {
  const emptyFallback = options.emptyFallback ?? '/api'
  if (typeof window === 'undefined') return base
  const origin = browserOrigin()
  if (!origin) return String(base ?? '').trim() || emptyFallback

  const s = String(base ?? '').trim()
  if (!s) return `${origin}${emptyFallback.startsWith('/') ? emptyFallback : `/${emptyFallback}`}`

  // Misconfigured compose/Dokploy: full URL to a service name the browser cannot resolve
  // (Do not match api.example.com — only single-label hosts like https://api:8000/…)
  if (
    /^https?:\/\/backend(?::\d+)?(?:\/|$|\?|#)/i.test(s) ||
    /^https?:\/\/(django|web)(?::\d+)?(?:\/|$|\?|#)/i.test(s) ||
    /^https?:\/\/api(?::\d+)?(?:\/|$|\?|#)/i.test(s)
  ) {
    try {
      const u = new URL(s.includes('://') ? s : `https://${s}`)
      const rest = `${u.pathname || '/api'}${u.search || ''}${u.hash || ''}`
      return `${origin}${rest.startsWith('/') ? rest : `/${rest}`}`
    } catch {
      return `${origin}${emptyFallback.startsWith('/') ? emptyFallback : `/${emptyFallback}`}`
    }
  }

  try {
    const u = new URL(s, `${origin}/`)
    if (isDockerServiceHostname(u.hostname)) {
      const pathDefault = emptyFallback.startsWith('/') ? emptyFallback : `/${emptyFallback}`
      const rest = `${u.pathname || pathDefault}${u.search || ''}${u.hash || ''}`
      return `${origin}${rest.startsWith('/') ? rest : `/${rest}`}`
    }
  } catch {
    /* keep s */
  }
  return s
}

export function ensureBrowserReachableApiBase(url, fallbackPath = '/api') {
  if (typeof window === 'undefined') return url
  const origin = browserOrigin()
  if (!origin) {
    return typeof url === 'string' && url.startsWith('/') && !url.startsWith('//') ? url : '/api'
  }

  const raw = String(url ?? '').trim()
  if (!raw) {
    return `${origin}${fallbackPath.startsWith('/') ? fallbackPath : `/${fallbackPath}`}`
  }

  try {
    // Same-origin path only, e.g. /api
    if (raw.startsWith('/') && !raw.startsWith('//')) {
      return `${origin}${raw}`
    }

    const resolved = new URL(raw, window.location.href)
    if (isDockerServiceHostname(resolved.hostname)) {
      const path = `${resolved.pathname || fallbackPath}${resolved.search || ''}`
      const p = path.startsWith('/') ? path : `/${path}`
      return `${origin}${p}`
    }
    return raw
  } catch {
    return `${origin}${fallbackPath.startsWith('/') ? fallbackPath : `/${fallbackPath}`}`
  }
}

/**
 * @returns {string} In the browser: absolute same-origin base (e.g. http://localhost:5173/api).
 * Without window: env string or /api (SSR/tests).
 */
export function getBrowserApiBaseUrl() {
  let raw = String(import.meta.env.VITE_API_BASE_URL ?? '').trim() || '/api'

  if (typeof window === 'undefined') {
    return raw
  }

  const origin = browserOrigin()
  if (!origin) {
    return '/api'
  }

  // Protocol-relative //backend:8000/api → resolvable URL for parsing
  if (raw.startsWith('//')) {
    raw = `${window.location.protocol}${raw}`
  }

  // Real external API (public host): keep full URL — CORS must allow this origin.
  if (raw.startsWith('http://') || raw.startsWith('https://')) {
    try {
      const u = new URL(raw)
      if (!isDockerServiceHostname(u.hostname)) {
        return ensureBrowserReachableApiBase(raw, '/api')
      }
      const pq = `${u.pathname || '/api'}${u.search || ''}` || '/api'
      return ensureBrowserReachableApiBase(`${origin}${pq.startsWith('/') ? pq : '/' + pq}`, '/api')
    } catch {
      return ensureBrowserReachableApiBase(`${origin}/api`, '/api')
    }
  }

  // host-only Docker form: backend:8000/api
  if (raw && !raw.startsWith('/') && raw.includes('/')) {
    const hostOnly = raw.split('/')[0].split(':')[0]
    if (isDockerServiceHostname(hostOnly)) {
      const slash = raw.indexOf('/')
      const pq = slash >= 0 ? raw.slice(slash) : '/api'
      const path = pq.startsWith('/') ? pq : `/${pq}`
      return ensureBrowserReachableApiBase(`${origin}${path}`, '/api')
    }
  }

  // host:port only, no path — e.g. backend:8000 (misconfigured .env)
  if (raw && !raw.startsWith('/') && !raw.includes('/')) {
    const hostOnly = String(raw).split(':')[0]
    if (isDockerServiceHostname(hostOnly)) {
      return ensureBrowserReachableApiBase(`${origin}/api`, '/api')
    }
  }

  // Relative: /api
  const rel = raw.startsWith('/') ? raw : `/${raw || 'api'}`
  return ensureBrowserReachableApiBase(`${origin}${rel}`, '/api')
}

/**
 * Safe IoT base for axios in the browser (player / device API).
 */
export function getBrowserIotBaseUrl() {
  const raw = import.meta.env.VITE_IOT_BASE_URL
  if (!raw || !String(raw).trim()) {
    const origin = browserOrigin()
    return ensureBrowserReachableApiBase(origin ? `${origin}/iot` : '/iot', '/iot')
  }

  let s = String(raw).trim()
  if (typeof window === 'undefined') {
    return s
  }

  const origin = browserOrigin()
  if (!origin) {
    return s.startsWith('/') ? s : '/iot'
  }

  if (s.startsWith('//')) {
    s = `${window.location.protocol}${s}`
  }

  if (s.startsWith('http://') || s.startsWith('https://')) {
    try {
      const u = new URL(s)
      if (!isDockerServiceHostname(u.hostname)) {
        return ensureBrowserReachableApiBase(s, '/iot')
      }
      const pq = `${u.pathname || '/iot'}${u.search || ''}` || '/iot'
      return ensureBrowserReachableApiBase(`${origin}${pq.startsWith('/') ? pq : '/' + pq}`, '/iot')
    } catch {
      return ensureBrowserReachableApiBase(`${origin}/iot`, '/iot')
    }
  }

  if (s && !s.startsWith('/') && s.includes('/')) {
    const hostOnly = s.split('/')[0].split(':')[0]
    if (isDockerServiceHostname(hostOnly)) {
      const slash = s.indexOf('/')
      const pq = slash >= 0 ? s.slice(slash) : '/iot'
      const path = pq.startsWith('/') ? pq : `/${pq}`
      return ensureBrowserReachableApiBase(`${origin}${path}`, '/iot')
    }
  }

  if (s && !s.startsWith('/') && !s.includes('/')) {
    const hostOnly = String(s).split(':')[0]
    if (isDockerServiceHostname(hostOnly)) {
      return ensureBrowserReachableApiBase(`${origin}/iot`, '/iot')
    }
  }

  const rel = s.startsWith('/') ? s : `/${s || 'iot'}`
  return ensureBrowserReachableApiBase(`${origin}${rel}`, '/iot')
}

/**
 * Last-resort fix for axios: if the resolved request URL still targets a Docker-internal
 * hostname (mis-baked VITE_* or a rare merge edge case), rewrite to same-origin paths
 * that Vite/nginx proxy to Django.
 */
export function rewriteAxiosConfigIfDockerInternalHost(config) {
  if (typeof window === 'undefined' || !config) return config

  const origin = window.location.origin
  const base = String(config.baseURL ?? '').trim()
  const rel = config.url == null ? '' : String(config.url)

  let absoluteHref
  try {
    if (/^https?:\/\//i.test(rel)) {
      absoluteHref = rel
    } else {
      const baseRoot =
        base && /^https?:\/\//i.test(base)
          ? base
          : new URL(base || '/', `${origin}/`).href
      const normalized = baseRoot.endsWith('/') ? baseRoot : `${baseRoot}/`
      absoluteHref = new URL(rel || '/', normalized).href
    }
  } catch {
    return config
  }

  let u
  try {
    u = new URL(absoluteHref)
  } catch {
    return config
  }

  if (!isDockerServiceHostname(u.hostname)) {
    return config
  }

  const pathname = u.pathname
  const tail = u.search + u.hash

  const applyPrefix = (prefix) => {
    if (pathname !== prefix && !pathname.startsWith(`${prefix}/`)) {
      return false
    }
    const restPath = pathname === prefix ? '/' : pathname.slice(prefix.length) || '/'
    const combined = restPath + tail
    config.baseURL = `${origin}${prefix}`
    config.url = combined.startsWith('/') ? combined.slice(1) : combined
    return true
  }

  if (applyPrefix('/api')) return config
  if (applyPrefix('/iot')) return config
  if (applyPrefix('/public-iot')) return config

  const fallback = pathname + tail
  config.baseURL = origin
  config.url = fallback.startsWith('/') ? fallback.slice(1) : fallback
  return config
}
