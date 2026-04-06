/**
 * Analytics Store
 * Manages analytics data and statistics
 */
import { defineStore } from 'pinia'
import { analyticsAPI } from '../services/api'

export const useAnalyticsStore = defineStore('analytics', {
  state: () => ({
    screenStats: null,
    screenDetails: {},
    commandStats: null,
    contentStats: null,
    templateStats: null,
    activityTrends: null,
    loading: false,
    error: null,
    filters: {
      start_date: null,
      end_date: null,
      screen_ids: null,
      period: 'day',
      days: 30,
    },
  }),

  getters: {
    hasScreenStats: (state) => state.screenStats !== null,
    hasCommandStats: (state) => state.commandStats !== null,
    hasContentStats: (state) => state.contentStats !== null,
    hasTemplateStats: (state) => state.templateStats !== null,
    hasActivityTrends: (state) => state.activityTrends !== null,
  },

  actions: {
    /**
     * Fetch screen statistics
     */
    async fetchScreenStatistics(params = {}) {
      this.loading = true
      this.error = null
      try {
        const queryParams = {
          ...this.filters,
          ...params,
        }
        // Remove null/undefined values
        Object.keys(queryParams).forEach(key => {
          if (queryParams[key] === null || queryParams[key] === undefined) {
            delete queryParams[key]
          }
        })
        // Convert screen_ids array to comma-separated string
        if (queryParams.screen_ids && Array.isArray(queryParams.screen_ids)) {
          queryParams.screen_ids = queryParams.screen_ids.join(',')
        }

        const response = await analyticsAPI.screenStatistics(queryParams)
        this.screenStats = response.data.data || response.data
        return this.screenStats
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch detailed statistics for a specific screen
     */
    async fetchScreenDetail(screenId, params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await analyticsAPI.screenDetail(screenId)
        this.screenDetails[screenId] = response.data.data || response.data
        return this.screenDetails[screenId]
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || error.message
        if (error.response?.status === 404) {
          this.screenDetails[screenId] = null
        }
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch command statistics
     */
    async fetchCommandStatistics(params = {}) {
      this.loading = true
      this.error = null
      try {
        const queryParams = {
          ...this.filters,
          ...params,
        }
        // Remove null/undefined values
        Object.keys(queryParams).forEach(key => {
          if (queryParams[key] === null || queryParams[key] === undefined) {
            delete queryParams[key]
          }
        })
        // Convert screen_ids array to comma-separated string
        if (queryParams.screen_ids && Array.isArray(queryParams.screen_ids)) {
          queryParams.screen_ids = queryParams.screen_ids.join(',')
        }

        const response = await analyticsAPI.commandStatistics(queryParams)
        this.commandStats = response.data.data || response.data
        return this.commandStats
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch content statistics
     */
    async fetchContentStatistics(params = {}) {
      this.loading = true
      this.error = null
      try {
        const queryParams = {
          ...this.filters,
          ...params,
        }
        // Remove null/undefined values
        Object.keys(queryParams).forEach(key => {
          if (queryParams[key] === null || queryParams[key] === undefined) {
            delete queryParams[key]
          }
        })

        const response = await analyticsAPI.contentStatistics(queryParams)
        this.contentStats = response.data.data || response.data
        return this.contentStats
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch template statistics
     */
    async fetchTemplateStatistics(params = {}) {
      this.loading = true
      this.error = null
      try {
        const queryParams = {
          ...this.filters,
          ...params,
        }
        // Remove null/undefined values
        Object.keys(queryParams).forEach(key => {
          if (queryParams[key] === null || queryParams[key] === undefined) {
            delete queryParams[key]
          }
        })

        const response = await analyticsAPI.templateStatistics(queryParams)
        this.templateStats = response.data.data || response.data
        return this.templateStats
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch activity trends
     */
    async fetchActivityTrends(params = {}) {
      this.loading = true
      this.error = null
      try {
        const queryParams = {
          period: this.filters.period || 'day',
          days: this.filters.days || 30,
          ...params,
        }

        const response = await analyticsAPI.activityTrends(queryParams)
        this.activityTrends = response.data.data || response.data
        return this.activityTrends
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Set filters
     */
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * Clear filters
     */
    clearFilters() {
      this.filters = {
        start_date: null,
        end_date: null,
        screen_ids: null,
        period: 'day',
        days: 30,
      }
    },

    /**
     * Reset store state
     */
    reset() {
      this.screenStats = null
      this.screenDetails = {}
      this.commandStats = null
      this.contentStats = null
      this.templateStats = null
      this.activityTrends = null
      this.error = null
      this.clearFilters()
    },
  },
})
