/**
 * Public deployment flags from the API (no auth). Used for client vs SaaS UI.
 */
import { setDeploymentFlags } from './permissions'

let loadPromise = null

/**
 * Fetch once and sync permission helpers. Safe to call multiple times.
 * @returns {Promise<object>}
 */
export function fetchDeploymentConfig() {
  if (loadPromise) {
    return loadPromise
  }
  loadPromise = fetch('/api/public/deployment/', { credentials: 'same-origin' })
    .then((r) => (r.ok ? r.json() : {}))
    .then((data) => {
      setDeploymentFlags(data || {})
      return data || {}
    })
    .catch(() => {
      setDeploymentFlags({})
      return {}
    })
  return loadPromise
}
