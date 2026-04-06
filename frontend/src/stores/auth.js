import { defineStore } from 'pinia'
import { authAPI, usersAPI } from '../services/api'
import { normalizeApiError } from '../utils/apiError'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const token = localStorage.getItem('auth_token')
    const refreshToken = localStorage.getItem('refresh_token')
    return {
      user: null,
      token,
      refreshToken,
      isAuthenticated: !!token,
      loading: false,
      error: null,
      initialized: false,
      /** Set when Developer is viewing the app as another user */
      impersonation: null,
    }
  },
  actions: {
    async login(credentials) {
      this.loading = true
      this.error = null
      try {
        const response = await authAPI.login(credentials)
        if (response.data.status === '2fa_required') {
          return {
            needs2fa: true,
            twoFactorToken: response.data.two_factor_token,
          }
        }
        // Backend returns: {status: 'success', user: {...}, tokens: {refresh, access}}
        if (response.data.tokens) {
          this.token = response.data.tokens.access
          this.refreshToken = response.data.tokens.refresh
          localStorage.setItem('auth_token', this.token)
          localStorage.setItem('refresh_token', this.refreshToken)
        }
        
        // Set user info from response
        if (response.data.user) {
          this.user = response.data.user
        } else {
          // Fallback: fetch user info
          await this.fetchMe()
        }
        
        this.isAuthenticated = true
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage || 'Login failed. Please check your credentials.'
        throw error
      } finally {
        this.loading = false
      }
    },
    async complete2fa({ twoFactorToken, code }) {
      this.loading = true
      this.error = null
      try {
        const response = await authAPI.login2fa({
          two_factor_token: twoFactorToken,
          code: String(code || '').trim(),
        })
        if (response.data.tokens) {
          this.token = response.data.tokens.access
          this.refreshToken = response.data.tokens.refresh
          localStorage.setItem('auth_token', this.token)
          localStorage.setItem('refresh_token', this.refreshToken)
        }
        if (response.data.user) {
          this.user = response.data.user
        } else {
          await this.fetchMe()
        }
        this.isAuthenticated = true
        return response.data
      } catch (error) {
        this.error = normalizeApiError(error).userMessage || 'Invalid code.'
        throw error
      } finally {
        this.loading = false
      }
    },
    async logout() {
      try {
        const refreshToken = this.refreshToken || localStorage.getItem('refresh_token')
        if (refreshToken) {
          await authAPI.logout({ refresh_token: refreshToken })
        }
      } catch (error) {
        // Ignore errors on logout - clear local state anyway
        console.error('Logout error:', error)
      } finally {
        this.token = null
        this.refreshToken = null
        this.user = null
        this.isAuthenticated = false
        this.impersonation = null
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        sessionStorage.removeItem('platform_admin_refresh')
      }
    },
    async fetchMe() {
      try {
        const response = await usersAPI.me()
        this.user = response.data
        this.isAuthenticated = true
        return response.data
      } catch (error) {
        // If fetch fails, clear auth
        if (error.response?.status === 401 || error.response?.status === 403) {
          this.token = null
          this.refreshToken = null
          this.user = null
          this.isAuthenticated = false
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
        }
        throw error
      }
    },
    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }
      try {
        const response = await authAPI.refreshToken(this.refreshToken)
        if (response.data.access) {
          this.token = response.data.access
          localStorage.setItem('auth_token', this.token)
          if (response.data.refresh) {
            this.refreshToken = response.data.refresh
            localStorage.setItem('refresh_token', this.refreshToken)
          }
        }
        return this.token
      } catch (error) {
        // Refresh failed, logout user
        await this.logout()
        throw error
      }
    },
    async updateMe(data) {
      try {
        const response = await usersAPI.updateMe(data)
        this.user = response.data
        return response.data
      } catch (error) {
        throw error
      }
    },
    async startPlatformImpersonation() {
      throw new Error('Platform impersonation is not available in this product build.')
    },
    async stopPlatformImpersonation() {
      const adminRefresh = sessionStorage.getItem('platform_admin_refresh')
      if (adminRefresh) {
        sessionStorage.removeItem('platform_admin_refresh')
      }
      this.impersonation = null
    },
    async initialize() {
      // Initialize auth state on app startup
      if (this.initialized) return
      
      const token = localStorage.getItem('auth_token')
      if (token && !this.user) {
        try {
          this.token = token
          this.refreshToken = localStorage.getItem('refresh_token')
          await this.fetchMe()
          this.isAuthenticated = true
          if (sessionStorage.getItem('platform_admin_refresh')) {
            this.impersonation = { active: true }
          }
        } catch (error) {
          // Token invalid, clear it
          this.token = null
          this.refreshToken = null
          this.isAuthenticated = false
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
        }
      }
      this.initialized = true
    },
  },
})
