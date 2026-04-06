import { defineStore } from 'pinia'
import { notificationCenterAPI } from '@/services/api'

export const useNotificationsStore = defineStore('notifications', {
  state: () => ({
    notifications: [],
    loading: false,
    error: null,
    lastFetchTime: null,
    pollingInterval: null,
  }),

  getters: {
    unreadCount: (state) => {
      return state.notifications.filter(n => !n.is_read).length
    },
    
    unreadNotifications: (state) => {
      return state.notifications.filter(n => !n.is_read)
    },
    
    readNotifications: (state) => {
      return state.notifications.filter(n => n.is_read)
    },
  },

  actions: {
    /**
     * Fetch notifications from the backend
     */
    async fetchNotifications(limit = 25) {
      this.loading = true
      this.error = null
      
      try {
        const response = await notificationCenterAPI.list({ limit })
        
        if (response.data.status === 'success' && Array.isArray(response.data.notifications)) {
          this.notifications = response.data.notifications
          this.lastFetchTime = new Date()
        } else {
          // Fallback: handle different response structures
          this.notifications = response.data.notifications || response.data.results || response.data || []
        }
        
        return this.notifications
      } catch (error) {
        console.error('Failed to fetch notifications:', error)
        this.error = error.response?.data?.error || error.message || 'Failed to fetch notifications'
        // Don't throw, just log the error
        return []
      } finally {
        this.loading = false
      }
    },

    /**
     * Mark a notification as read
     */
    async markAsRead(notificationId) {
      try {
        const response = await notificationCenterAPI.markAsRead(notificationId)
        
        // Update local state
        const notification = this.notifications.find(n => n.id === notificationId)
        if (notification) {
          notification.is_read = true
        }
        
        return response.data
      } catch (error) {
        console.error('Failed to mark notification as read:', error)
        // Update local state anyway for better UX
        const notification = this.notifications.find(n => n.id === notificationId)
        if (notification) {
          notification.is_read = true
        }
        throw error
      }
    },

    /**
     * Mark all notifications as read
     */
    async markAllAsRead() {
      try {
        const response = await notificationCenterAPI.markAllAsRead()
        
        // Update local state
        this.notifications.forEach(n => {
          n.is_read = true
        })
        
        return response.data
      } catch (error) {
        console.error('Failed to mark all notifications as read:', error)
        // Update local state anyway for better UX
        this.notifications.forEach(n => {
          n.is_read = true
        })
        throw error
      }
    },

    /**
     * Dismiss a single notification
     */
    async dismiss(notificationId) {
      await notificationCenterAPI.dismiss(notificationId)
      this.notifications = this.notifications.filter((n) => n.id !== notificationId)
    },

    /**
     * Clear all notifications
     */
    async clearAll() {
      await notificationCenterAPI.clear()
      this.notifications = []
    },

    /**
     * Start polling for new notifications
     */
    startPolling(intervalMs = 30000) {
      // Clear existing interval if any
      this.stopPolling()
      
      // Fetch immediately
      this.fetchNotifications()
      
      // Set up polling
      this.pollingInterval = setInterval(() => {
        this.fetchNotifications()
      }, intervalMs)
    },

    /**
     * Stop polling for notifications
     */
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
    },

    /**
     * Clear all notifications from store
     */
    clear() {
      this.notifications = []
      this.error = null
    },
  },
})

