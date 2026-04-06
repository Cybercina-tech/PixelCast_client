import { defineStore } from 'pinia'
import { usersAPI } from '../services/api'

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [],
    currentUser: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchUsers(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await usersAPI.list(params)
        // Backend returns paginated results or array
        this.users = response.data.results || response.data || []
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchUser(id) {
      this.loading = true
      this.error = null
      try {
        const response = await usersAPI.detail(id)
        this.currentUser = response.data
        // Update in list if exists
        const index = this.users.findIndex(u => u.id === id)
        if (index !== -1) {
          this.users[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async createUser(data) {
      this.loading = true
      this.error = null
      try {
        // Backend requires password_confirm for user creation
        const userData = {
          ...data,
          password_confirm: data.password,
        }
        const response = await usersAPI.create(userData)
        this.users.push(response.data)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async updateUser(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await usersAPI.update(id, data)
        const index = this.users.findIndex(u => u.id === id)
        if (index !== -1) {
          this.users[index] = response.data
        }
        if (this.currentUser?.id === id) {
          this.currentUser = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async deleteUser(id) {
      this.loading = true
      this.error = null
      try {
        await usersAPI.delete(id)
        this.users = this.users.filter(u => u.id !== id)
        if (this.currentUser?.id === id) {
          this.currentUser = null
        }
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async changeRole(id, role) {
      this.loading = true
      this.error = null
      try {
        // Backend expects: {role: 'Admin'}
        await usersAPI.changeRole(id, { role })
        const user = this.users.find(u => u.id === id)
        if (user) user.role = role
        if (this.currentUser?.id === id) {
          this.currentUser.role = role
        }
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async changePassword(id, data) {
      this.loading = true
      this.error = null
      try {
        // Backend requires: old_password, new_password, new_password_confirm
        const passwordData = {
          old_password: data.old_password || '',
          new_password: data.password || data.new_password,
          new_password_confirm: data.password_confirm || data.new_password,
        }
        await usersAPI.changePassword(id, passwordData)
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchMe() {
      try {
        const response = await usersAPI.me()
        this.currentUser = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.message
        throw error
      }
    },
  },
})
