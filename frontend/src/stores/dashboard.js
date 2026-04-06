import { defineStore } from 'pinia'
import { screensAPI, commandsAPI, contentsAPI, logsAPI, coreAPI } from '../services/api'
import { smartUpdateObject, smartUpdateArray } from '../utils/deepCompare'
import { hasPermission } from '../utils/permissions'
import { useAuthStore } from './auth'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    stats: {
      online_screens: 0,
      offline_screens: 0,
      commands_in_queue: 0,
      content_downloading: 0,
    },
    metrics: {
      cpu: [],
      memory: [],
      latency: [],
    },
    activities: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchStats() {
      this.loading = true
      this.error = null
      try {
        console.log('DEBUG [fetchStats]: Starting stats fetch...')
        
        // Fetch screens to calculate stats - GLOBAL LIST ONLY (no screen_id)
        let screens = []
        try {
          // Use global list endpoint - no screen_id parameter
          const screensResponse = await screensAPI.list({})
          console.log('DEBUG [fetchStats]: Screens response:', screensResponse.data)
          // Handle different response structures
          if (screensResponse.data?.results && Array.isArray(screensResponse.data.results)) {
            screens = screensResponse.data.results
          } else if (Array.isArray(screensResponse.data)) {
            screens = screensResponse.data
          } else if (screensResponse.data?.data && Array.isArray(screensResponse.data.data)) {
            screens = screensResponse.data.data
          }
          console.log('DEBUG [fetchStats]: Parsed screens:', screens.length)
        } catch (e) {
          // Suppress screen_id errors - these shouldn't happen with list() but catch them anyway
          if (e?.response?.data?.message?.includes('screen_id') || 
              e?.response?.data?.error?.includes('screen_id')) {
            console.debug('DEBUG [fetchStats]: Suppressed screen_id error (unexpected but handled)')
          } else {
            console.error('DEBUG [fetchStats]: Error fetching screens:', e)
          }
        }
        
        // Fetch pending commands - GLOBAL (no screen_id)
        let pendingCommands = []
        try {
          // Use global pending endpoint - no screen_id parameter
          const commandsResponse = await commandsAPI.pending({})
          console.log('DEBUG [fetchStats]: Commands response:', commandsResponse.data)
          // Handle different response structures
          if (commandsResponse.data?.commands && Array.isArray(commandsResponse.data.commands)) {
            pendingCommands = commandsResponse.data.commands
          } else if (commandsResponse.data?.results && Array.isArray(commandsResponse.data.results)) {
            pendingCommands = commandsResponse.data.results
          } else if (Array.isArray(commandsResponse.data)) {
            pendingCommands = commandsResponse.data
          } else if (commandsResponse.data?.data && Array.isArray(commandsResponse.data.data)) {
            pendingCommands = commandsResponse.data.data
          }
          console.log('DEBUG [fetchStats]: Parsed pending commands:', pendingCommands.length)
        } catch (e) {
          // Suppress screen_id errors
          if (e?.response?.data?.message?.includes('screen_id') || 
              e?.response?.data?.error?.includes('screen_id')) {
            console.debug('DEBUG [fetchStats]: Suppressed screen_id error in commands')
          } else {
            console.error('DEBUG [fetchStats]: Error fetching commands:', e)
          }
        }
        
        // Fetch downloading content - GLOBAL LIST (no screen_id)
        let downloadingContent = []
        try {
          // Use global list endpoint with status filter - no screen_id parameter
          let contentsResponse = await contentsAPI.list({ download_status: 'downloading' })
          console.log('DEBUG [fetchStats]: Contents response (downloading):', contentsResponse.data)
          
          // Handle different response structures
          if (contentsResponse.data?.results && Array.isArray(contentsResponse.data.results)) {
            downloadingContent = contentsResponse.data.results
          } else if (Array.isArray(contentsResponse.data)) {
            downloadingContent = contentsResponse.data
          } else if (contentsResponse.data?.data && Array.isArray(contentsResponse.data.data)) {
            downloadingContent = contentsResponse.data.data
          }
          
          // If no results, try 'pending' status
          if (downloadingContent.length === 0) {
            contentsResponse = await contentsAPI.list({ download_status: 'pending' })
            if (contentsResponse.data?.results && Array.isArray(contentsResponse.data.results)) {
              downloadingContent = contentsResponse.data.results.filter(c => 
                c.download_status === 'downloading' || c.download_status === 'pending'
              )
            } else if (Array.isArray(contentsResponse.data)) {
              downloadingContent = contentsResponse.data.filter(c => 
                c.download_status === 'downloading' || c.download_status === 'pending'
              )
            }
          }
          
          console.log('DEBUG [fetchStats]: Parsed downloading content:', downloadingContent.length)
        } catch (e) {
          // Suppress screen_id errors
          if (e?.response?.data?.message?.includes('screen_id') || 
              e?.response?.data?.error?.includes('screen_id')) {
            console.debug('DEBUG [fetchStats]: Suppressed screen_id error in content')
          } else {
            console.error('DEBUG [fetchStats]: Error fetching content:', e)
          }
        }
        
        // Calculate stats
        const onlineScreens = screens.filter(s => s.is_online === true).length
        const offlineScreens = screens.filter(s => s.is_online === false).length
        
        console.log('DEBUG [fetchStats]: Calculated stats:', {
          online_screens: onlineScreens,
          offline_screens: offlineScreens,
          commands_in_queue: pendingCommands.length,
          content_downloading: downloadingContent.length,
        })
        
        // Smart update: Only update stats if values changed
        const newStats = {
          online_screens: onlineScreens,
          offline_screens: offlineScreens,
          commands_in_queue: pendingCommands.length,
          content_downloading: downloadingContent.length,
        }
        this.stats = smartUpdateObject(this.stats, newStats)
        
        console.log('DEBUG [fetchStats]: Final stats:', this.stats)
      } catch (error) {
        console.error('DEBUG [fetchStats]: Error:', error)
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        // Don't reset stats on error - keep previous values
        console.warn('DEBUG [fetchStats]: Error occurred, keeping previous stats')
      } finally {
        this.loading = false
      }
    },
    async fetchMetrics() {
      this.loading = true
      this.error = null
      const authStore = useAuthStore()
      if (!hasPermission(authStore.user, 'view_logs')) {
        this.metrics = { cpu: [], memory: [], latency: [] }
        this.loading = false
        return
      }
      try {
        // Fetch recent screen status logs for metrics
        const response = await logsAPI.screenStatus.list({ page_size: 100 })
        const logs = response.data.results || response.data || []
        
        // Process logs for charts (last 24 hours)
        const now = new Date()
        const last24h = logs
          .filter(log => {
            if (!log.recorded_at) return false
            const logDate = new Date(log.recorded_at)
            return (now - logDate) < 24 * 60 * 60 * 1000
          })
          .sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at))
        
        // Smart update: Only update metrics if data changed
        const newMetrics = {
          cpu: last24h.map(log => ({
            time: log.recorded_at,
            value: log.cpu_usage || 0,
          })),
          memory: last24h.map(log => ({
            time: log.recorded_at,
            value: log.memory_usage || 0,
          })),
          latency: last24h.map(log => ({
            time: log.recorded_at,
            value: log.heartbeat_latency || 0,
          })),
        }
        // Update each metric array only if changed
        this.metrics = {
          cpu: smartUpdateArray(this.metrics.cpu || [], newMetrics.cpu, 'time'),
          memory: smartUpdateArray(this.metrics.memory || [], newMetrics.memory, 'time'),
          latency: smartUpdateArray(this.metrics.latency || [], newMetrics.latency, 'time'),
        }
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        // Set empty metrics on error
        this.metrics = {
          cpu: [],
          memory: [],
          latency: [],
        }
      } finally {
        this.loading = false
      }
    },
    async fetchActivities() {
      this.loading = true
      this.error = null
      try {
        // Fetch recent activities from AuditLog (primary source) and logs
        const activities = []
        
        // Fetch AuditLog entries (comprehensive activity tracking)
        try {
          const auditLogs = await coreAPI.auditLogs.list({ page_size: 20, ordering: '-timestamp' })
          const auditLogsData = auditLogs.data?.results || auditLogs.data || []
          if (Array.isArray(auditLogsData)) {
            auditLogsData.forEach(log => {
              if (log && log.id) {
                // Map audit log action types to activity types
                let activityType = 'update'
                if (log.action_type === 'create') {
                  activityType = log.resource_type === 'Template' ? 'template' : 
                                log.resource_type === 'Screen' ? 'screen' : 'update'
                } else if (log.action_type === 'delete') {
                  activityType = 'alert'
                } else if (log.action_type === 'execute') {
                  activityType = 'command'
                }
                
                activities.push({
                  id: `audit-${log.id}`,
                  type: activityType,
                  message: log.description || `${log.action_type} ${log.resource_type || 'resource'}: ${log.resource_name || 'Unknown'}`,
                  timestamp: log.timestamp || new Date().toISOString(),
                  details: log,
                })
              }
            })
          }
        } catch (e) {
          console.warn('Failed to fetch audit logs, falling back to logs:', e)
        }

        const authStore = useAuthStore()
        const canViewOperationalLogs = hasPermission(authStore.user, 'view_logs')
        
        // Fallback: Recent command executions (if audit logs not available)
        if (canViewOperationalLogs && activities.length < 10) {
          try {
            const cmdLogs = await logsAPI.commandExecution.list({ page_size: 10, ordering: '-created_at' })
            const cmdLogsData = cmdLogs.data.results || cmdLogs.data || []
            if (Array.isArray(cmdLogsData)) {
              cmdLogsData.forEach(log => {
                if (log && log.id) {
                  activities.push({
                    id: `cmd-${log.id}`,
                    type: 'command',
                    message: `Command "${log.command_name || log.command_type_display || log.command_type || 'Unknown'}" ${log.status_display || log.status || 'executed'} on ${log.screen_name || 'Screen'}`,
                    timestamp: log.created_at || log.started_at || new Date().toISOString(),
                    details: log,
                  })
                }
              })
            }
          } catch (e) {
            // Suppress screen_id errors
            if (e?.response?.data?.message?.includes('screen_id') || 
                e?.response?.data?.error?.includes('screen_id')) {
              console.debug('Suppressed screen_id error in command logs')
            } else {
              console.error('Failed to fetch command logs:', e)
            }
          }
        }
        
        // Recent content downloads - GLOBAL (no screen_id)
        if (canViewOperationalLogs && activities.length < 15) {
          try {
            // Use global list endpoint - no screen_id parameter
            const contentLogs = await logsAPI.contentDownload.list({ page_size: 10, ordering: '-created_at' })
            const contentLogsData = contentLogs.data.results || contentLogs.data || []
            if (Array.isArray(contentLogsData)) {
              contentLogsData.forEach(log => {
                if (log && log.id) {
                  activities.push({
                    id: `content-${log.id}`,
                    type: 'content',
                    message: `Content "${log.content_name || 'Unknown'}" ${log.status_display || log.status || 'downloaded'} on ${log.screen_name || 'Screen'}`,
                    timestamp: log.created_at || log.downloaded_at || new Date().toISOString(),
                    details: log,
                  })
                }
              })
            }
          } catch (e) {
            // Suppress screen_id errors
            if (e?.response?.data?.message?.includes('screen_id') || 
                e?.response?.data?.error?.includes('screen_id')) {
              console.debug('Suppressed screen_id error in content logs')
            } else {
              console.error('Failed to fetch content logs:', e)
            }
          }
        }
        
        // Recent screen status changes - GLOBAL (no screen_id filter)
        if (canViewOperationalLogs && activities.length < 20) {
          try {
            // Use global list endpoint - no screen_id parameter
            const statusLogs = await logsAPI.screenStatus.list({ page_size: 10, ordering: '-recorded_at' })
            const statusLogsData = statusLogs.data.results || statusLogs.data || []
            if (Array.isArray(statusLogsData)) {
              // Group by screen and only show status changes
              const screenStatusMap = new Map()
              statusLogsData.forEach(log => {
                if (log && log.id && log.screen_id) {
                  const key = log.screen_id
                  if (!screenStatusMap.has(key) || screenStatusMap.get(key).recorded_at < log.recorded_at) {
                    screenStatusMap.set(key, log)
                  }
                }
              })
              
              screenStatusMap.forEach(log => {
                activities.push({
                  id: `status-${log.id}`,
                  type: 'screen',
                  message: `Screen "${log.screen_name || 'Unknown'}" is now ${log.status_display || log.status || 'online'}`,
                  timestamp: log.recorded_at || new Date().toISOString(),
                  details: log,
                })
              })
            }
          } catch (e) {
            // Suppress screen_id errors
            if (e?.response?.data?.message?.includes('screen_id') || 
                e?.response?.data?.error?.includes('screen_id')) {
              console.debug('Suppressed screen_id error in status logs')
            } else {
              console.error('Failed to fetch status logs:', e)
            }
          }
        }
        
        // Sort by timestamp (most recent first) and take top 20
        const newActivities = activities
          .filter(activity => activity.timestamp) // Only include activities with valid timestamps
          .sort((a, b) => {
            const dateA = new Date(a.timestamp)
            const dateB = new Date(b.timestamp)
            return dateB - dateA // Most recent first
          })
          .slice(0, 20)
        
        // Smart update: Only update activities array if changed
        this.activities = smartUpdateArray(this.activities || [], newActivities, 'id')
        
        console.log(`Loaded ${this.activities.length} recent activities`)
      } catch (error) {
        console.error('Error fetching activities:', error)
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        this.activities = []
      } finally {
        this.loading = false
      }
    },
  },
})
