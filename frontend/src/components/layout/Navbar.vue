<template>
  <nav class="sleek-navbar">
    <div
      v-if="authStore.impersonation?.active"
      class="w-full bg-amber-500/90 dark:bg-amber-700/90 text-slate-900 dark:text-amber-50 px-4 py-2 flex flex-wrap items-center justify-between gap-2 text-sm"
      role="status"
    >
      <span
        >Impersonation: signed in as <strong>{{ authStore.user?.username }}</strong> ({{
          authStore.user?.email
        }})</span
      >
      <button
        type="button"
        class="underline font-medium shrink-0"
        @click="exitImpersonation"
      >
        Exit to admin
      </button>
    </div>
    <div class="navbar-container">
      <div class="navbar-content">
        <!-- Left: Sidebar Toggle + Breadcrumb -->
        <div class="navbar-left">
          <!-- Sidebar Toggle (Mobile/Tablet) -->
          <button
            @click="$emit('toggle-sidebar')"
            class="sidebar-toggle"
            aria-label="Toggle sidebar"
          >
            <Bars3Icon class="w-5 h-5" />
          </button>

          <!-- Breadcrumb -->
          <nav class="breadcrumb-nav">
            <router-link
              to="/dashboard"
              class="breadcrumb-item"
            >
              Dashboard
            </router-link>
            <template v-if="breadcrumbs.length > 0">
              <span class="breadcrumb-separator">›</span>
              <span
                v-for="(crumb, index) in breadcrumbs"
                :key="`${crumb.path || crumb.label}-${index}`"
              >
                <router-link
                  v-if="index < breadcrumbs.length - 1"
                  :to="crumb.path"
                  class="breadcrumb-item breadcrumb-link"
                >
                  {{ crumb.label }}
                </router-link>
                <span
                  v-else
                  class="breadcrumb-item breadcrumb-current"
                >
                  {{ crumb.label }}
                </span>
                <span
                  v-if="index < breadcrumbs.length - 1"
                  class="breadcrumb-separator"
                >
                  ›
                </span>
              </span>
            </template>
          </nav>
        </div>

        <!-- Center: Ghost Search -->
        <div class="navbar-center">
          <div class="ghost-search" :class="{ 'search-expanded': searchExpanded }">
            <button
              v-if="!searchExpanded"
              @click="searchExpanded = true"
              class="search-trigger"
              aria-label="Search"
            >
              <MagnifyingGlassIcon class="w-4 h-4" />
            </button>
            <div v-else class="search-input-wrapper">
              <MagnifyingGlassIcon class="w-4 h-4 search-icon" />
              <input
                ref="searchInput"
                v-model="searchQuery"
                type="text"
                placeholder="Search..."
                class="search-input"
                @blur="handleSearchBlur"
                @keyup.esc="closeSearch"
              />
              <button
                @click="closeSearch"
                class="search-close"
                aria-label="Close search"
              >
                <XMarkIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Icons -->
        <div class="navbar-right">
          <!-- Theme Toggle -->
          <ThemeToggle />
          
          <!-- Notifications -->
          <div class="icon-button-wrapper">
            <button
              @click="toggleNotifications"
              class="icon-button"
              :class="{ 'bell-shake': bellShake }"
              aria-label="Notifications"
            >
              <BellIcon class="w-5 h-5 icon-thin" />
              <span
                v-if="unreadNotifications > 0"
                class="notification-dot notification-dot-neon"
              ></span>
            </button>

            <!-- Notifications Dropdown -->
            <transition name="slide-down">
              <div
                v-if="showNotifications"
                ref="notificationsDropdown"
                class="notifications-dropdown space-dropdown"
              >
                <div class="dropdown-header">
                  <h3 class="dropdown-title">Notifications</h3>
                  <div class="flex items-center gap-2">
                    <button
                      v-if="unreadNotifications > 0"
                      @click="markAllAsRead"
                      class="dropdown-action space-action"
                    >
                      Mark all read
                    </button>
                    <button
                      v-if="notifications.length > 0"
                      @click="clearNotifications"
                      class="dropdown-action space-action"
                    >
                      Clear all
                    </button>
                  </div>
                </div>
                <div class="dropdown-content">
                  <div
                    v-if="notifications.length === 0"
                    class="dropdown-empty space-empty"
                  >
                    <SparklesIcon class="w-5 h-5 empty-icon" />
                    <p>All systems clear. No new alerts.</p>
                  </div>
                  <div
                    v-for="notification in notifications"
                    :key="notification.id"
                    :class="[
                      'notification-item space-notification-item',
                      !notification.is_read ? 'notification-unread' : ''
                    ]"
                    @click="handleNotificationClick(notification)"
                  >
                    <component
                      :is="getNotificationIcon(notification.type)"
                      :class="[
                        'notification-icon',
                        `icon-${notification.type}`
                      ]"
                    />
                    <div class="notification-content">
                      <p class="notification-title">{{ notification.title }}</p>
                      <p class="notification-message">{{ notification.message }}</p>
                      <p class="notification-time">{{ formatTime(notification.created_at) }}</p>
                    </div>
                    <button
                      class="notification-dismiss"
                      aria-label="Dismiss notification"
                      @click.stop="dismissNotification(notification.id)"
                    >
                      <XMarkIcon class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- User Menu -->
          <div class="icon-button-wrapper">
            <button
              @click="toggleUserMenu"
              class="icon-button"
              aria-label="User menu"
            >
              <UserIcon class="w-5 h-5 icon-thin" />
            </button>

            <!-- User Dropdown -->
            <div
              v-if="showUserMenu"
              ref="userMenuDropdown"
              class="user-dropdown"
            >
              <div class="dropdown-header">
                <p class="user-name">{{ user?.username || 'Guest' }}</p>
                <p class="user-email">{{ user?.email || '' }}</p>
              </div>
              <div class="dropdown-menu">
                <router-link
                  to="/profile"
                  class="dropdown-item"
                  @click="closeUserMenu"
                >
                  <UserIcon class="w-4 h-4" />
                  Profile
                </router-link>
                <router-link
                  to="/security"
                  class="dropdown-item"
                  @click="closeUserMenu"
                >
                  <ShieldCheckIcon class="w-4 h-4" />
                  Security
                </router-link>
                <router-link
                  to="/sessions"
                  class="dropdown-item"
                  @click="closeUserMenu"
                >
                  <DevicePhoneMobileIcon class="w-4 h-4" />
                  Sessions
                </router-link>
                <div class="dropdown-divider"></div>
                <button
                  @click="handleLogout"
                  class="dropdown-item dropdown-item-danger"
                >
                  <ArrowRightOnRectangleIcon class="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notificationsStore'
import {
  Bars3Icon,
  ChevronRightIcon,
  BellIcon,
  UserIcon,
  ShieldCheckIcon,
  DevicePhoneMobileIcon,
  ArrowRightOnRectangleIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

defineEmits(['toggle-sidebar'])

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

async function exitImpersonation() {
  try {
    await authStore.stopPlatformImpersonation()
    await router.push('/super-admin')
  } catch (e) {
    console.error(e)
  }
}

// UI State
const showNotifications = ref(false)
const showUserMenu = ref(false)
const searchExpanded = ref(false)
const searchQuery = ref('')
const searchInput = ref(null)
const notificationsDropdown = ref(null)
const userMenuDropdown = ref(null)
const bellShake = ref(false)

// Notifications from store
const notifications = computed(() => notificationsStore.notifications)
const unreadNotifications = computed(() => notificationsStore.unreadCount)

// User
const user = computed(() => authStore.user)

// Breadcrumb generation
const breadcrumbs = computed(() => {
  const paths = route.path.split('/').filter(Boolean)
  const crumbs = []
  
  if (paths.length <= 1 && paths[0] === 'dashboard') {
    return []
  }

  let currentPath = ''
  paths.forEach((path, index) => {
    currentPath += `/${path}`
    
    if (path === 'dashboard') return
    
    const label = path
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
    
    crumbs.push({
      path: currentPath,
      label: label
    })
  })
  
  return crumbs
})

// Search handlers
const closeSearch = () => {
  searchExpanded.value = false
  searchQuery.value = ''
}

const handleSearchBlur = (e) => {
  // Don't close if clicking inside dropdown
  if (!e.relatedTarget || !e.relatedTarget.closest('.notifications-dropdown, .user-dropdown')) {
    setTimeout(() => {
      if (!searchQuery.value) {
        closeSearch()
      }
    }, 200)
  }
}

// Toggle functions
const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    showUserMenu.value = false
  }
}

const closeNotifications = () => {
  showNotifications.value = false
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
  if (showUserMenu.value) {
    showNotifications.value = false
  }
}

const closeUserMenu = () => {
  showUserMenu.value = false
}

// Click outside handler
const handleClickOutside = (event) => {
  if (showNotifications.value && notificationsDropdown.value) {
    const button = event.target.closest('.icon-button')
    if (!notificationsDropdown.value.contains(event.target) && !button) {
      closeNotifications()
    }
  }
  
  if (showUserMenu.value && userMenuDropdown.value) {
    const button = event.target.closest('.icon-button')
    if (!userMenuDropdown.value.contains(event.target) && !button) {
      closeUserMenu()
    }
  }
}

// Notification handlers
const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await notificationsStore.markAsRead(notification.id)
  }
}

const markAllAsRead = async () => {
  await notificationsStore.markAllAsRead()
}

const clearNotifications = async () => {
  await notificationsStore.clearAll()
}

const dismissNotification = async (notificationId) => {
  await notificationsStore.dismiss(notificationId)
}

// Get icon component for notification type
const getNotificationIcon = (type) => {
  switch (type) {
    case 'error':
      return ExclamationCircleIcon
    case 'success':
      return CheckCircleIcon
    case 'warning':
      return ExclamationTriangleIcon
    case 'info':
    default:
      return InformationCircleIcon
  }
}

const formatTime = (dateString) => {
  if (!dateString) return 'Just now'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

// Watch for new notifications and trigger bell shake (skip initial sync)
let previousUnreadCount = -1
watch(unreadNotifications, (newCount) => {
  if (previousUnreadCount >= 0 && newCount > previousUnreadCount) {
    bellShake.value = true
    setTimeout(() => {
      bellShake.value = false
    }, 600)
  }
  previousUnreadCount = newCount
})

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}

// Focus search input when expanded
watch(searchExpanded, async (expanded) => {
  if (expanded) {
    await nextTick()
    searchInput.value?.focus()
  }
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  
  // Start polling for notifications if user is authenticated
  if (authStore.isAuthenticated) {
    notificationsStore.startPolling(30000) // Poll every 30 seconds
    previousUnreadCount = unreadNotifications.value
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  notificationsStore.stopPolling()
})
</script>

<style scoped>
.sleek-navbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--surface-3); /* More solid to avoid transparent look */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: none; /* No borders - Aether uses soft shadows */
  box-shadow: var(--shadow-soft); /* Soft shadow instead of border */
  transition: all 0.4s ease;
}

.dark .sleek-navbar {
  background: var(--surface-3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: var(--shadow-soft);
}

.navbar-container {
  padding: 0 1.5rem;
}

.navbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 3.5rem;
  gap: 1.5rem;
}

/* Left Section */
.navbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 0;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.4s ease;
}

.sidebar-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-main);
}

.dark .sidebar-toggle {
  color: rgba(255, 255, 255, 0.7);
}

.dark .sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

@media (min-width: 1024px) {
  .sidebar-toggle {
    display: none;
  }
}

/* Breadcrumb */
.breadcrumb-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  overflow: hidden;
  transition: color 0.4s ease;
}

.dark .breadcrumb-nav {
  color: rgba(255, 255, 255, 0.5);
}

.breadcrumb-item {
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.4s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .breadcrumb-item {
  color: rgba(255, 255, 255, 0.5);
}

.breadcrumb-item:hover {
  color: var(--text-main);
}

.dark .breadcrumb-item:hover {
  color: rgba(255, 255, 255, 0.8);
}

.breadcrumb-link {
  cursor: pointer;
}

.breadcrumb-current {
  color: var(--text-main);
  font-weight: 500;
}

.dark .breadcrumb-current {
  color: rgba(255, 255, 255, 0.9);
}

.breadcrumb-separator {
  color: var(--text-muted);
  font-size: 0.75rem;
  user-select: none;
  opacity: 0.5;
}

.dark .breadcrumb-separator {
  color: rgba(255, 255, 255, 0.3);
}

/* Center: Ghost Search */
.navbar-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.ghost-search {
  position: relative;
  display: flex;
  align-items: center;
}

.search-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.4s ease;
}

.search-trigger:hover {
  color: var(--accent-color);
  background: rgba(9, 132, 227, 0.1);
}

.dark .search-trigger {
  color: rgba(255, 255, 255, 0.6);
}

.dark .search-trigger:hover {
  color: #00d2ff;
  background: rgba(0, 210, 255, 0.1);
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--card-bg); /* Frosted glass with 80% opacity */
  border: none; /* No borders - Aether uses soft shadows */
  border-radius: 8px;
  min-width: 250px;
  box-shadow: var(--shadow-soft); /* Soft shadow instead of border */
  animation: searchExpand 0.3s ease;
  transition: all 0.4s ease;
}

.dark .search-input-wrapper {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
}

@keyframes searchExpand {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.search-icon {
  color: var(--text-muted);
  flex-shrink: 0;
  transition: color 0.4s ease;
}

.dark .search-icon {
  color: rgba(255, 255, 255, 0.5);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-main);
  font-size: 0.875rem;
  min-width: 0;
  transition: color 0.4s ease;
}

.dark .search-input {
  color: rgba(255, 255, 255, 0.9);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.dark .search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.search-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.search-close:hover {
  color: var(--text-main);
  background: rgba(15, 23, 42, 0.08);
}

.dark .search-close {
  color: rgba(255, 255, 255, 0.5);
}

.dark .search-close:hover {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.1);
}

/* Right Section */
.navbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 0 0 auto;
}

.icon-button-wrapper {
  position: relative;
}

.icon-button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.4s ease;
}

.icon-button:hover {
  color: var(--accent-color);
  background: rgba(9, 132, 227, 0.1);
}

.dark .icon-button {
  color: rgba(255, 255, 255, 0.6);
}

.dark .icon-button:hover {
  color: #00d2ff;
  background: rgba(0, 210, 255, 0.1);
}

.icon-thin {
  stroke-width: 1.5;
}

.notification-dot {
  position: absolute;
  top: 0.375rem;
  right: 0.375rem;
  width: 0.5rem;
  height: 0.5rem;
  background: var(--accent-color);
  border-radius: 50%;
  box-shadow: 0 0 4px rgba(9, 132, 227, 0.4);
  animation: pulse 2s ease-in-out infinite;
}

.dark .notification-dot {
  background: #00d2ff;
  box-shadow: 0 0 8px rgba(0, 210, 255, 0.8);
}

.notification-dot-neon {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
  animation: pulse 2s ease-in-out infinite;
}

.dark .notification-dot-neon {
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.9), 0 0 20px rgba(239, 68, 68, 0.6);
  animation: neonPulse 2s ease-in-out infinite;
}

@keyframes neonPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.9), 0 0 20px rgba(239, 68, 68, 0.6);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.2);
    box-shadow: 0 0 15px rgba(239, 68, 68, 1), 0 0 30px rgba(239, 68, 68, 0.8);
  }
}

.bell-shake {
  animation: bellShake 0.6s ease-in-out;
}

@keyframes bellShake {
  0%, 100% {
    transform: rotate(0deg);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: rotate(-10deg);
  }
  20%, 40%, 60%, 80% {
    transform: rotate(10deg);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* Dropdowns */
.notifications-dropdown,
.user-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  width: 20rem;
  background: var(--card-bg); /* Frosted glass with 80% opacity */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: none; /* No borders - Aether uses soft shadows */
  border-radius: 12px;
  box-shadow: var(--shadow-medium); /* Soft shadow instead of border */
  z-index: 50;
  transition: all 0.4s ease;
}

.dark .notifications-dropdown,
.dark .user-dropdown {
  background: rgba(10, 10, 26, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.space-dropdown {
  background: var(--card-bg); /* Frosted glass with 80% opacity */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: none; /* No borders - Aether uses soft shadows */
  box-shadow: var(--shadow-soft); /* Soft shadow instead of border */
}

.dark .space-dropdown {
  background: rgba(10, 10, 26, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 210, 255, 0.1);
}

/* Slide down animation */
.slide-down-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-5px) scale(0.98);
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.dropdown-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-heading);
}

.dark .dropdown-title {
  color: rgba(255, 255, 255, 0.9);
}

.dropdown-action {
  font-size: 0.75rem;
  color: var(--accent-color);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dropdown-action:hover {
  opacity: 0.8;
}

.space-action {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.space-action:hover {
  background: rgba(37, 99, 235, 0.1);
  color: var(--accent-color);
  box-shadow: 0 0 10px rgba(37, 99, 235, 0.2);
}

.dark .space-action:hover {
  background: rgba(0, 210, 255, 0.1);
  color: #00d2ff;
  box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

.user-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.dark .user-name {
  color: rgba(255, 255, 255, 0.9);
}

.dark .user-email {
  color: rgba(255, 255, 255, 0.5);
}

.dropdown-content {
  max-height: 24rem;
  overflow-y: auto;
}

.dropdown-empty {
  padding: 2rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.dark .dropdown-empty {
  color: rgba(255, 255, 255, 0.5);
}

.space-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2.5rem 1.5rem;
}

.empty-icon {
  color: rgba(100, 116, 139, 0.7);
  opacity: 0.6;
}

.dark .empty-icon {
  color: rgba(255, 255, 255, 0.3);
}

.notification-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid var(--border-color);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: rgba(15, 23, 42, 0.05);
}

.dark .notification-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.space-notification-item {
  position: relative;
  overflow: hidden;
}

.space-notification-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
  transition: all 0.3s ease;
}

.space-notification-item:hover::before {
  background: rgba(0, 210, 255, 0.5);
  box-shadow: 0 0 10px rgba(0, 210, 255, 0.3);
}

.notification-unread {
  background: rgba(37, 99, 235, 0.08);
}

.notification-unread::before {
  background: rgba(37, 99, 235, 0.35);
}

.dark .notification-unread {
  background: rgba(0, 210, 255, 0.05);
}

.dark .notification-unread::before {
  background: rgba(0, 210, 255, 0.3);
}

.notification-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.notification-icon.icon-error {
  color: #ef4444;
  filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.6));
}

.notification-icon.icon-success {
  color: #10b981;
  filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.6));
}

.notification-icon.icon-warning {
  color: #f59e0b;
  filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.6));
}

.notification-icon.icon-info {
  color: #00d2ff;
  filter: drop-shadow(0 0 4px rgba(0, 210, 255, 0.6));
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-dismiss {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.notification-dismiss:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.notification-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-heading);
  margin-bottom: 0.25rem;
}

.notification-message {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.notification-time {
  font-size: 0.625rem;
  color: color-mix(in srgb, var(--text-muted) 80%, transparent);
}

.dark .notification-title {
  color: rgba(255, 255, 255, 0.9);
}

.dark .notification-message {
  color: rgba(255, 255, 255, 0.6);
}

.dark .notification-time {
  color: rgba(255, 255, 255, 0.4);
}

.dropdown-menu {
  padding: 0.5rem 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  color: var(--text-main);
  text-decoration: none;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.dropdown-item:hover {
  background: rgba(15, 23, 42, 0.06);
  color: var(--text-heading);
}

.dropdown-item svg {
  width: 1rem;
  height: 1rem;
  color: var(--text-muted);
}

.dark .dropdown-item {
  color: rgba(255, 255, 255, 0.7);
}

.dark .dropdown-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

.dark .dropdown-item svg {
  color: rgba(255, 255, 255, 0.5);
}

.dropdown-item-danger {
  color: rgba(239, 68, 68, 0.8);
}

.dropdown-item-danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.dropdown-divider {
  height: 1px;
  background: var(--border-color);
  margin: 0.5rem 0;
}

/* Responsive */
@media (max-width: 768px) {
  .navbar-center {
    display: none;
  }
  
  .breadcrumb-nav {
    font-size: 0.75rem;
  }
}
</style>
