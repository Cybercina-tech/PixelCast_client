<template>
  <div
    :class="[
      'w-full max-w-[100vw]',
      shellClass,
    ]"
  >
    <RouterView />
    <NotificationContainer />
    <DeleteConfirmation />
  </div>
</template>

<script setup>
import { computed, onBeforeMount, onMounted, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { useSidebarStore } from './stores/sidebar'
import { useNotificationStore } from './stores/notification'
import NotificationContainer from './components/common/NotificationContainer.vue'
import DeleteConfirmation from './components/common/DeleteConfirmation.vue'
import { useRouteHead } from '@/composables/useRouteHead'

useRouteHead()

const route = useRoute()
const isPlayerRoute = computed(() => {
  const n = route.name
  if (n === 'player-connect' || n === 'player-screen' || n === 'player') return true
  return typeof route.path === 'string' && route.path.startsWith('/player')
})
const shellClass = computed(() => {
  if (route.name === 'landing') {
    return 'min-h-screen min-h-[100dvh] overflow-x-hidden'
  }
  if (isPlayerRoute.value) {
    return 'min-h-[100dvh] h-[100dvh] overflow-hidden overscroll-none'
  }
  return 'min-h-[100dvh] h-[100dvh] overflow-hidden'
})
const authStore = useAuthStore()
const themeStore = useThemeStore()
const sidebarStore = useSidebarStore()
const notificationStore = useNotificationStore()

// Initialize notification store (ensure it's reactive)
// This ensures the store is properly initialized when the app starts

// Initialize theme BEFORE component mounts to prevent flash
onBeforeMount(() => {
  themeStore.initTheme()
})

onMounted(async () => {
  // Skip auth initialization on player route (player uses its own authentication)
  if (!isPlayerRoute.value) {
    // Initialize auth state on app startup (restore session if token exists)
    await authStore.initialize()
    
    // Initialize sidebar items if user is authenticated
    if (authStore.isAuthenticated && authStore.user) {
      await sidebarStore.fetchSidebarItems()
    }
  }
})

// Watch for user changes and update sidebar (skip on player route)
watch(() => authStore.user, async (newUser) => {
  // Skip sidebar updates on player route
  if (isPlayerRoute.value) return
  
  if (newUser) {
    await sidebarStore.fetchSidebarItems()
  } else {
    sidebarStore.clearSidebarItems()
  }
})
</script>
