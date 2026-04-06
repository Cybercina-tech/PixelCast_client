import { defineStore } from 'pinia'

const THEME_STORAGE_KEY = 'pixelcast-signage_theme'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: 'dark', // 'dark' | 'light'
  }),

  getters: {
    /**
     * Check if dark mode is active
     */
    isDarkMode() {
      return this.theme === 'dark'
    },
  },

  actions: {
    /**
     * Initialize theme on app startup
     * Reads from localStorage or detects system preference
     */
    initTheme() {
      // Check localStorage first
      const storedTheme = localStorage.getItem(THEME_STORAGE_KEY)
      
      if (storedTheme === 'dark' || storedTheme === 'light') {
        this.setTheme(storedTheme)
        return
      }

      // Detect system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        this.setTheme('light')
      } else {
        // Default to dark
        this.setTheme('dark')
      }
    },

    /**
     * Set theme and update DOM
     */
    setTheme(theme) {
      if (theme !== 'dark' && theme !== 'light') {
        console.warn(`Invalid theme: ${theme}. Using 'dark' as fallback.`)
        theme = 'dark'
      }

      this.theme = theme
      localStorage.setItem(THEME_STORAGE_KEY, theme)

      // Update HTML class
      const html = document.documentElement
      if (theme === 'dark') {
        html.classList.add('dark')
      } else {
        html.classList.remove('dark')
      }
    },

    /**
     * Toggle between dark and light theme
     */
    toggleTheme() {
      this.setTheme(this.theme === 'dark' ? 'light' : 'dark')
    },
  },
})

