/**
 * Google Tag Manager / Google Ads dataLayer helpers (SPA-safe).
 */

export function initDataLayer() {
  if (typeof window === 'undefined') return
  window.dataLayer = window.dataLayer || []
}

/**
 * @param {string} eventName
 * @param {Record<string, unknown>} [params]
 */
export function pushDataLayerEvent(eventName, params = {}) {
  initDataLayer()
  window.dataLayer.push({
    event: eventName,
    ...params,
  })
}

/**
 * Virtual page views for SPA route changes (map to GA4 page_view in GTM).
 */
export function pushVirtualPageView(to) {
  initDataLayer()
  const title = typeof document !== 'undefined' ? document.title : ''
  window.dataLayer.push({
    event: 'virtual_page_view',
    page_path: to.fullPath,
    page_title: title,
    page_location:
      typeof window !== 'undefined' ? `${window.location.origin}${to.fullPath}` : '',
  })
}

export function pushCtaClick(ctaId, label, extra = {}) {
  pushDataLayerEvent('cta_click', {
    cta_id: ctaId,
    cta_label: label,
    ...extra,
  })
}

export function pushSignUp(method = 'email') {
  pushDataLayerEvent('sign_up', { method })
}

export function pushLogin(method = 'password') {
  pushDataLayerEvent('login', { method })
}
