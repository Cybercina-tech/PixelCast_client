import { defineStore } from 'pinia'
import playerAPI from '@/services/playerApi'
import { collectSystemInfo } from '@/composables/useSystemInfo'

const STORAGE_KEYS = {
  identities: 'player_identities',
  screenId: 'player_screen_id',
  deviceToken: 'player_device_token',
  isPaired: 'player_is_paired',
  pairedAt: 'player_paired_at',
}

export const usePlayerStore = defineStore('player', {
  state: () => ({
    status: 'loading', // loading | success | no_template | error | unpaired
    template: null,
    errorMessage: null,
    retryCountdown: 0,
    overlayMessage: null,
    overlayVisible: false,
    overlayTimer: null,
    pollingInterval: null,
    heartbeatInterval: null,
    commandPollingInterval: null,
    retryTimer: null,
    lastSuccessfulHeartbeat: null,
    connectionLostTimer: null,
    activeScreenId: null,
    /** Difference serverNow - deviceNow from HTTP Date header on template fetch (ms). */
    serverTimeOffsetMs: 0,
    /** Last ETag from GET /player/template/ (for If-None-Match on silent polls). */
    templateEtag: null,
    /** Bumped on soft "restart" command to remount the template tree without document reload. */
    templateMountKey: 0,
  }),

  actions: {
    // ── Device identity helpers ────────────────────────────────────

    normalizeScreenId(screenId) {
      return screenId ? String(screenId).trim() : null
    },

    getStoredIdentities() {
      try {
        const raw = localStorage.getItem(STORAGE_KEYS.identities)
        if (!raw) return {}
        const parsed = JSON.parse(raw)
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {}
        return parsed
      } catch (_) {
        return {}
      }
    },

    saveStoredIdentities(identities) {
      try {
        localStorage.setItem(STORAGE_KEYS.identities, JSON.stringify(identities))
      } catch (e) {
        console.error('[PlayerStore] Failed to persist player identities:', e)
      }
    },

    migrateLegacyIdentity() {
      const legacyScreenId = localStorage.getItem(STORAGE_KEYS.screenId)
      const legacyDeviceToken = localStorage.getItem(STORAGE_KEYS.deviceToken)
      if (!legacyScreenId || !legacyDeviceToken) return

      const identities = this.getStoredIdentities()
      if (!identities[legacyScreenId]) {
        identities[legacyScreenId] = legacyDeviceToken
        this.saveStoredIdentities(identities)
      }
    },

    getFirstStoredScreenId() {
      const identities = this.getStoredIdentities()
      const first = Object.keys(identities)[0]
      return first || null
    },

    setActiveScreen(screenId) {
      this.activeScreenId = this.normalizeScreenId(screenId)
    },

    getActiveScreenId() {
      return this.activeScreenId
    },

    resolveScreenId(screenId, options = {}) {
      const { allowFallback = true } = options
      const normalized = this.normalizeScreenId(screenId)
      if (normalized) return normalized
      if (!allowFallback) return null
      if (this.activeScreenId) return this.activeScreenId
      const legacyScreenId = this.normalizeScreenId(localStorage.getItem(STORAGE_KEYS.screenId))
      if (legacyScreenId) return legacyScreenId
      return this.getFirstStoredScreenId()
    },

    saveDeviceIdentity(screenId, deviceToken) {
      const normalizedScreenId = this.normalizeScreenId(screenId)
      if (!normalizedScreenId || !deviceToken) return

      try {
        const identities = this.getStoredIdentities()
        identities[normalizedScreenId] = deviceToken
        this.saveStoredIdentities(identities)

        // Keep legacy keys aligned with currently active identity for backward compatibility.
        localStorage.setItem(STORAGE_KEYS.screenId, normalizedScreenId)
        localStorage.setItem(STORAGE_KEYS.deviceToken, deviceToken)
        localStorage.setItem(STORAGE_KEYS.isPaired, 'true')
        localStorage.setItem(STORAGE_KEYS.pairedAt, new Date().toISOString())
      } catch (e) {
        console.error('[PlayerStore] Failed to save device identity:', e)
      }
      this.setActiveScreen(normalizedScreenId)
      playerAPI.setDeviceIdentity({ screenId: normalizedScreenId, deviceToken })
    },

    loadDeviceIdentity(screenId = null, options = {}) {
      this.migrateLegacyIdentity()
      const resolvedScreenId = this.resolveScreenId(screenId, options)
      if (!resolvedScreenId) return false

      const identities = this.getStoredIdentities()
      const token = identities[resolvedScreenId]

      if (token) {
        this.setActiveScreen(resolvedScreenId)
        localStorage.setItem(STORAGE_KEYS.screenId, resolvedScreenId)
        localStorage.setItem(STORAGE_KEYS.deviceToken, token)
        localStorage.setItem(STORAGE_KEYS.isPaired, 'true')
        playerAPI.setDeviceIdentity({ screenId: resolvedScreenId, deviceToken: token })
        return true
      }
      return false
    },

    hasDeviceIdentity(screenId = null, options = {}) {
      this.migrateLegacyIdentity()
      const resolvedScreenId = this.resolveScreenId(screenId, options)
      if (!resolvedScreenId) return false

      const identities = this.getStoredIdentities()
      return !!identities[resolvedScreenId]
    },

    clearDeviceIdentity(screenId = null, options = {}) {
      const resolvedScreenId = this.resolveScreenId(screenId, options)
      if (resolvedScreenId) {
        const identities = this.getStoredIdentities()
        delete identities[resolvedScreenId]
        this.saveStoredIdentities(identities)
      } else {
        for (const key of Object.values(STORAGE_KEYS)) {
          try { localStorage.removeItem(key) } catch (_) { /* ignore */ }
        }
      }

      const activeIdentity = playerAPI.getDeviceIdentity()
      if (!resolvedScreenId || activeIdentity.screenId === resolvedScreenId) {
        playerAPI.clearDeviceIdentity()
      }

      if (!resolvedScreenId || this.activeScreenId === resolvedScreenId) {
        this.activeScreenId = null
      }

      try {
        localStorage.removeItem(STORAGE_KEYS.screenId)
        localStorage.removeItem(STORAGE_KEYS.deviceToken)
        localStorage.removeItem(STORAGE_KEYS.isPaired)
      } catch (_) { /* ignore */ }

      // Also clean up legacy keys
      for (const k of ['player_auth_token', 'player_secret_key']) {
        try { localStorage.removeItem(k) } catch (_) { /* ignore */ }
      }
    },

    // Legacy alias expected by WebPlayer.vue
    clearCredentials() {
      this.clearDeviceIdentity()
    },

    // ── Initialization ─────────────────────────────────────────────

    async initialize(screenId = null, options = {}) {
      const { allowFallback = true } = options
      try {
        const resolvedScreenId = this.resolveScreenId(screenId, { allowFallback })
        if (resolvedScreenId) {
          this.setActiveScreen(resolvedScreenId)
        }

        if (!this.loadDeviceIdentity(this.activeScreenId, { allowFallback })) {
          const error = new Error('Screen not paired. Please pair your screen first.')
          error.code = 'SCREEN_NOT_PAIRED'
          error.screenId = this.activeScreenId
          throw error
        }
        await this.fetchTemplate()
      } catch (error) {
        console.error('[PlayerStore] Initialization error:', error)
        this.status = 'error'
        this.errorMessage = error.message || 'Initialization failed'

        if (
          error.code === 'SCREEN_NOT_PAIRED' ||
          error.code === 'DEVICE_NOT_PAIRED' ||
          error.code === 'DEVICE_AUTH_FAILED'
        ) {
          this.status = 'unpaired'
          this.errorMessage = 'Please pair your screen first to continue.'
        }
        throw error
      }
    },

    // ── Template ───────────────────────────────────────────────────

    /**
     * Load or refresh the active template for this screen.
     * @param {{ silent?: boolean }} options — silent: no loading flash, keep playing on transient errors (polling).
     */
    async fetchTemplate(options = {}) {
      const silent = options.silent === true
      try {
        if (!this.loadDeviceIdentity(this.activeScreenId)) {
          const error = new Error('Screen not paired. Please pair your screen first.')
          error.code = 'SCREEN_NOT_PAIRED'
          throw error
        }
        if (!silent) {
          this.status = 'loading'
          this.errorMessage = null
        }
        const response = await playerAPI.fetchTemplate({
          ifNoneMatch: silent && this.templateEtag ? this.templateEtag : undefined,
        })

        if (response.status === 'not_modified') {
          if (response._etag) this.templateEtag = response._etag
          return
        }

        const { _timeSync, _etag, ...payload } = response
        if (_etag) this.templateEtag = _etag
        if (_timeSync) {
          this.serverTimeOffsetMs = _timeSync.serverNowMs - _timeSync.clientNowMs
        } else if (!silent) {
          this.serverTimeOffsetMs = 0
        }

        if (payload.status === 'success') {
          this.template = payload.template
          this.status = 'success'
        } else if (payload.status === 'no_template') {
          this.template = null
          this.status = 'no_template'
        } else {
          throw new Error(payload.message || 'Unknown response status')
        }
      } catch (error) {
        console.error('Template fetch error:', error)

        if (error.code === 'DEVICE_AUTH_FAILED' || error.status === 401) {
          this.status = 'unpaired'
          this.errorMessage = 'Device token revoked or invalid. Please re-pair.'
          this.stopPolling()
          return
        }

        if (error.status === 404) {
          this.status = 'unpaired'
          this.errorMessage = 'Screen not found. Please re-pair.'
          this.stopPolling()
          return
        }

        if (silent && this.status === 'success' && this.template) {
          return
        }

        this.status = 'error'
        this.errorMessage = error.message || 'Failed to fetch template'
        this.startRetryCountdown()
      }
    },

    startRetryCountdown() {
      this.retryCountdown = 30
      if (this.retryTimer) clearInterval(this.retryTimer)
      this.retryTimer = setInterval(() => {
        this.retryCountdown--
        if (this.retryCountdown <= 0) {
          clearInterval(this.retryTimer)
          this.retryTimer = null
          this.fetchTemplate()
        }
      }, 1000)
    },

    // ── Heartbeat ──────────────────────────────────────────────────

    async sendHeartbeat() {
      try {
        const systemInfo = collectSystemInfo()
        const response = await playerAPI.sendHeartbeat(systemInfo)
        this.lastSuccessfulHeartbeat = Date.now()
        if (this.connectionLostTimer) {
          clearTimeout(this.connectionLostTimer)
          this.connectionLostTimer = null
        }
        this.startConnectionLossMonitoring()
        return response
      } catch (error) {
        console.error('Heartbeat error:', error)

        if (error.code === 'DEVICE_AUTH_FAILED' || error.status === 401) {
          this.status = 'unpaired'
          this.errorMessage = 'Device token revoked. Returning to pairing.'
          this.stopPolling()
          throw error
        }

        this.checkConnectionLoss()
        throw error
      }
    },

    startConnectionLossMonitoring() {
      if (this.connectionLostTimer) clearTimeout(this.connectionLostTimer)
      this.connectionLostTimer = setTimeout(() => this.checkConnectionLoss(), 300000)
    },

    checkConnectionLoss() {
      if (!this.lastSuccessfulHeartbeat) {
        this.startConnectionLossMonitoring()
        return
      }
      if (Date.now() - this.lastSuccessfulHeartbeat >= 300000) {
        this.status = 'error'
        this.errorMessage = 'Connection lost for 5 minutes. Please check your network.'
      }
    },

    // ── Overlay ────────────────────────────────────────────────────

    showOverlay(message, durationMs = 10000) {
      if (this.overlayTimer) { clearTimeout(this.overlayTimer); this.overlayTimer = null }
      this.overlayMessage = message
      this.overlayVisible = true
      this.overlayTimer = setTimeout(() => this.clearOverlay(), durationMs)
    },

    clearOverlay() {
      if (this.overlayTimer) { clearTimeout(this.overlayTimer); this.overlayTimer = null }
      this.overlayVisible = false
      this.overlayMessage = null
    },

    // ── Polling ────────────────────────────────────────────────────

    startPolling() {
      if (!this.hasDeviceIdentity(this.activeScreenId)) {
        this.status = 'unpaired'
        this.errorMessage = 'Screen not paired.'
        return
      }
      // Ensure API has identity loaded
      this.loadDeviceIdentity(this.activeScreenId)

      if (this.pollingInterval) { clearInterval(this.pollingInterval); this.pollingInterval = null }

      this.lastSuccessfulHeartbeat = Date.now()

      // Initial heartbeat (small delay for init)
      setTimeout(() => {
        this.sendHeartbeat().catch(() => {
          setTimeout(() => this.sendHeartbeat().catch(() => this.checkConnectionLoss()), 5000)
        })
      }, 500)

      // Heartbeat every 30s
      this.heartbeatInterval = setInterval(() => {
        this.sendHeartbeat().catch(() => this.checkConnectionLoss())
      }, 30000)

      // Command polling every 5s
      this.fetchAndExecuteCommands().catch(() => {})
      this.commandPollingInterval = setInterval(() => {
        this.fetchAndExecuteCommands().catch(() => {})
      }, 5000)

      // Template polling safety net: commands deliver refresh quickly; this catches missed pushes.
      // Silent fetch + If-None-Match avoids loading flicker and cheap 304s when nothing changed.
      const poll = () => {
        const interval = this.status === 'no_template' ? 20000 : 60000
        this.pollingInterval = setInterval(() => {
          this.fetchTemplate({ silent: true }).then(() => {
            if (this.pollingInterval) {
              const newInterval = this.status === 'no_template' ? 20000 : 60000
              if (newInterval !== interval) {
                clearInterval(this.pollingInterval)
                this.pollingInterval = null
                poll()
              }
            }
          })
        }, interval)
      }
      poll()
    },

    // ── Commands ───────────────────────────────────────────────────

    async fetchAndExecuteCommands() {
      if (!this.hasDeviceIdentity(this.activeScreenId)) return
      try {
        this.loadDeviceIdentity(this.activeScreenId)
        const response = await playerAPI.fetchPendingCommands()
        if (response.status === 'success' && response.commands?.length > 0) {
          for (const command of response.commands) {
            await this.executeCommand(command)
          }
        }
      } catch (error) {
        if (error.code === 'DEVICE_AUTH_FAILED' || error.status === 401) {
          this.status = 'unpaired'
          this.stopPolling()
        }
      }
    },

    async executeCommand(command) {
      const { id, type, payload } = command
      try {
        let success = false
        let errorMessage = ''

        switch (type) {
          case 'restart':
            success = true
            await playerAPI.updateCommandStatus(id, 'done', '', {})
            this.templateMountKey += 1
            await this.fetchTemplate({ silent: true })
            return

          case 'refresh':
            success = true
            await this.fetchTemplate({ silent: true })
            break

          case 'change_template':
            if (payload?.template_id) {
              success = true
              await this.fetchTemplate({ silent: true })
            } else {
              errorMessage = 'Template ID not provided in payload'
            }
            break

          case 'display_message':
            if (payload?.message) {
              const ms = Math.max(1000, (payload.duration || 10) * 1000)
              this.showOverlay(payload.message, ms)
              success = true
            } else {
              errorMessage = 'Message not provided in payload'
            }
            break

          case 'sync_content':
            success = true
            break

          case 'unpair':
            this.clearDeviceIdentity()
            success = true
            await playerAPI.updateCommandStatus(id, 'done', '', {})
            this.status = 'unpaired'
            this.template = null
            this.templateEtag = null
            this.stopPolling()
            return

          case 'custom':
            success = true
            errorMessage = 'Custom script execution not implemented for security'
            break

          default:
            errorMessage = `Unknown command type: ${type}`
        }

        await playerAPI.updateCommandStatus(id, success ? 'done' : 'failed', errorMessage, {})
      } catch (error) {
        try {
          await playerAPI.updateCommandStatus(id, 'failed', error.message || 'Execution error', {})
        } catch (_) { /* ignore */ }
      }
    },

    stopPolling() {
      for (const key of ['pollingInterval', 'heartbeatInterval', 'commandPollingInterval', 'retryTimer']) {
        if (this[key]) { clearInterval(this[key]); this[key] = null }
      }
      if (this.connectionLostTimer) { clearTimeout(this.connectionLostTimer); this.connectionLostTimer = null }
      if (this.overlayTimer) { clearTimeout(this.overlayTimer); this.overlayTimer = null }
      this.overlayVisible = false
      this.overlayMessage = null
    },
  },
})
