import { defineStore } from 'pinia'
import { screensAPI } from '../services/api'
import { smartUpdateArray, smartUpdateObject, deepEqual } from '../utils/deepCompare'
import { normalizeApiError } from '../utils/apiError'

export const useScreensStore = defineStore('screens', {
  state: () => ({
    screens: [],
    currentScreen: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      status: null,
      organization: null,
    },
  }),
  getters: {
    onlineScreens: (state) => state.screens.filter(s => s.is_online),
    offlineScreens: (state) => state.screens.filter(s => !s.is_online),
    filteredScreens: (state) => {
      let filtered = state.screens
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(s => 
          s.name?.toLowerCase().includes(search) ||
          s.device_id?.toLowerCase().includes(search) ||
          s.location?.toLowerCase().includes(search)
        )
      }
      if (state.filters.status === 'online') {
        filtered = filtered.filter(s => s.is_online)
      } else if (state.filters.status === 'offline') {
        filtered = filtered.filter(s => !s.is_online)
      }
      return filtered
    },
    /**
     * Get screen status display: 'connecting', 'online', or 'offline'
     * Shows 'connecting' for screens created < 1 minute ago without heartbeat
     */
    getScreenStatus: (state) => (screen) => {
      if (!screen) {
        console.log('DEBUG [getScreenStatus]: Screen is null/undefined')
        return 'offline'
      }
      
      // DEBUG: Log screen status check
      console.log(`DEBUG [getScreenStatus]: Checking status for screen "${screen.name || screen.id}"`, {
        is_online: screen.is_online,
        created_at: screen.created_at,
        last_heartbeat_at: screen.last_heartbeat_at,
        _isNew: screen._isNew,
        _createdAt: screen._createdAt,
      })
      
      // If screen is online, return online
      if (screen.is_online) {
        console.log('DEBUG [getScreenStatus]: Screen is online')
        return 'online'
      }
      
      // Check if screen was created recently (< 1 minute ago) and has no heartbeat
      const createdDateStr = screen._createdAt || screen.created_at
      if (createdDateStr) {
        const createdDate = new Date(createdDateStr)
        const now = new Date()
        const ageMinutes = (now - createdDate) / (1000 * 60)
        
        console.log(`DEBUG [getScreenStatus]: Screen age: ${ageMinutes.toFixed(2)} minutes, has heartbeat: ${!!screen.last_heartbeat_at}`)
        
        // If created < 1 minute ago and no heartbeat, show "connecting"
        if (ageMinutes < 1 && !screen.last_heartbeat_at) {
          console.log('DEBUG [getScreenStatus]: Screen is connecting (new, no heartbeat)')
          return 'connecting'
        }
      } else {
        console.log('DEBUG [getScreenStatus]: No created_at or _createdAt found')
      }
      
      // Default to offline
      console.log('DEBUG [getScreenStatus]: Screen is offline')
      return 'offline'
    },
  },
  actions: {
    async fetchScreens(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await screensAPI.list({ ...this.filters, ...params })
        const newScreens = response.data.results || response.data || []
        
        // Smart update: Fine-grained patching - only update changed screens
        this.screens = smartUpdateArray(this.screens || [], newScreens, 'id')
        
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchScreen(id) {
      this.loading = true
      this.error = null
      try {
        const response = await screensAPI.detail(id)
        const newScreen = response.data
        
        // Smart update: Only update if screen data changed
        this.currentScreen = smartUpdateObject(this.currentScreen, newScreen)
        
        // Update in list if exists (fine-grained patch)
        const index = this.screens.findIndex(s => s.id === id)
        if (index !== -1) {
          // Only update if data actually changed
          if (!deepEqual(this.screens[index], newScreen)) {
            this.screens[index] = smartUpdateObject(this.screens[index], newScreen)
          }
        }
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async createScreen(data) {
      this.loading = true
      this.error = null
      try {
        const response = await screensAPI.create(data)
        const newScreen = response.data
        
        // Optimistic UI: Add screen with "Connecting" state
        // Mark as newly created for status display logic
        const optimisticScreen = {
          ...newScreen,
          is_online: false, // Will be updated when first heartbeat arrives
          _isNew: true, // Flag to indicate this is a new screen
          _createdAt: new Date().toISOString(), // Store creation time
        }
        
        this.screens.push(optimisticScreen)
        
        // Immediately fetch the latest status (in case heartbeat already arrived)
        // Don't await - let it update in background
        this.fetchSingleScreenStatus(newScreen.id).catch(err => {
          console.warn('Failed to fetch initial screen status:', err)
        })
        
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    /**
     * Fetch status for a single screen without re-fetching entire list
     * Useful for newly added screens or real-time updates
     */
    async fetchSingleScreenStatus(screenId) {
      try {
        const response = await screensAPI.detail(screenId)
        const updatedScreen = response.data
        
        // Update in list if exists
        const index = this.screens.findIndex(s => s.id === screenId)
        if (index !== -1) {
          // Preserve _isNew flag if screen was just created
          const existingScreen = this.screens[index]
          const merged = {
            ...updatedScreen,
            _isNew: existingScreen._isNew,
            _createdAt: existingScreen._createdAt || existingScreen.created_at,
          }
          
          // Only update if data actually changed
          if (!deepEqual(this.screens[index], merged)) {
            this.screens[index] = smartUpdateObject(this.screens[index], merged)
          }
        } else {
          // Screen not in list, add it
          this.screens.push(updatedScreen)
        }
        
        // Update currentScreen if it's the one we're fetching
        if (this.currentScreen?.id === screenId) {
          this.currentScreen = smartUpdateObject(this.currentScreen, updatedScreen)
        }
        
        return updatedScreen
      } catch (error) {
        console.error(`Failed to fetch status for screen ${screenId}:`, error)
        throw error
      }
    },
    async updateScreen(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await screensAPI.update(id, data)
        const updatedScreen = response.data
        
        // Smart update: Fine-grained patch
        const index = this.screens.findIndex(s => s.id === id)
        if (index !== -1) {
          // Only update if data changed
          if (!deepEqual(this.screens[index], updatedScreen)) {
            this.screens[index] = smartUpdateObject(this.screens[index], updatedScreen)
          }
        }
        if (this.currentScreen?.id === id) {
          this.currentScreen = smartUpdateObject(this.currentScreen, updatedScreen)
        }
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async deleteScreen(id) {
      this.loading = true
      this.error = null
      try {
        await screensAPI.delete(id)
        this.screens = this.screens.filter(s => s.id !== id)
        if (this.currentScreen?.id === id) {
          this.currentScreen = null
        }
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async sendHeartbeat(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await screensAPI.heartbeat(id, data)
        const updatedData = response.data
        
        // Smart update: Only update changed properties (e.g., is_online, last_heartbeat_at)
        const index = this.screens.findIndex(s => s.id === id)
        if (index !== -1) {
          // Merge only changed properties
          const merged = { ...this.screens[index], ...updatedData }
          // Only update if something actually changed
          if (!deepEqual(this.screens[index], merged)) {
            this.screens[index] = smartUpdateObject(this.screens[index], merged)
          }
        }
        if (this.currentScreen?.id === id) {
          const merged = { ...this.currentScreen, ...updatedData }
          if (!deepEqual(this.currentScreen, merged)) {
            this.currentScreen = smartUpdateObject(this.currentScreen, merged)
          }
        }
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },
    clearFilters() {
      this.filters = { search: '', status: null, organization: null }
    },
    /**
     * Handle WebSocket screen status update
     * Called when backend broadcasts a screen status change
     */
    handleScreenStatusUpdate(screenData) {
      if (!screenData || !screenData.id) {
        console.warn('Invalid screen status update data:', screenData)
        return
      }
      
      const screenId = screenData.id
      const index = this.screens.findIndex(s => s.id === screenId)
      
      if (index !== -1) {
        // Update existing screen with new status
        const updatedScreen = {
          ...this.screens[index],
          ...screenData,
          // Preserve _isNew flag if screen was just created
          _isNew: this.screens[index]._isNew,
        }
        
        // Only update if data actually changed
        if (!deepEqual(this.screens[index], updatedScreen)) {
          this.screens[index] = smartUpdateObject(this.screens[index], updatedScreen)
        }
      } else {
        // Screen not in list, add it
        this.screens.push(screenData)
      }
      
      // Update currentScreen if it's the one being updated
      if (this.currentScreen?.id === screenId) {
        this.currentScreen = smartUpdateObject(this.currentScreen, screenData)
      }
    },
  },
})
