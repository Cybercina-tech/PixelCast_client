<template>
  <AppLayout>
    <div class="space-y-6 max-w-6xl mx-auto pb-24">
      <!-- Page header (matches Profile / other panels) -->
      <div>
        <h1 class="text-2xl font-bold text-primary">Settings</h1>
        <p class="text-muted mt-1">Manage your account, display, notifications, and system preferences</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-[minmax(200px,260px)_1fr] gap-6 items-start">
        <!-- Sidebar -->
        <aside class="card-base rounded-2xl p-4 lg:sticky lg:top-24">
          <h2 class="text-sm font-semibold text-primary mb-3 pb-2 border-b border-border-color">Sections</h2>
          <nav class="flex flex-col gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              @click="activeTab = tab.id"
              :class="navTabClass(tab.id)"
            >
              <component :is="tab.icon" class="w-5 h-5 shrink-0" />
              <span>{{ tab.label }}</span>
            </button>
          </nav>
        </aside>

        <!-- Main content -->
        <div class="min-w-0">
          <Transition
            mode="out-in"
            enter-active-class="transition-opacity duration-200 ease-out"
            leave-active-class="transition-opacity duration-150 ease-in"
            enter-from-class="opacity-0"
            leave-to-class="opacity-0"
          >
            <!-- Profile -->
            <Card
              v-if="activeTab === 'profile'"
              key="profile"
              title="Profile Settings"
              subtitle="Manage your account information and preferences"
            >
              <div class="grid md:grid-cols-[auto_1fr] gap-8">
                <div class="flex flex-col items-center md:items-start gap-3">
                  <label class="label-base block text-sm">Profile Picture</label>
                  <div class="relative group">
                    <div
                      class="w-28 h-28 rounded-full overflow-hidden border-2 border-border-color bg-surface-inset flex items-center justify-center"
                    >
                      <img
                        v-if="profileSettings.avatar"
                        :src="profileSettings.avatar"
                        alt="Avatar"
                        class="w-full h-full object-cover"
                      />
                      <span v-else class="text-3xl font-bold text-primary">{{ userInitials }}</span>
                    </div>
                    <div
                      class="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity cursor-pointer"
                      @click="avatarInput?.click()"
                    >
                      <CameraIcon class="w-7 h-7 text-white" />
                    </div>
                    <input
                      ref="avatarInput"
                      type="file"
                      accept="image/*"
                      class="hidden"
                      @change="handleAvatarUpload"
                    />
                  </div>
                  <button
                    type="button"
                    class="btn-outline px-4 py-2 rounded-lg text-sm"
                    @click="avatarInput?.click()"
                  >
                    Change Photo
                  </button>
                </div>

                <div class="space-y-4 max-w-md">
                  <div>
                    <label class="label-base block text-sm mb-1">Username</label>
                    <input
                      v-model="profileSettings.username"
                      type="text"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="Enter username"
                      @input="markAsChanged"
                    />
                  </div>
                  <div>
                    <label class="label-base block text-sm mb-1">Email</label>
                    <input
                      v-model="profileSettings.email"
                      type="email"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="Enter email"
                      @input="markAsChanged"
                    />
                  </div>
                  <div>
                    <label class="label-base block text-sm mb-1">Full Name</label>
                    <input
                      v-model="profileSettings.fullName"
                      type="text"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="Enter full name"
                      @input="markAsChanged"
                    />
                  </div>
                  <div>
                    <label class="label-base block text-sm mb-1">Member Since</label>
                    <div
                      class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border-color bg-surface-inset text-sm text-primary"
                    >
                      <CalendarIcon class="w-4 h-4 text-muted shrink-0" />
                      <span>{{ memberSince }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <!-- Display -->
            <Card
              v-else-if="activeTab === 'display'"
              key="display"
              title="Display Settings"
              subtitle="Customize your visual experience"
            >
              <div class="space-y-6">
                <div>
                  <label class="label-base block text-sm mb-3">Global Theme</label>
                  <div class="grid grid-cols-2 gap-4">
                    <button
                      v-for="theme in themes"
                      :key="theme.id"
                      type="button"
                      @click="displaySettings.theme = theme.id; markAsChanged()"
                      :class="[
                        'min-h-[3.25rem] w-full min-w-0 flex items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm font-medium transition-all',
                        displaySettings.theme === theme.id
                          ? 'border-brand bg-surface-inset ring-1 ring-brand/30 text-brand'
                          : 'border-border-color bg-surface-inset text-primary hover:border-border-color hover:shadow-sm',
                      ]"
                    >
                      <component :is="theme.icon" class="w-5 h-5 shrink-0" />
                      <span class="truncate">{{ theme.label }}</span>
                    </button>
                  </div>
                </div>
                <div>
                  <label class="label-base block text-sm mb-1">Default Orientation</label>
                  <select
                    v-model="displaySettings.orientation"
                    class="select-base w-full px-3 py-2 rounded-lg"
                    @change="markAsChanged"
                  >
                    <option value="landscape">Landscape</option>
                    <option value="portrait">Portrait</option>
                    <option value="auto">Auto</option>
                  </select>
                </div>
                <div>
                  <label class="label-base block text-sm mb-1">Refresh Interval (seconds)</label>
                  <input
                    v-model.number="displaySettings.refreshInterval"
                    type="number"
                    min="1"
                    max="3600"
                    class="input-base w-full px-3 py-2 rounded-lg"
                    @input="markAsChanged"
                  />
                  <p class="text-xs text-muted mt-1">How often the dashboard refreshes data</p>
                </div>
              </div>
            </Card>

            <!-- Notifications -->
            <Card
              v-else-if="activeTab === 'notifications'"
              key="notifications"
              title="Notification Center"
              subtitle="Control what notifications you receive"
            >
              <div class="space-y-3">
                <div
                  v-for="row in notificationRows"
                  :key="row.title"
                  class="flex items-center justify-between gap-4 p-4 rounded-xl border border-border-color bg-surface-inset"
                >
                  <div class="min-w-0">
                    <h4 class="text-sm font-semibold text-primary">{{ row.title }}</h4>
                    <p class="text-xs text-muted mt-0.5">{{ row.description }}</p>
                  </div>
                  <NeonToggle
                    :model-value="row.get()"
                    @update:model-value="row.set($event); markAsChanged()"
                  />
                </div>
                <div class="pt-2">
                  <label class="label-base block text-sm mb-1">Notification Email</label>
                  <input
                    v-model="notificationSettings.notificationEmail"
                    type="email"
                    class="input-base w-full px-3 py-2 rounded-lg max-w-md"
                    placeholder="notifications@example.com"
                    @input="markAsChanged"
                  />
                </div>
              </div>
            </Card>

            <!-- Security -->
            <Card
              v-else-if="activeTab === 'security'"
              key="security"
              title="Security Settings"
              subtitle="Manage your account security and sessions"
            >
              <div class="space-y-6">
                <div>
                  <label class="label-base block text-sm mb-2">Change Password</label>
                  <div class="space-y-3 max-w-md">
                    <input
                      v-model="securitySettings.currentPassword"
                      type="password"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="Current password"
                      @input="markAsChanged"
                    />
                    <input
                      v-model="securitySettings.newPassword"
                      type="password"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="New password"
                      @input="markAsChanged"
                    />
                    <input
                      v-model="securitySettings.confirmPassword"
                      type="password"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="Confirm new password"
                      @input="markAsChanged"
                    />
                  </div>
                </div>
                <div>
                  <label class="label-base block text-sm mb-3">Active Sessions</label>
                  <div v-if="loadingSessions" class="flex items-center justify-center py-8 rounded-xl border border-border-color bg-surface-inset">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand" />
                  </div>
                  <div
                    v-else-if="sessionsError"
                    class="rounded-xl border border-error/20 bg-error/10 p-4 text-error text-sm break-words"
                  >
                    {{ sessionsError }}
                  </div>
                  <div v-else-if="sessions.length === 0" class="text-center py-8 text-muted text-sm rounded-xl border border-border-color bg-surface-inset">
                    No active sessions found
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="session in sessions"
                      :key="session.id"
                      class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-border-color bg-surface-inset"
                    >
                      <div class="flex items-start gap-3 min-w-0">
                        <component :is="sessionDeviceIcon(session.device)" class="w-5 h-5 text-muted shrink-0 mt-0.5" />
                        <div>
                          <p class="text-sm font-medium text-primary">{{ session.device || 'Unknown device' }}</p>
                          <p class="text-xs text-muted">IP: {{ session.ip_address || '—' }}</p>
                          <p class="text-xs text-muted mt-0.5">Last activity: {{ formatSessionDate(session.last_activity) }}</p>
                        </div>
                      </div>
                      <div class="flex items-center gap-3 shrink-0">
                        <span
                          v-if="session.current"
                          class="px-2 py-0.5 rounded text-xs font-medium bg-forest-green/15 text-forest-green border border-forest-green/30"
                        >
                          Current
                        </span>
                        <button
                          v-if="!session.current"
                          type="button"
                          class="btn-outline px-3 py-1.5 rounded-lg text-sm text-error border-error/30 hover:bg-error/10 disabled:opacity-50"
                          :disabled="terminatingSession === session.id"
                          @click="revokeSession(session.id)"
                        >
                          <span v-if="terminatingSession === session.id">Revoking…</span>
                          <span v-else>Revoke</span>
                        </button>
                      </div>
                    </div>
                    <div class="pt-2 border-t border-border-color">
                      <button
                        type="button"
                        class="btn-outline px-3 py-2 rounded-lg text-sm text-error border-error/30 hover:bg-error/10 disabled:opacity-50"
                        :disabled="loggingOutAllSessions"
                        @click="logoutAllSessions"
                      >
                        <span v-if="loggingOutAllSessions">Logging out…</span>
                        <span v-else>Log out from all sessions</span>
                      </button>
                      <p class="text-xs text-muted mt-2">You will need to sign in again on every device.</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <!-- System -->
            <Card
              v-else-if="activeTab === 'system'"
              key="system"
              title="System Settings"
              subtitle="Advanced system configuration"
            >
              <div class="space-y-4 max-w-2xl">
                <div>
                  <label class="label-base block text-sm mb-1">API Base URL</label>
                  <input
                    v-model="systemSettings.apiBaseUrl"
                    type="text"
                    class="input-base w-full px-3 py-2 rounded-lg font-mono text-sm"
                    placeholder="http://localhost:8000/api"
                    @input="markAsChanged"
                  />
                </div>
                <div>
                  <label class="label-base block text-sm mb-1">WebSocket URL</label>
                  <input
                    v-model="systemSettings.wsUrl"
                    type="text"
                    class="input-base w-full px-3 py-2 rounded-lg font-mono text-sm"
                    placeholder="ws://localhost:8000/ws/dashboard/"
                    @input="markAsChanged"
                  />
                </div>
                <div>
                  <label class="label-base block text-sm mb-1">Storage Backend</label>
                  <select
                    v-model="systemSettings.storageBackend"
                    class="select-base w-full px-3 py-2 rounded-lg"
                    @change="markAsChanged"
                  >
                    <option value="local">Local File System</option>
                    <option value="s3">Amazon S3</option>
                  </select>
                </div>
                <div v-if="systemSettings.storageBackend === 's3'" class="space-y-4">
                  <div>
                    <label class="label-base block text-sm mb-1">S3 Bucket Name</label>
                    <input
                      v-model="systemSettings.s3Bucket"
                      type="text"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="your-bucket-name"
                      @input="markAsChanged"
                    />
                  </div>
                  <div>
                    <label class="label-base block text-sm mb-1">S3 Region</label>
                    <input
                      v-model="systemSettings.s3Region"
                      type="text"
                      class="input-base w-full px-3 py-2 rounded-lg"
                      placeholder="us-east-1"
                      @input="markAsChanged"
                    />
                  </div>
                </div>
              </div>
            </Card>


          </Transition>
        </div>
      </div>

      <!-- Sticky save bar -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        leave-active-class="transition duration-150 ease-in"
        enter-from-class="opacity-0 translate-y-2"
        leave-to-class="opacity-0 translate-y-2"
      >
        <div
          v-if="hasChanges"
          class="fixed bottom-6 left-1/2 z-50 w-[calc(100%-2rem)] max-w-2xl -translate-x-1/2 px-2"
        >
          <div
            class="card-base flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-4 py-3 rounded-2xl border border-border-color shadow-lg"
          >
            <span class="text-sm text-primary font-medium">You have unsaved changes</span>
            <div class="flex items-center gap-2 justify-end">
              <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" @click="discardChanges">
                Discard
              </button>
              <button type="button" class="btn-primary px-4 py-2 rounded-lg text-sm" @click="saveChanges">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useNotification } from '@/composables/useNotification'
import { authAPI, notificationCenterAPI } from '@/services/api'
import { getBrowserApiBaseUrl } from '@/utils/apiBaseUrl'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import NeonToggle from '@/components/common/NeonToggle.vue'
import {
  UserIcon,
  PaintBrushIcon,
  BellIcon,
  ShieldCheckIcon,
  Cog6ToothIcon,
  KeyIcon,
  CameraIcon,
  CalendarIcon,
  ComputerDesktopIcon,
  DevicePhoneMobileIcon,
  MoonIcon,
  SunIcon,
} from '@heroicons/vue/24/outline'

const avatarInput = ref(null)
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const notify = useNotification()

const tabs = [
  { id: 'profile', label: 'Profile', icon: UserIcon },
  { id: 'display', label: 'Display', icon: PaintBrushIcon },
  { id: 'notifications', label: 'Notifications', icon: BellIcon },
  { id: 'security', label: 'Security', icon: ShieldCheckIcon },
  { id: 'system', label: 'System', icon: Cog6ToothIcon },
]

const activeTab = ref('profile')
const hasChanges = ref(false)

const user = computed(() => authStore.user)
const userInitials = computed(() => {
  if (!user.value?.username) return 'U'
  const parts = user.value.username.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return user.value.username.substring(0, 2).toUpperCase()
})

const memberSince = computed(() => {
  if (!user.value) return 'N/A'
  const dateStr = user.value.date_joined || user.value.created_at || user.value.joined_at
  if (!dateStr) return 'N/A'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
  } catch {
    return 'N/A'
  }
})

const profileSettings = ref({
  avatar: null,
  username: '',
  email: '',
  fullName: '',
})

const displaySettings = ref({
  theme: themeStore.theme || 'dark',
  orientation: 'landscape',
  refreshInterval: 30,
})

const themes = [
  { id: 'dark', label: 'Deep Space', icon: MoonIcon },
  { id: 'light', label: 'Light', icon: SunIcon },
]

const notificationSettings = ref({
  screenOffline: true,
  templatePush: true,
  systemUpdates: false,
  email: false,
  notificationEmail: user.value?.email || '',
})

const notificationRows = computed(() => [
  {
    title: 'Screen Offline Alerts',
    description: 'Get notified when a screen goes offline',
    get: () => notificationSettings.value.screenOffline,
    set: (v) => { notificationSettings.value.screenOffline = v },
  },
  {
    title: 'Template Push Success',
    description: 'Notifications when content is successfully deployed',
    get: () => notificationSettings.value.templatePush,
    set: (v) => { notificationSettings.value.templatePush = v },
  },
  {
    title: 'System Updates',
    description: 'Receive updates about system maintenance and new features',
    get: () => notificationSettings.value.systemUpdates,
    set: (v) => { notificationSettings.value.systemUpdates = v },
  },
  {
    title: 'Email Notifications',
    description: 'Send notifications via email',
    get: () => notificationSettings.value.email,
    set: (v) => { notificationSettings.value.email = v },
  },
])

const securitySettings = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const systemSettings = ref({
  apiBaseUrl: getBrowserApiBaseUrl(),
  wsUrl: import.meta.env.VITE_WS_HOST || 'ws://localhost:8000/ws/dashboard/',
  storageBackend: 'local',
  s3Bucket: '',
  s3Region: 'us-east-1',
})

const sessions = ref([])
const loadingSessions = ref(false)
const sessionsError = ref(null)


const terminatingSession = ref(null)
const loggingOutAllSessions = ref(false)

function sessionDeviceIcon(deviceLabel) {
  const d = (deviceLabel || '').toLowerCase()
  if (/iphone|ipad|ipod|android|mobile/.test(d)) {
    return DevicePhoneMobileIcon
  }
  return ComputerDesktopIcon
}

function formatSessionDate(dateString) {
  if (!dateString) return 'Never'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}



async function loadSessions() {
  loadingSessions.value = true
  sessionsError.value = null
  try {
    const { data } = await authAPI.sessions()
    sessions.value = data.sessions || []
  } catch (err) {
    sessionsError.value =
      err.response?.data?.detail || err.response?.data?.error || 'Failed to load sessions'
    console.error('Failed to load sessions:', err)
  } finally {
    loadingSessions.value = false
  }
}

const originalSettings = ref({
  profile: JSON.parse(JSON.stringify(profileSettings.value)),
  display: JSON.parse(JSON.stringify(displaySettings.value)),
  notifications: JSON.parse(JSON.stringify(notificationSettings.value)),
  security: JSON.parse(JSON.stringify(securitySettings.value)),
  system: JSON.parse(JSON.stringify(systemSettings.value)),
})

function navTabClass(tabId) {
  const base =
    'w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors border'
  if (activeTab.value === tabId) {
    return `${base} bg-surface-inset border-border-color text-primary ring-1 ring-brand/20`
  }
  return `${base} border-transparent text-muted hover:bg-surface-inset/80 hover:text-primary`
}

watch(user, (newUser) => {
  if (newUser) {
    profileSettings.value = {
      avatar: newUser.avatar || null,
      username: newUser.username || '',
      email: newUser.email || '',
      fullName: newUser.full_name || newUser.first_name + ' ' + newUser.last_name || '',
    }
    notificationSettings.value.notificationEmail = newUser.email || ''
    originalSettings.value.profile = JSON.parse(JSON.stringify(profileSettings.value))
  }
}, { immediate: true })

const markAsChanged = () => {
  hasChanges.value = true
}

const discardChanges = () => {
  profileSettings.value = JSON.parse(JSON.stringify(originalSettings.value.profile))
  displaySettings.value = JSON.parse(JSON.stringify(originalSettings.value.display))
  notificationSettings.value = JSON.parse(JSON.stringify(originalSettings.value.notifications))
  securitySettings.value = JSON.parse(JSON.stringify(originalSettings.value.security))
  systemSettings.value = JSON.parse(JSON.stringify(originalSettings.value.system))
  hasChanges.value = false
  notify.info('Changes discarded')
}

const saveChanges = async () => {
  try {
    if (activeTab.value === 'profile') {
      originalSettings.value.profile = JSON.parse(JSON.stringify(profileSettings.value))
    }

    if (activeTab.value === 'display') {
      if (displaySettings.value.theme !== themeStore.theme) {
        themeStore.setTheme(displaySettings.value.theme)
      }
      localStorage.setItem('displaySettings', JSON.stringify(displaySettings.value))
      originalSettings.value.display = JSON.parse(JSON.stringify(displaySettings.value))
    }

    if (activeTab.value === 'notifications') {
      await notificationCenterAPI.savePreferences({
        screen_offline: notificationSettings.value.screenOffline,
        template_push: notificationSettings.value.templatePush,
        system_updates: notificationSettings.value.systemUpdates,
        email_enabled: notificationSettings.value.email,
        notification_email: notificationSettings.value.notificationEmail,
      })
      originalSettings.value.notifications = JSON.parse(JSON.stringify(notificationSettings.value))
    }

    if (activeTab.value === 'security') {
      if (securitySettings.value.newPassword && securitySettings.value.newPassword === securitySettings.value.confirmPassword) {
        securitySettings.value.currentPassword = ''
        securitySettings.value.newPassword = ''
        securitySettings.value.confirmPassword = ''
        originalSettings.value.security = JSON.parse(JSON.stringify(securitySettings.value))
      }
    }

    if (activeTab.value === 'system') {
      localStorage.setItem('systemSettings', JSON.stringify(systemSettings.value))
      originalSettings.value.system = JSON.parse(JSON.stringify(systemSettings.value))
    }

    hasChanges.value = false
    notify.success('Settings saved successfully')
  } catch (error) {
    console.error('Error saving settings:', error)
    notify.error('Failed to save settings')
  }
}

const handleAvatarUpload = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      profileSettings.value.avatar = e.target?.result
      markAsChanged()
    }
    reader.readAsDataURL(file)
  }
}

async function revokeSession(sessionId) {
  terminatingSession.value = sessionId
  try {
    const oid = parseInt(sessionId, 10)
    await authAPI.revokeSession(Number.isFinite(oid) ? oid : sessionId)
    notify.success('Session revoked')
    await loadSessions()
  } catch (err) {
    notify.error(err.response?.data?.error || err.response?.data?.detail || 'Could not revoke session')
  } finally {
    terminatingSession.value = null
  }
}

async function logoutAllSessions() {
  loggingOutAllSessions.value = true
  try {
    await authAPI.logoutAll()
    notify.success('Logged out from all sessions')
    authStore.logout()
    router.push('/login')
  } catch (err) {
    notify.error(
      err.response?.data?.detail || err.response?.data?.error || 'Failed to log out from all sessions',
    )
  } finally {
    loggingOutAllSessions.value = false
  }
}

const loadSettings = () => {
  const savedDisplay = localStorage.getItem('displaySettings')
  if (savedDisplay) {
    displaySettings.value = { ...displaySettings.value, ...JSON.parse(savedDisplay) }
  }

  const savedSystem = localStorage.getItem('systemSettings')
  if (savedSystem) {
    systemSettings.value = { ...systemSettings.value, ...JSON.parse(savedSystem) }
  }
}

const loadNotificationPreferences = async () => {
  try {
    const { data } = await notificationCenterAPI.getPreferences()
    notificationSettings.value = {
      ...notificationSettings.value,
      screenOffline: Boolean(data?.screen_offline),
      templatePush: Boolean(data?.template_push),
      systemUpdates: Boolean(data?.system_updates),
      email: Boolean(data?.email_enabled),
      notificationEmail: data?.notification_email || notificationSettings.value.notificationEmail || '',
    }
    originalSettings.value.notifications = JSON.parse(JSON.stringify(notificationSettings.value))
  } catch (error) {
    console.error('Failed to load notification preferences:', error)
  }
}

function syncTabFromRoute() {
  const t = route.query.tab
  if (typeof t === 'string' && tabs.some((x) => x.id === t)) {
    activeTab.value = t
  }
}

watch(activeTab, (tab) => {
  hasChanges.value = false
  if (tab === 'security') {
    loadSessions()
  }
  if (tab === 'license') {
    loadLicenseSummary()
  }
})

watch(() => route.query.tab, () => {
  syncTabFromRoute()
})

onMounted(() => {
  syncTabFromRoute()
})

loadSettings()
loadNotificationPreferences()
</script>
