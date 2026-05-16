<template>
  <div
    :class="[
      'w-full max-w-[100vw]',
      shellClass,
    ]"
  >
    <div v-if="fatalError" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 p-6 text-center text-white">
      <div>
        <h2 class="text-xl font-semibold">Something went wrong</h2>
        <p class="mt-2 text-sm text-gray-200">{{ fatalError }}</p>
        <button class="mt-4 rounded bg-cyan-600 px-4 py-2 text-sm font-medium hover:bg-cyan-500" @click="reloadApp">
          Reload
        </button>
      </div>
    </div>
    <RouterView />
    <NotificationContainer />
    <DeleteConfirmation />
  </div>
</template>

<script setup>
import { computed, onBeforeMount, onMounted, onUnmounted, ref, watch } from 'vue'
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
const fatalError = ref('')

const handleRuntimeError = (event) => {
  fatalError.value = event?.detail?.message || 'Unexpected application error'
}

const reloadApp = () => {
  window.location.reload()
}

// Initialize notification store (ensure it's reactive)
// This ensures the store is properly initialized when the app starts

// Initialize theme BEFORE component mounts to prevent flash
onBeforeMount(() => {
  themeStore.initTheme()
})

onMounted(async () => {
  window.addEventListener('app-runtime-error', handleRuntimeError)
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

onUnmounted(() => {
  window.removeEventListener('app-runtime-error', handleRuntimeError)
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
