import { initDataLayer } from './dataLayer'

const GTM_ID_RE = /^GTM-[A-Z0-9]+$/i

/**
 * Initialise dataLayer and inject GTM when `VITE_GTM_CONTAINER_ID` is a valid GTM- ID.
 */
export function bootGtm(containerId) {
  initDataLayer()
  const id = (containerId || '').trim()
  if (!id || !GTM_ID_RE.test(id)) {
    return
  }
  if (typeof document === 'undefined') return
  if (document.getElementById('gtm-script')) return

  const script = document.createElement('script')
  script.id = 'gtm-script'
  script.async = true
  script.src = `https://www.googletagmanager.com/gtm.js?id=${id}`
  document.head.appendChild(script)

  const noscript = document.createElement('noscript')
  noscript.innerHTML = `<iframe src="https://www.googletagmanager.com/ns.html?id=${id}" height="0" width="0" style="display:none;visibility:hidden" title="Google Tag Manager"></iframe>`
  document.body.insertBefore(noscript, document.body.firstChild)
}
