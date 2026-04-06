import { defineStore } from 'pinia'
import { coreAPI } from '../services/api'
import { useNotificationStore } from './notification'

export const useCoreStore = defineStore('core', {
  state: () => ({
    // Audit Logs
    auditLogs: [],
    auditLogSummary: null,
    auditLogFilters: {
      action_type: null,
      resource_type: null,
      severity: null,
      success: null,
      start_date: null,
      end_date: null,
      search: null,
    },
    
    // Backups
    backups: [],
    currentBackup: null,
    
    loading: false,
    error: null,
  }),
  
  actions: {
    // ===== Audit Logs =====
    async fetchAuditLogs(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await coreAPI.auditLogs.list({ ...this.auditLogFilters, ...params })
        this.auditLogs = response.data.results || response.data || []
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        const notifyStore = useNotificationStore()
        notifyStore.error(this.error || 'Failed to fetch audit logs')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchAuditLog(id) {
      this.loading = true
      this.error = null
      try {
        const response = await coreAPI.auditLogs.detail(id)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        const notifyStore = useNotificationStore()
        notifyStore.error(this.error || 'Failed to fetch audit log')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchAuditLogSummary(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await coreAPI.auditLogs.summary({ ...this.auditLogFilters, ...params })
        this.auditLogSummary = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    setAuditLogFilters(filters) {
      this.auditLogFilters = { ...this.auditLogFilters, ...filters }
    },
    
    clearAuditLogFilters() {
      this.auditLogFilters = {
        action_type: null,
        resource_type: null,
        severity: null,
        success: null,
        start_date: null,
        end_date: null,
        search: null,
      }
    },
    
    // ===== Backups =====
    async fetchBackups(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await coreAPI.backups.list(params)
        this.backups = response.data.results || response.data || []
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        const notifyStore = useNotificationStore()
        notifyStore.error(this.error || 'Failed to fetch backups')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchBackup(id) {
      this.loading = true
      this.error = null
      try {
        const response = await coreAPI.backups.detail(id)
        this.currentBackup = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        const notifyStore = useNotificationStore()
        notifyStore.error(this.error || 'Failed to fetch backup')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async triggerBackup(backupType, options = {}) {
      this.loading = true
      this.error = null
      const notifyStore = useNotificationStore()
      try {
        const response = await coreAPI.backups.trigger({
          backup_type: backupType,
          compression: options.compression !== false,
          include_media: options.include_media || false,
        })
        notifyStore.success('Backup triggered successfully')
        // Refresh backups list
        await this.fetchBackups()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        notifyStore.error(this.error || 'Failed to trigger backup')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async verifyBackup(id) {
      this.loading = true
      this.error = null
      const notifyStore = useNotificationStore()
      try {
        const response = await coreAPI.backups.verify(id)
        const isValid = response.data.is_valid
        if (isValid) {
          notifyStore.success('Backup verification passed')
        } else {
          notifyStore.error('Backup verification failed')
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        notifyStore.error(this.error || 'Failed to verify backup')
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async cleanupBackups() {
      this.loading = true
      this.error = null
      const notifyStore = useNotificationStore()
      try {
        const response = await coreAPI.backups.cleanup()
        const deletedCount = response.data.deleted_count || 0
        notifyStore.success(`Cleaned up ${deletedCount} expired backups`)
        // Refresh backups list
        await this.fetchBackups()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        notifyStore.error(this.error || 'Failed to cleanup backups')
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
