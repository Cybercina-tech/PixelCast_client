/**
 * Session list display helpers (aligns with /api/auth/sessions/ payload).
 */

export function sessionTitle(session) {
  if (!session) return 'Unknown device'
  if (session.device) return session.device
  if (session.browser && session.os) return `${session.browser} on ${session.os}`
  return session.browser || session.os || 'Unknown device'
}

export function sessionSubtitle(session) {
  const parts = []
  if (session?.browser && session?.os && session.device !== `${session.browser} on ${session.os}`) {
    parts.push(`${session.browser} · ${session.os}`)
  }
  if (session?.ip_address && session.ip_address !== '—') {
    parts.push(`IP ${session.ip_address}`)
  }
  return parts.join(' · ')
}

export function sessionDeviceKind(session) {
  const kind = (session?.device_type || '').toLowerCase()
  if (kind === 'mobile' || kind === 'tablet' || kind === 'desktop') {
    return kind
  }
  const hint = `${session?.device || ''} ${session?.browser || ''} ${session?.os || ''}`.toLowerCase()
  if (/iphone|ipad|ipod|android|mobile/.test(hint)) return 'mobile'
  if (/ipad|tablet/.test(hint)) return 'tablet'
  return 'desktop'
}

export function formatSessionActivity(dateString) {
  if (!dateString) return 'Never'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}
