<template>
  <div class="sidebar-root">
  <aside
    ref="sidebarRef"
    :class="[
      'space-sidebar fixed left-0 top-0 z-40 transition-all duration-500 ease-in-out w-64',
      isOpen ? 'translate-x-0' : '-translate-x-full',
      'lg:translate-x-0 lg:static lg:z-auto'
    ]"
  >

    <div class="flex flex-col h-full relative">
      <!-- Header -->
      <div class="sidebar-header">
        <div class="flex items-center gap-3 px-4 py-4">
          <div class="logo-container">
            <div class="logo-icon">
              <BoltIcon class="w-6 h-6" />
            </div>
          </div>
          <h2 class="logo-text">PixelCast Signage</h2>
        </div>
      </div>
      
      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto sidebar-nav custom-scrollbar">
        <div v-if="sidebarStore.loading" class="loading-container">
          <div class="loading-spinner"></div>
        </div>
        
        <div v-else class="nav-content">
          <!-- Menu Items -->
          <ul class="menu-list">
            <li v-for="item in displayedItems" :key="item.id" class="menu-item-wrapper">
                <!-- Parent item with children (submenu) -->
                <div v-if="item.children && item.children.length > 0">
                  <button
                    @click="toggleSubmenu(item.id)"
                    class="menu-item"
                    :class="{
                      'menu-item-active': isParentActive(item)
                    }"
                  >
                    <div class="menu-icon-wrapper">
                      <component 
                        :is="getIconComponent(item.icon)" 
                        class="menu-icon"
                        :class="{ 'icon-active': isParentActive(item) }"
                      />
                    </div>
                    <span class="menu-text">{{ item.title }}</span>
                    <span
                      v-if="item.badge"
                      class="menu-badge"
                    >
                      {{ item.badge }}
                    </span>
                    <ChevronDownIcon
                      :class="[
                        'chevron-icon',
                        openSubmenus.has(item.id) ? 'rotate-180' : ''
                      ]"
                    />
                  </button>
                  
                  <!-- Submenu items -->
                  <transition name="slide">
                    <ul
                      v-if="openSubmenus.has(item.id)"
                      class="submenu-list"
                    >
                      <li v-for="child in item.children" :key="child.id">
                        <router-link
                          :to="child.path"
                          class="submenu-item"
                          :class="{ 'submenu-item-active': isActive(child.path) }"
                        >
                          <component 
                            :is="getIconComponent(child.icon)" 
                            class="submenu-icon"
                            :class="{ 'icon-active': isActive(child.path) }"
                          />
                          <span class="submenu-text">{{ child.title }}</span>
                          <span
                            v-if="child.badge"
                            class="submenu-badge"
                          >
                            {{ child.badge }}
                          </span>
                        </router-link>
                      </li>
                    </ul>
                  </transition>
                </div>
                
                <!-- Regular item without children -->
                <router-link
                  v-else-if="item.path"
                  :to="item.path"
                  class="menu-item"
                  :class="{
                    'menu-item-active': isActive(item.path)
                  }"
                >
                  <div class="menu-icon-wrapper">
                    <component 
                      :is="getIconComponent(item.icon)" 
                      class="menu-icon"
                      :class="{ 'icon-active': isActive(item.path) }"
                    />
                  </div>
                  <span class="menu-text">{{ item.title }}</span>
                  <span
                    v-if="item.badge"
                    class="menu-badge"
                  >
                    {{ item.badge }}
                  </span>
                </router-link>
              </li>
            </ul>
        </div>
      </nav>
      
      <!-- Restriction banner -->
      <div v-if="isRestricted" class="px-3 pb-2">
        <div class="rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2.5 text-xs text-rose-300">
          <p class="font-semibold">Access restricted</p>
          <p class="mt-0.5 text-rose-300/80">{{ restrictionMessage }}</p>
        </div>
      </div>

      <!-- Developer: Error logs panel -->
      <div v-if="isDeveloper" class="sidebar-footer">
        <button
          @click="errorDashboardOpen = !errorDashboardOpen"
          class="error-dashboard-button"
          type="button"
        >
          <ClipboardDocumentListIcon class="w-5 h-5" />
          <span class="error-dashboard-text">Error Logs</span>
        </button>
      </div>
    </div>
  </aside>
  
  <!-- Error logs (Developer only): do not mount for other roles — avoids /admin/errors/stats 403 + toasts on every page -->
  <ErrorDashboard
    v-if="isDeveloper"
    :is-open="errorDashboardOpen"
    @close="errorDashboardOpen = false"
  />
  
  <!-- Overlay for mobile -->
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-30 lg:hidden transition-opacity duration-300"
    @click="$emit('close')"
  ></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeIcon,
  TvIcon,
  DocumentTextIcon,
  FolderIcon,
  ClockIcon,
  CommandLineIcon,
  UsersIcon,
  DocumentChartBarIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ServerIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentListIcon,
  ChevronDownIcon,
  BuildingOffice2Icon,
  EnvelopeIcon,
  TicketIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useSidebarStore } from '@/stores/sidebar'
import { isDeveloperOrSuperuser, isRouteAllowedInRestrictedMode } from '@/utils/permissions'
import ErrorDashboard from '@/components/admin/ErrorDashboard.vue'

defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close'])

const route = useRoute()
const authStore = useAuthStore()
const sidebarStore = useSidebarStore()

const sidebarRef = ref(null)
const errorDashboardOpen = ref(false)
const openSubmenus = ref(new Set())

// Icon mapping
const iconMap = {
  HomeIcon,
  TvIcon,
  DocumentTextIcon,
  FolderIcon,
  ClockIcon,
  CommandLineIcon,
  UsersIcon,
  DocumentChartBarIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ServerIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  BuildingOffice2Icon,
  EnvelopeIcon,
  ShieldCheckIcon,
  TicketIcon,
}

const getIconComponent = (iconName) => {
  return iconMap[iconName] || HomeIcon
}

const isDeveloper = computed(() => isDeveloperOrSuperuser(authStore.user))
const isRestricted = computed(() => authStore.isRestrictedMode)
const restrictionMessage = computed(() => {
  const info = authStore.restrictionInfo
  if (!info) return 'Your access has been limited by an administrator.'
  return info.reason || info.message || 'Your access has been limited by an administrator.'
})

const displayedItems = computed(() => {
  if (!isRestricted.value) return sidebarStore.items
  return sidebarStore.items.filter((item) => {
    if (item.path && isRouteAllowedInRestrictedMode(item.path)) return true
    if (item.children?.length) {
      return item.children.some((c) => c.path && isRouteAllowedInRestrictedMode(c.path))
    }
    return false
  })
})

const isActive = (path) => {
  if (!path) return false
  if (route.path === path) return true
  if (path !== '/' && route.path.startsWith(path)) return true
  return false
}

const isParentActive = (item) => {
  if (!item.children || item.children.length === 0) return false
  return item.children.some(child => isActive(child.path))
}

const toggleSubmenu = (itemId) => {
  if (openSubmenus.value.has(itemId)) {
    openSubmenus.value.delete(itemId)
  } else {
    openSubmenus.value.add(itemId)
  }
}


// Auto-open submenu if child is active
watch(() => route.path, (newPath) => {
  sidebarStore.items.forEach(item => {
    if (item.children && item.children.length > 0) {
      const hasActiveChild = item.children.some(child => isActive(child.path))
      if (hasActiveChild) {
        openSubmenus.value.add(item.id)
      }
    }
  })
}, { immediate: true })

// Fetch sidebar items when component mounts or user changes
onMounted(async () => {
  if (authStore.isAuthenticated && authStore.user) {
    await sidebarStore.fetchSidebarItems()
    // Auto-open submenus with active children
    sidebarStore.items.forEach(item => {
      if (item.children && item.children.length > 0) {
        const hasActiveChild = item.children.some(child => isActive(child.path))
        if (hasActiveChild) {
          openSubmenus.value.add(item.id)
        }
      }
    })
  }
})

// Watch for user changes and refetch sidebar items
watch(() => authStore.user, async (newUser) => {
  if (newUser) {
    await sidebarStore.fetchSidebarItems()
  } else {
    sidebarStore.clearSidebarItems()
  }
})
</script>

<style scoped>
/* Keep a regular wrapper to avoid overlay stacking edge cases. */
.sidebar-root {
  display: block;
}

/* Space Sidebar Base - Aether Identity */
.space-sidebar {
  background: var(--sidebar-bg); /* Frosted glass with 80% opacity */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: none; /* No borders - Aether uses soft shadows */
  box-shadow: var(--shadow-soft); /* Soft shadow instead of border */
  height: 100vh; /* Full viewport height from top to bottom */
  min-height: 100vh; /* Ensure minimum full height */
  z-index: 50; /* Higher than footer (z-20) */
  transition: background 0.4s ease, box-shadow 0.4s ease;
}

.dark .space-sidebar {
  background: rgba(10, 10, 26, 0.6);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.3);
}

/* When sidebar is static (desktop), also use full height */
.space-sidebar.lg\:static {
  height: 100vh;
  min-height: 100vh;
}


/* Header - Aether: Soft shadow instead of border */
.sidebar-header {
  position: relative;
  border: none; /* No border - use shadow */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04); /* Soft shadow for separation */
  padding: 1rem 0;
  z-index: 10;
  transition: box-shadow 0.3s ease;
}

.dark .sidebar-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--accent-color);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(9, 132, 227, 0.3);
  transition: all 0.4s ease;
}

.dark .logo-icon {
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.05em;
  transition: color 0.4s ease;
}

.dark .logo-text {
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}


/* Navigation */
.sidebar-nav {
  position: relative;
  z-index: 5;
  padding: 1rem 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(6, 182, 212, 0.2);
  border-top-color: #06b6d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.nav-content {
  padding: 0 0.75rem;
}


.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item-wrapper {
  margin-bottom: 0.25rem;
}

/* Menu Item */
.menu-item {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: 12px;
  color: var(--text-body);
  text-decoration: none;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 3px solid transparent;
  background: transparent;
  cursor: pointer;
  font-size: 0.9375rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.dark .menu-item {
  color: rgba(255, 255, 255, 0.7);
}

.menu-item:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--text-heading);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.dark .menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
  box-shadow: none;
}

.menu-item-active {
  background: rgba(9, 132, 227, 0.1);
  border-left-color: var(--accent-color);
  color: var(--accent-color);
  box-shadow: 
    inset 2px 0 0 var(--accent-color),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.dark .menu-item-active {
  background: rgba(6, 182, 212, 0.1);
  border-left-color: #06b6d4;
  color: #06b6d4;
  box-shadow: 
    inset 0 0 20px rgba(6, 182, 212, 0.1),
    0 0 15px rgba(6, 182, 212, 0.2);
}


.menu-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-icon {
  width: 20px;
  height: 20px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--icon-color);
  stroke-width: 2;
}

.dark .menu-icon {
  color: rgba(255, 255, 255, 0.7);
}

.menu-item:hover .menu-icon {
  transform: translateX(3px);
  color: var(--accent-color);
}

.dark .menu-item:hover .menu-icon {
  color: #06b6d4;
  filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.6));
}

.menu-icon.icon-active {
  color: var(--accent-color);
}

.dark .menu-icon.icon-active {
  color: #06b6d4;
  filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.6));
}

.menu-text {
  flex: 1;
  text-align: left;
}

.menu-badge {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  color: #ef4444;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.chevron-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.3s;
  color: rgba(255, 255, 255, 0.5);
}


/* Submenu */
.submenu-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 2rem;
  border-left: 2px solid var(--border-color);
  padding-left: 1rem;
  transition: border-color 0.3s ease;
}

.dark .submenu-list {
  border-left: 2px solid rgba(255, 255, 255, 0.1);
}

.submenu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  color: var(--text-body);
  text-decoration: none;
  transition: all 0.3s;
  font-size: 0.875rem;
}

.dark .submenu-item {
  color: rgba(255, 255, 255, 0.6);
}

.submenu-item:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--text-heading);
}

.dark .submenu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
}

.submenu-item-active {
  background: rgba(9, 132, 227, 0.1);
  color: var(--accent-color);
  border-left: 2px solid var(--accent-color);
  padding-left: 0.875rem;
}

.dark .submenu-item-active {
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
  border-left: 2px solid #06b6d4;
}

.submenu-icon {
  width: 16px;
  height: 16px;
  color: var(--icon-color);
  stroke-width: 2;
}

.dark .submenu-icon {
  color: rgba(255, 255, 255, 0.5);
}

.submenu-icon.icon-active {
  color: var(--accent-color);
}

.dark .submenu-icon.icon-active {
  color: #06b6d4;
}

.submenu-text {
  flex: 1;
}

.submenu-badge {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  color: #ef4444;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-size: 0.625rem;
  font-weight: 600;
}

/* Footer - Aether: Soft shadow instead of border */
.sidebar-footer {
  border: none; /* No border - use shadow */
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.04); /* Soft shadow for separation */
  padding: 1rem 0.75rem;
  background: rgba(0, 0, 0, 0.01);
  transition: box-shadow 0.4s ease, background 0.4s ease;
}

.dark .sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
  background: rgba(0, 0, 0, 0.2);
}

/* Error Dashboard Button */
.error-dashboard-container {
  margin-bottom: 1rem;
}

.error-dashboard-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  color: #ef4444;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.875rem;
  font-weight: 500;
  position: relative;
}

.error-dashboard-button:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
}

.error-dashboard-text {
  flex: 1;
  text-align: left;
}


/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}


.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

/* Responsive */
@media (max-width: 1024px) {
  .space-sidebar {
    width: 260px !important;
  }
  
  .space-sidebar.w-20 {
    width: 260px !important;
  }
}
</style>
