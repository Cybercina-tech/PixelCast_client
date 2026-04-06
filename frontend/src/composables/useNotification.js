/**
 * Notification Composable
 * 
 * Provides a simple, clean API for showing notifications from any component.
 * 
 * @example
 * ```javascript
 * import { useNotification } from '@/composables/useNotification'
 * 
 * const notify = useNotification()
 * 
 * // Simple usage
 * notify.success('Operation completed!')
 * notify.error('Something went wrong')
 * 
 * // Advanced usage
 * notify.show({
 *   message: 'File uploaded successfully',
 *   type: 'success',
 *   title: 'Upload Complete',
 *   duration: 3000,
 *   action: {
 *     label: 'View',
 *     handler: () => router.push('/files')
 *   }
 * })
 * ```
 */

import { useNotificationStore } from '@/stores/notification'

export function useNotification() {
  const store = useNotificationStore()

  return {
    /**
     * Show a notification
     * @param {string|Object} messageOrOptions - Message string or options object
     * @param {Object} options - Additional options (if first param is string)
     */
    show(messageOrOptions, options = {}) {
      if (typeof messageOrOptions === 'string') {
        return store.show({
          message: messageOrOptions,
          ...options,
        })
      }
      return store.show(messageOrOptions)
    },

    /**
     * Show success notification
     */
    success(message, options = {}) {
      return store.success(message, options)
    },

    /**
     * Show error notification
     */
    error(message, options = {}) {
      return store.error(message, options)
    },

    /**
     * Show warning notification
     */
    warning(message, options = {}) {
      return store.warning(message, options)
    },

    /**
     * Show info notification
     */
    info(message, options = {}) {
      return store.info(message, options)
    },

    /**
     * Remove notification by ID
     */
    remove(id) {
      return store.remove(id)
    },

    /**
     * Clear all notifications
     */
    clear() {
      return store.clear()
    },

    /**
     * Set notification position
     */
    setPosition(position) {
      return store.setPosition(position)
    },
  }
}

/**
 * Global notification helper (for use outside components)
 * Can be imported and used in stores, utilities, etc.
 */
let globalNotificationInstance = null

export function getNotification() {
  if (!globalNotificationInstance) {
    // This will be initialized when store is created
    // For now, return a proxy that will work once store is available
    const store = useNotificationStore()
    globalNotificationInstance = {
      show: (options) => store.show(options),
      success: (message, options) => store.success(message, options),
      error: (message, options) => store.error(message, options),
      warning: (message, options) => store.warning(message, options),
      info: (message, options) => store.info(message, options),
      remove: (id) => store.remove(id),
      clear: () => store.clear(),
      setPosition: (position) => store.setPosition(position),
    }
  }
  return globalNotificationInstance
}

