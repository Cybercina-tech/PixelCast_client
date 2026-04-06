import { defineStore } from 'pinia'
import { logsAPI } from '../services/api'
import { smartUpdateArray, smartUpdateObject } from '../utils/deepCompare'

export const useLogsStore = defineStore('logs', {
  state: () => ({
    screenStatusLogs: [],
    contentDownloadLogs: [],
    commandExecutionLogs: [],
    summary: {
      screenStatus: null,
      contentDownload: null,
      commandExecution: null,
    },
    loading: false,
    error: null,
    filters: {
      screen_id: null,
      status: null,
      start_date: null,
      end_date: null,
      type: 'all', // 'screen-status', 'content-download', 'command-execution', 'all'
    },
  }),
  actions: {
    async fetchScreenStatusLogs(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.screenStatus.list({ ...this.filters, ...params })
        const newLogs = response.data.results || response.data || []
        
        // Smart update: Only update logs if changed
        this.screenStatusLogs = smartUpdateArray(this.screenStatusLogs || [], newLogs, 'id')
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchScreenStatusLog(id) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.screenStatus.detail(id)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchScreenStatusSummary(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.screenStatus.summary({ ...this.filters, ...params })
        // Backend returns: {status: 'success', summary: {...}}
        this.summary.screenStatus = response.data.summary || response.data
        return response.data.summary || response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchContentDownloadLogs(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.contentDownload.list({ ...this.filters, ...params })
        const newLogs = response.data.results || response.data || []
        
        // Smart update: Only update logs if changed
        this.contentDownloadLogs = smartUpdateArray(this.contentDownloadLogs || [], newLogs, 'id')
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchContentDownloadLog(id) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.contentDownload.detail(id)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchContentDownloadSummary(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.contentDownload.summary({ ...this.filters, ...params })
        // Backend returns: {status: 'success', summary: {...}}
        this.summary.contentDownload = response.data.summary || response.data
        return response.data.summary || response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchCommandExecutionLogs(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.commandExecution.list({ ...this.filters, ...params })
        const newLogs = response.data.results || response.data || []
        
        // Smart update: Only update logs if changed
        this.commandExecutionLogs = smartUpdateArray(this.commandExecutionLogs || [], newLogs, 'id')
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchCommandExecutionLog(id) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.commandExecution.detail(id)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchCommandExecutionSummary(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await logsAPI.commandExecution.summary({ ...this.filters, ...params })
        // Backend returns: {status: 'success', summary: {...}}
        this.summary.commandExecution = response.data.summary || response.data
        return response.data.summary || response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async exportLogs(type, format = 'csv', params = {}) {
      try {
        // Note: This would need to be implemented in backend or use a different approach
        // For now, we'll fetch the data and convert it client-side
        let logs = []
        if (type === 'screen-status') {
          const response = await logsAPI.screenStatus.list({ ...params, page_size: 10000 })
          logs = response.data.results || response.data || []
        } else if (type === 'content-download') {
          const response = await logsAPI.contentDownload.list({ ...params, page_size: 10000 })
          logs = response.data.results || response.data || []
        } else if (type === 'command-execution') {
          const response = await logsAPI.commandExecution.list({ ...params, page_size: 10000 })
          logs = response.data.results || response.data || []
        }
        
        if (format === 'csv') {
          return this.convertToCSV(logs)
        } else {
          return JSON.stringify(logs, null, 2)
        }
      } catch (error) {
        throw error
      }
    },
    convertToCSV(data) {
      if (!data || data.length === 0) return ''
      
      const headers = Object.keys(data[0])
      const csvRows = [
        headers.join(','),
        ...data.map(row => 
          headers.map(header => {
            const value = row[header]
            return typeof value === 'object' ? JSON.stringify(value) : value
          }).join(',')
        ),
      ]
      
      return csvRows.join('\n')
    },
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },
    clearFilters() {
      this.filters = {
        screen_id: null,
        status: null,
        start_date: null,
        end_date: null,
        type: 'all',
      }
    },
  },
})
