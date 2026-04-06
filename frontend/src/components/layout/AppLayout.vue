<template>
  <div :class="['flex h-screen starry-background relative', { 'editor-layout': isEditorRoute }]">
    <!-- Animated Blob Background -->
    <div class="starry-blobs">
      <div class="starry-blob starry-blob-1"></div>
      <div class="starry-blob starry-blob-2"></div>
      <div class="starry-blob starry-blob-3"></div>
    </div>
    
    <Sidebar :is-open="sidebarOpen" @close="sidebarOpen = false" />
    <div class="flex-1 flex flex-col overflow-hidden lg:ml-0 relative z-10">
      <Navbar :title="title" @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <div
        v-if="authStore.isRestrictedMode"
        class="shrink-0 border-b border-rose-500/30 bg-rose-500/10 px-4 py-2.5 flex items-center gap-3 text-sm text-rose-300"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
        </svg>
        <span class="flex-1">{{ restrictionBannerText }}</span>
      </div>
      <main :class="['flex-1 flex flex-col scroll-container', isEditorRoute ? 'overflow-hidden' : 'overflow-y-auto custom-scrollbar']">
        <div :class="[
          'flex-1 min-h-0 w-full main-content-wrapper',
          isEditorRoute ? 'p-0' : 'p-4 md:p-6 lg:p-8'
        ]">
          <slot />
        </div>
      </main>
      <Footer :class="{ 'hidden lg:block': isEditorRoute }" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useScreensStore } from '@/stores/screens'
import { useWebSocket } from '@/composables/useWebSocket'
import Sidebar from './Sidebar.vue'
import Navbar from './Navbar.vue'
import Footer from './Footer.vue'

defineProps({
  title: {
    type: String,
    default: 'PixelCast Signage',
  },
})

const route = useRoute()
const sidebarOpen = ref(false)

// Check if we're on the template editor route to prevent main scroll
const isEditorRoute = computed(() => {
  return route.name === 'template-editor' || route.name === 'template-editor-new' || (route.path.includes('/templates/') && route.path.includes('/edit'))
})
const authStore = useAuthStore()
const restrictionBannerText = computed(() => {
  const info = authStore.restrictionInfo
  if (!info) return 'Your access is currently restricted. Only limited pages are available.'
  const msg = info.reason || info.message || 'Your access is currently restricted.'
  const untilStr = info.until ? ` Until: ${new Date(info.until).toLocaleString()}` : ''
  return `${msg}${untilStr}`
})
const screensStore = useScreensStore()
const { connect, disconnect, on, off, isConnected } = useWebSocket()

// Set up WebSocket listener for screen status updates
onMounted(() => {
  if (authStore.isAuthenticated && authStore.token) {
    // Connect WebSocket (JWT access token lives on `token`, not accessToken)
    connect(authStore.token)
    
    // Listen for screen status updates
    on('screen_status_update', (data) => {
      if (data && data.screen) {
        screensStore.handleScreenStatusUpdate(data.screen)
      }
    })
    
    // Listen for screen heartbeat updates
    on('screen_heartbeat', (data) => {
      if (data && data.screen_id) {
        // Fetch updated status for this screen
        screensStore.fetchSingleScreenStatus(data.screen_id).catch(err => {
          console.warn('Failed to fetch screen status after heartbeat:', err)
        })
      }
    })
  }
})

onUnmounted(() => {
  // Clean up WebSocket listeners
  off('screen_status_update')
  off('screen_heartbeat')
  disconnect()
})
</script>

<style scoped>
/* Ensure content has space above footer when scrolling */
.main-content-wrapper:not(.p-0) {
  padding-bottom: calc(1.5rem + 30px);
}

.main-content-wrapper.p-0 {
  padding-bottom: 30px;
}

/* Keep global navigation visible but compact in editor mode. */
.editor-layout :deep(.space-sidebar) {
  width: 5rem !important;
}

.editor-layout :deep(.logo-text),
.editor-layout :deep(.menu-text),
.editor-layout :deep(.error-dashboard-text),
.editor-layout :deep(.submenu-list),
.editor-layout :deep(.chevron-icon),
.editor-layout :deep(.menu-badge),
.editor-layout :deep(.submenu-badge) {
  display: none !important;
}

.editor-layout :deep(.menu-item) {
  justify-content: center;
  padding: 0.875rem 0.5rem;
}

.editor-layout :deep(.nav-content) {
  padding: 0 0.4rem;
}
</style>
