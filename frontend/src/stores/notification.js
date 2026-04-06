import { defineStore } from 'pinia'

/**
 * Professional Notification Store
 * 
 * Features:
 * - Multiple notification types (success, error, warning, info)
 * - Auto-dismiss with configurable duration
 * - Manual close support
 * - Clickable actions
 * - Stack management (no overlapping)
 * - Position control (top-right, top-left, bottom-right, bottom-left)
 */
export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [],
    position: 'top-right', // top-right, top-left, bottom-right, bottom-left
    maxNotifications: 5, // Maximum number of visible notifications
  }),

  getters: {
    visibleNotifications(state) {
      // Return a reactive slice of notifications
      return state.notifications.slice(0, state.maxNotifications)
    },
  },

  actions: {
    /**
     * Show a notification
     * @param {Object} options - Notification options
     * @param {string} options.message - Notification message (required)
     * @param {string} options.type - Notification type: 'success' | 'error' | 'warning' | 'info' (default: 'info')
     * @param {number} options.duration - Auto-dismiss duration in ms (0 = no auto-dismiss, default: 5000)
     * @param {string} options.title - Optional title
     * @param {Object} options.action - Optional action button { label: string, handler: function }
     * @param {boolean} options.persistent - If true, notification won't auto-dismiss (default: false)
     * @returns {string} Notification ID
     */
    show(options) {
      if (typeof options === 'string') {
        // Backward compatibility: if string is passed, treat as message
        options = { message: options }
      }

      const {
        message,
        type = 'info',
        duration = 5000,
        title = null,
        action = null,
        persistent = false,
      } = options

      if (!message) {
        console.warn('Notification: message is required')
        return null
      }

      const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      const notification = {
        id,
        message,
        type,
        duration: persistent ? 0 : duration,
        title,
        action,
        timestamp: Date.now(),
        visible: true,
      }

      // Add to beginning of array (newest first)
      // Use array spread to ensure reactivity
      this.notifications = [notification, ...this.notifications]

      // Remove oldest if exceeding max
      if (this.notifications.length > this.maxNotifications * 2) {
        this.notifications = this.notifications.slice(0, this.maxNotifications)
      }

      return id
    },

    /**
     * Show success notification
     */
    success(message, options = {}) {
      return this.show({
        message,
        type: 'success',
        ...options,
      })
    },

    /**
     * Show error notification
     */
    error(message, options = {}) {
      return this.show({
        message,
        type: 'error',
        duration: 7000, // Errors stay longer
        ...options,
      })
    },

    /**
     * Show warning notification
     */
    warning(message, options = {}) {
      return this.show({
        message,
        type: 'warning',
        duration: 6000,
        ...options,
      })
    },

    /**
     * Show info notification
     */
    info(message, options = {}) {
      return this.show({
        message,
        type: 'info',
        ...options,
      })
    },

    /**
     * Remove a notification by ID
     */
    remove(id) {
      const index = this.notifications.findIndex(n => n.id === id)
      if (index !== -1) {
        this.notifications.splice(index, 1)
      }
    },

    /**
     * Clear all notifications
     */
    clear() {
      this.notifications = []
    },

    /**
     * Update notification position
     */
    setPosition(position) {
      const validPositions = ['top-right', 'top-left', 'bottom-right', 'bottom-left']
      if (validPositions.includes(position)) {
        this.position = position
      }
    },
  },
})

