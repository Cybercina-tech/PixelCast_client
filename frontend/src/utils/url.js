/**
 * URL helpers for media and API-relative resolution.
 */
import { resolveMediaFileUrl, getBackendOrigin } from './mediaUrl'

export { getBackendOrigin }

/** Site origin for media (matches Vite proxy / direct API host). */
export const MEDIA_BASE_URL = import.meta.env.VITE_MEDIA_BASE_URL || getBackendOrigin()

/**
 * Ensure URL is absolute for <img> / <video> (same rules as resolveMediaFileUrl).
 * @deprecated Prefer importing resolveMediaFileUrl from '@/utils/mediaUrl' directly.
 */
export function ensureAbsoluteUrl(url) {
  return resolveMediaFileUrl(url)
}

/**
 * Prefer serializer fields in order suitable for API content objects.
 */
export function getContentFileUrl(content) {
  if (!content) {
    return null
  }
  if (content.absolute_file_url) {
    return resolveMediaFileUrl(content.absolute_file_url)
  }
  if (content.secure_url) {
    return resolveMediaFileUrl(content.secure_url)
  }
  if (content.file_url) {
    return resolveMediaFileUrl(content.file_url)
  }
  return null
}
