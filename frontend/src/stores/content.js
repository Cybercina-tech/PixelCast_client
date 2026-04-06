import { defineStore } from 'pinia'
import { contentsAPI } from '../services/api'

export const useContentStore = defineStore('content', {
  state: () => ({
    contents: [],
    currentContent: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      type: null,
      download_status: null,
      widget: null,
    },
  }),
  getters: {
    downloadedContents: (state) => state.contents.filter(c => c.downloaded),
    pendingContents: (state) => state.contents.filter(c => !c.downloaded && c.download_status === 'pending'),
    failedContents: (state) => state.contents.filter(c => c.download_status === 'failed'),
    filteredContents: (state) => {
      let filtered = state.contents
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(c => 
          c.name?.toLowerCase().includes(search) ||
          c.description?.toLowerCase().includes(search)
        )
      }
      if (state.filters.type) {
        filtered = filtered.filter(c => c.type === state.filters.type)
      }
      if (state.filters.download_status) {
        filtered = filtered.filter(c => c.download_status === state.filters.download_status)
      }
      if (state.filters.widget) {
        filtered = filtered.filter(c => c.widget === state.filters.widget)
      }
      return filtered
    },
  },
  actions: {
    async fetchContents(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await contentsAPI.list({ ...this.filters, ...params })
        this.contents = response.data.results || response.data || []
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchContent(id) {
      this.loading = true
      this.error = null
      try {
        const response = await contentsAPI.detail(id)
        this.currentContent = response.data
        // Update in list if exists
        const index = this.contents.findIndex(c => c.id === id)
        if (index !== -1) {
          this.contents[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async createContent(data) {
      this.loading = true
      this.error = null
      try {
        const response = await contentsAPI.create(data)
        this.contents.push(response.data)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async updateContent(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await contentsAPI.update(id, data)
        const index = this.contents.findIndex(c => c.id === id)
        if (index !== -1) {
          this.contents[index] = response.data
        }
        if (this.currentContent?.id === id) {
          this.currentContent = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async deleteContent(id) {
      this.loading = true
      this.error = null
      try {
        await contentsAPI.delete(id)
        this.contents = this.contents.filter(c => c.id !== id)
        if (this.currentContent?.id === id) {
          this.currentContent = null
        }
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async uploadContent(id, file, additionalData = {}) {
      this.loading = true
      this.error = null
      
      console.log('[ContentStore] uploadContent called', {
        contentId: id,
        fileName: file?.name,
        fileSize: file?.size,
        fileType: file?.type,
        additionalData
      })
      
      try {
        const response = await contentsAPI.upload(id, file, additionalData)
        
        console.log('[ContentStore] uploadContent success', {
          status: response.status,
          data: response.data
        })
        
        // Update content in list
        const index = this.contents.findIndex(c => c.id === id)
        if (index !== -1) {
          this.contents[index] = { ...this.contents[index], ...response.data }
        }
        if (this.currentContent?.id === id) {
          this.currentContent = { ...this.currentContent, ...response.data }
        }
        return response.data
      } catch (error) {
        console.error('[ContentStore] uploadContent error', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message,
          config: {
            url: error.config?.url,
            method: error.config?.method,
            headers: error.config?.headers
          }
        })
        
        // Extract detailed error message
        const errorData = error.response?.data || {}
        const errorMessage = errorData.message || 
                               errorData.error || 
                               errorData.detail || 
                               (typeof errorData === 'string' ? errorData : JSON.stringify(errorData)) ||
                               error.message ||
                               'Failed to upload content'
        
        this.error = errorMessage
        throw error
      } finally {
        this.loading = false
      }
    },
    async downloadToScreen(contentId, screenId) {
      this.loading = true
      this.error = null
      try {
        const response = await contentsAPI.downloadToScreen(contentId, { screen_id: screenId })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async retryDownload(contentId, screenId) {
      this.loading = true
      this.error = null
      try {
        console.log(`DEBUG [retryDownload]: Starting retry - contentId: ${contentId}, screenId: ${screenId}`)
        console.log(`DEBUG [retryDownload]: Request payload: { screen_id: ${screenId} }`)
        
        const response = await contentsAPI.retryDownload(contentId, { screen_id: screenId })
        
        console.log('DEBUG [retryDownload]: Response received:', response.data)
        console.log('DEBUG [retryDownload]: Response content data:', response.data?.content)
        console.log('DEBUG [retryDownload]: Response download_status:', response.data?.download_status)
        
        // CRITICAL: Update content in store immediately if response includes content data
        // This ensures UI updates without waiting for next fetch
        if (response.data && response.data.content) {
          console.log('DEBUG [retryDownload]: Updating Content Store with:', response.data.content)
          
          // Import smart update utility
          const { smartUpdateObject } = await import('@/utils/deepCompare')
          
          // Find content in current list and update
          const index = this.contents.findIndex(c => c.id === contentId)
          if (index !== -1) {
            const oldContent = this.contents[index]
            this.contents[index] = smartUpdateObject(oldContent, response.data.content)
            console.log('DEBUG [retryDownload]: Content updated in store. New download_status:', this.contents[index]?.download_status)
          } else {
            // Content not in list, add it
            this.contents.push(response.data.content)
            console.log('DEBUG [retryDownload]: Content added to store')
          }
          
          // Update currentContent if it's the one being updated
          if (this.currentContent?.id === contentId) {
            this.currentContent = smartUpdateObject(this.currentContent, response.data.content)
            console.log('DEBUG [retryDownload]: currentContent updated. New download_status:', this.currentContent?.download_status)
          }
        } else {
          console.warn('DEBUG [retryDownload]: Response does not include content data!')
        }
        
        return response.data
      } catch (error) {
        console.error('DEBUG [retryDownload]: Error:', error)
        console.error('DEBUG [retryDownload]: Error response:', error.response?.data)
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async getDownloadURL(contentId, expiration = null) {
      this.loading = true
      this.error = null
      try {
        const params = expiration ? { expiration } : {}
        const response = await contentsAPI.download(contentId, params)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    async verifyIntegrity(contentId, file = null) {
      this.loading = true
      this.error = null
      try {
        const formData = file ? new FormData() : null
        if (formData) {
          formData.append('file', file)
        }
        const response = await contentsAPI.verifyIntegrity(contentId, formData || {})
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.response?.data?.message || error.message
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
