import { defineStore } from 'pinia'
import { usersAPI } from '../services/api'
import { smartUpdateArray } from '../utils/deepCompare'

export const useSidebarStore = defineStore('sidebar', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
    lastFetched: null,
    fetchPromise: null,
  }),
  actions: {
    async fetchSidebarItems(options = {}) {
      const { force = false, minIntervalMs = 5000 } = options

      if (this.fetchPromise) {
        return this.fetchPromise
      }

      if (!force && this.lastFetched) {
        const elapsed = Date.now() - new Date(this.lastFetched).getTime()
        if (elapsed < minIntervalMs) {
          return this.items
        }
      }

      this.loading = true
      this.error = null

      this.fetchPromise = (async () => {
        try {
          const response = await usersAPI.sidebarItems()
          const newItems = response.data.items || []

          // Smart update: Only update sidebar items if changed
          // This prevents re-triggering entrance animations
          this.items = smartUpdateArray(this.items || [], newItems, 'id')
          this.lastFetched = new Date()
          return this.items
        } catch (error) {
          this.error = error.response?.data?.detail || error.message || 'Failed to load sidebar items'
          console.error('Failed to fetch sidebar items:', error)
          // Return empty array on error to prevent breaking the UI
          this.items = []
          return []
        } finally {
          this.loading = false
          this.fetchPromise = null
        }
      })()

      return this.fetchPromise
    },
    clearSidebarItems() {
      this.items = []
      this.lastFetched = null
      this.fetchPromise = null
    },
  },
  getters: {
    hasItems: (state) => state.items.length > 0,
    // Get items that should be visible (no children or has accessible children)
    visibleItems: (state) => {
      return state.items.filter(item => {
        // If item has children, only show if at least one child is accessible
        if (item.children && item.children.length > 0) {
          return true // Children filtering is done in the component
        }
        // If no children, show the item
        return true
      })
    },
  },
})

