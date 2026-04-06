import { defineStore } from 'pinia'
import { schedulesAPI } from '../services/api'
import { normalizeApiError } from '../utils/apiError'

export const useSchedulesStore = defineStore('schedules', {
  state: () => ({
    schedules: [],
    currentSchedule: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      is_active: null,
      template: null,
    },
  }),
  getters: {
    activeSchedules: (state) => state.schedules.filter(s => s.is_active),
    filteredSchedules: (state) => {
      let filtered = state.schedules
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(s => 
          s.name?.toLowerCase().includes(search) ||
          s.description?.toLowerCase().includes(search)
        )
      }
      if (state.filters.is_active !== null) {
        filtered = filtered.filter(s => s.is_active === state.filters.is_active)
      }
      if (state.filters.template) {
        filtered = filtered.filter(s => s.template === state.filters.template)
      }
      return filtered
    },
  },
  actions: {
    async fetchSchedules(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.list({ ...this.filters, ...params })
        this.schedules = response.data.results || response.data || []
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchSchedule(id) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.detail(id)
        this.currentSchedule = response.data
        // Update in list if exists
        const index = this.schedules.findIndex(s => s.id === id)
        if (index !== -1) {
          this.schedules[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async createSchedule(data) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.create(data)
        this.schedules.push(response.data)
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async updateSchedule(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.update(id, data)
        const index = this.schedules.findIndex(s => s.id === id)
        if (index !== -1) {
          this.schedules[index] = response.data
        }
        if (this.currentSchedule?.id === id) {
          this.currentSchedule = response.data
        }
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async deleteSchedule(id) {
      this.loading = true
      this.error = null
      try {
        await schedulesAPI.delete(id)
        this.schedules = this.schedules.filter(s => s.id !== id)
        if (this.currentSchedule?.id === id) {
          this.currentSchedule = null
        }
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async executeSchedule(id, force = false) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.execute(id, { force })
        // Update schedule status
        const index = this.schedules.findIndex(s => s.id === id)
        if (index !== -1) {
          this.schedules[index] = { ...this.schedules[index], ...response.data }
        }
        if (this.currentSchedule?.id === id) {
          this.currentSchedule = { ...this.currentSchedule, ...response.data }
        }
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchDueSchedules(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.dueSchedules(params)
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchConflicting(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await schedulesAPI.conflicting(params)
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
  },
})
