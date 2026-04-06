/**
 * Public site branding and SEO defaults (digital signage focus, soft UK where relevant).
 */

export const SITE_NAME = 'PixelCast'

/** @returns {string} Origin without trailing slash, or '' if unset (canonical/OG omitted). */
export function getSiteOrigin() {
  const raw = import.meta.env.VITE_PUBLIC_SITE_ORIGIN
  if (raw && String(raw).trim()) {
    return String(raw).trim().replace(/\/$/, '')
  }
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }
  return ''
}

export function getPublicRegionPhrase() {
  const r = (import.meta.env.VITE_PUBLIC_REGION || '').trim().toUpperCase()
  if (r === 'UK' || r === 'GB') return 'UK'
  return ''
}

/**
 * Optional full URL for default Open Graph image (1200×630). If unset, og:image is omitted (avoids broken previews).
 */
export function getDefaultOgImageUrl() {
  const full = import.meta.env.VITE_OG_IMAGE_URL
  if (full && String(full).trim().startsWith('http')) {
    return String(full).trim()
  }
  return ''
}

export const DEFAULT_DESCRIPTION =
  'Commercial digital signage software for UK teams and global fleets—manage displays, templates, schedules, and remote players from one secure platform.'
