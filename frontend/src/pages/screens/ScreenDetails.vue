<template>
  <AppLayout>
    <!-- Loading State -->
    <div v-if="screensStore.loading && !screen" class="flex items-center justify-center min-h-[60vh]">
      <div class="text-center">
        <svg class="animate-spin h-12 w-12 text-brand mx-auto mb-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-muted">Loading screen details...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="screensStore.error && !screen" class="flex items-center justify-center min-h-[60vh]">
      <div class="text-center card-base rounded-2xl p-8">
        <svg class="w-16 h-16 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-xl font-semibold text-primary mb-2">Error Loading Screen</h3>
        <p class="text-secondary mb-4">{{ screensStore.error }}</p>
        <button @click="loadScreenData" class="btn-primary px-4 py-2 rounded-lg">Retry</button>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else-if="screen" class="space-y-6 pb-6">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-start gap-3 min-w-0">
          <button
            type="button"
            @click="goToScreensList"
            class="btn-outline px-3 py-2 rounded-lg text-sm font-medium transition-all duration-400 flex items-center gap-2 shrink-0 mt-0.5"
            title="Back to Screens"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back
          </button>
          <div class="min-w-0 flex-1">
            <div class="flex items-start gap-2 flex-wrap">
              <h1 class="text-3xl font-bold text-primary mb-2">{{ screen.name || 'Unnamed Screen' }}</h1>
              <button
                v-if="playerUrl"
                type="button"
                class="btn-outline p-2 rounded-lg shrink-0 mt-1"
                title="Copy player URL"
                aria-label="Copy player URL"
                @click="copyPlayerUrl"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
            <p class="text-secondary">{{ screen.device_id }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <!-- Online Status Indicator -->
          <div class="flex items-center gap-2 px-4 py-2 rounded-lg card-base">
            <div
              :class="[
                'w-3 h-3 rounded-full',
                isOnline ? 'bg-forest-green animate-pulse' : 'bg-dusty-red',
              ]"
            ></div>
            <span class="text-sm font-medium" :class="isOnline ? 'text-forest-green' : 'text-dusty-red'">
              {{ isOnline ? 'Online' : 'Offline' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Row 1: Live preview + remote controls (side-by-side on xl) -->
      <div class="grid grid-cols-1 xl:grid-cols-12 gap-4 md:gap-6">
        <div class="xl:col-span-7 min-w-0">
          <div class="card-base rounded-2xl p-6 h-full flex flex-col">
            <h2 class="text-lg font-semibold text-primary mb-4">Live Preview</h2>
            <div class="flex-1 min-h-0">
              <VirtualMonitor
                ref="virtualMonitorRef"
                :active-template="activeTemplatePreview"
                :is-online="isOnline"
                :loading="screenshotLoading"
                @take-screenshot="handleTakeScreenshot"
              />
            </div>
          </div>
        </div>
        <div class="xl:col-span-5 min-w-0">
          <div class="card-base rounded-2xl p-6 h-full flex flex-col">
            <h2 class="text-lg font-semibold text-primary mb-4">Remote Actions</h2>
            <p class="text-sm text-muted mb-4">Control this display. Primary actions are available first.</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-auto">
              <button
                type="button"
                class="btn-primary min-h-[44px] px-4 py-3 rounded-lg transition-all duration-400 flex items-center justify-center gap-2"
                :disabled="!isOnline || actionLoading"
                @click="handleRefresh"
              >
                <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh</span>
              </button>
              <button
                type="button"
                class="btn-primary min-h-[44px] px-4 py-3 rounded-lg transition-all duration-400 flex items-center justify-center gap-2"
                :disabled="actionLoading"
                @click="showTemplateModal = true"
              >
                <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Template</span>
              </button>
              <button
                type="button"
                class="btn-secondary min-h-[44px] px-4 py-3 rounded-lg transition-all duration-400 flex items-center justify-center gap-2"
                :disabled="!isOnline || actionLoading"
                @click="handleReboot"
              >
                <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Reboot</span>
              </button>
              <button
                type="button"
                class="btn-secondary min-h-[44px] px-4 py-3 rounded-lg transition-all duration-400 flex items-center justify-center gap-2"
                :disabled="!isOnline || actionLoading"
                @click="handleIdentify"
              >
                <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
                <span>Identify</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: General info + health -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div class="card-base rounded-2xl p-6">
          <h2 class="text-lg font-semibold text-primary mb-4">General Information</h2>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Device ID</dt>
              <dd class="text-sm text-primary font-mono break-all">{{ screen.device_id }}</dd>
            </div>
            <div>
              <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Name</dt>
              <dd class="text-sm text-primary min-w-0">
                <input
                  v-if="editingName"
                  v-model="editableName"
                  class="input-base w-full px-2 py-1 rounded"
                  autofocus
                  @blur="handleSaveName"
                  @keyup.enter="handleSaveName"
                  @keyup.esc="cancelEditName"
                />
                <span v-else class="cursor-pointer hover:text-blue-400 transition-colors" @click="startEditName">
                  {{ screen.name || 'Unnamed Screen' }}
                  <svg class="inline w-4 h-4 ml-1 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </span>
              </dd>
            </div>
            <div class="sm:col-span-2">
              <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Player URL</dt>
              <dd class="text-sm text-primary break-all space-y-2">
                <div class="font-mono text-xs sm:text-sm">{{ playerUrl }}</div>
                <button type="button" class="btn-outline px-3 py-1.5 rounded-lg text-xs" @click="copyPlayerUrl">
                  Copy URL
                </button>
              </dd>
            </div>
            <div>
              <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">IP Address</dt>
              <dd class="text-sm text-primary font-mono">{{ screen.last_ip || 'N/A' }}</dd>
            </div>
            <div>
              <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">OS Version</dt>
              <dd class="text-sm text-primary">{{ screen.os_version || 'N/A' }}</dd>
            </div>
            <div class="sm:col-span-2">
              <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">App Version</dt>
              <dd class="text-sm text-primary">{{ screen.app_version || 'N/A' }}</dd>
            </div>
          </dl>
        </div>

        <div class="card-base rounded-2xl p-6">
          <h2 class="text-lg font-semibold text-primary mb-4">Health Metrics</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6">
            <HealthGauge :value="healthMetrics.cpu_usage || 0" label="CPU" />
            <HealthGauge :value="healthMetrics.memory_usage || 0" label="Memory" />
          </div>
          <div class="mt-6 space-y-3">
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm text-muted">Latency</span>
              <span class="text-sm font-semibold text-primary tabular-nums">{{ healthMetrics.latency || 0 }}ms</span>
            </div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm text-muted">Last Heartbeat</span>
              <div class="flex items-center gap-2 min-w-0">
                <div
                  :class="[
                    'w-2 h-2 rounded-full shrink-0',
                    isOnline ? 'bg-green-500 animate-pulse' : 'bg-gray-500',
                  ]"
                ></div>
                <span class="text-sm text-primary truncate">{{ formatLastHeartbeat(screen.last_heartbeat_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Activity: commands vs logs -->
      <div class="card-base rounded-2xl overflow-hidden">
        <div class="px-4 pt-4 md:px-6 md:pt-6 border-b border-border-color/40">
          <div class="flex gap-1 overflow-x-auto border-b border-border-color/40 pb-px -mb-px">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap"
              :class="activityTab === 'commands'
                ? 'bg-card border border-b-0 border-border-color/70 text-primary'
                : 'text-muted hover:text-primary'"
              @click="activityTab = 'commands'"
            >
              Command Queue
            </button>
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap"
              :class="activityTab === 'logs'
                ? 'bg-card border border-b-0 border-border-color/70 text-primary'
                : 'text-muted hover:text-primary'"
              @click="activityTab = 'logs'"
            >
              Recent Logs
            </button>
          </div>
        </div>
        <div class="p-4 md:p-6 pt-4">
          <div v-show="activityTab === 'commands'" class="max-h-96 overflow-y-auto custom-scrollbar -mx-1 px-1">
            <CommandTimeline :commands="allCommands" />
          </div>
          <div v-show="activityTab === 'logs'" class="max-h-96 overflow-y-auto custom-scrollbar space-y-2 -mx-1 px-1">
            <div
              v-for="log in recentLogs"
              :key="log.id"
              class="p-3 bg-card rounded-lg border border-border-color hover:bg-card transition-colors duration-400"
            >
              <p class="text-sm text-primary">{{ log.message || `${log.status} - ${formatDate(log.recorded_at || log.created_at)}` }}</p>
              <p class="text-xs text-muted mt-1">{{ formatDate(log.recorded_at || log.created_at) }}</p>
            </div>
            <div v-if="recentLogs.length === 0" class="text-center text-muted py-8">
              <p class="text-sm">No logs available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Danger Zone (collapsed by default) -->
      <details class="danger-zone-details card-base rounded-2xl border-dusty-red/30">
        <summary
          class="cursor-pointer list-none px-6 py-4 flex items-center justify-between gap-3 text-lg font-semibold text-dusty-red select-none [&::-webkit-details-marker]:hidden outline-none focus-visible:ring-2 focus-visible:ring-dusty-red/40 rounded-2xl"
        >
          <span>Danger Zone</span>
          <svg
            class="w-5 h-5 shrink-0 text-dusty-red/80 transition-transform duration-200"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="px-6 pb-6 pt-0 space-y-6 border-t border-border-color/30">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p class="text-sm text-primary font-medium">Revoke Device Token</p>
              <p class="text-xs text-muted">Forces the TV back to pairing mode. It will need to be re-paired.</p>
            </div>
            <button
              type="button"
              :disabled="revokingToken"
              class="px-5 py-2 border-2 border-amber-500/50 hover:bg-amber-500/20 hover:border-amber-500 text-amber-400 rounded-lg transition-all duration-200 font-semibold disabled:opacity-50 shrink-0"
              @click="handleRevokeToken"
            >
              {{ revokingToken ? 'Revoking...' : 'Revoke Token' }}
            </button>
          </div>
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p class="text-sm text-primary font-medium">Delete Screen</p>
              <p class="text-xs text-muted">Permanently remove this screen from your system.</p>
            </div>
            <button
              type="button"
              class="px-6 py-2 border-2 border-red-500/50 hover:bg-red-500/20 hover:border-red-500 text-red-400 rounded-lg transition-all duration-200 font-semibold shrink-0"
              @click="handleDeleteScreen"
            >
              Delete Screen
            </button>
          </div>
        </div>
      </details>

      <!-- Modals -->
      <Modal :show="showCommandModal" title="Send Command" @close="showCommandModal = false">
        <div class="space-y-4">
          <div v-if="commandFormError" class="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {{ commandFormError }}
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Command Type</label>
            <select v-model="commandForm.type" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="restart">Restart</option>
              <option value="refresh">Refresh</option>
              <option value="change_template">Change Template</option>
              <option value="display_message">Display Message</option>
              <option value="sync_content">Sync Content</option>
              <option value="custom">Custom</option>
            </select>
            <p v-if="commandFieldErrors.type" class="mt-1 text-xs text-red-400">{{ commandFieldErrors.type[0] }}</p>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Payload (JSON)</label>
            <textarea
              v-model="commandForm.payload"
              rows="4"
              class="textarea-base w-full px-3 py-2 rounded-lg font-mono text-sm"
              placeholder='{"key": "value"}'
            ></textarea>
            <p v-if="commandFieldErrors.payload" class="mt-1 text-xs text-red-400">{{ commandFieldErrors.payload[0] }}</p>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Priority</label>
            <input
              v-model.number="commandForm.priority"
              type="number"
              min="1"
              max="10"
              value="5"
              class="input-base w-full px-3 py-2 rounded-lg"
            />
            <p v-if="commandFieldErrors.priority" class="mt-1 text-xs text-red-400">{{ commandFieldErrors.priority[0] }}</p>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleSendCommand" class="btn-primary px-4 py-2 rounded-lg">
            Send Command
          </button>
          <button type="button" @click="showCommandModal = false" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>

      <Modal :show="showTemplateModal" title="Activate Template" @close="showTemplateModal = false">
        <div class="space-y-4">
          <div v-if="templateFormError" class="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {{ templateFormError }}
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Template</label>
            <select v-model="templateForm.template_id" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="">Select a template</option>
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}
              </option>
            </select>
            <p v-if="templateFieldErrors.template_id || templateFieldErrors.template" class="mt-1 text-xs text-red-400">{{ (templateFieldErrors.template_id || templateFieldErrors.template)[0] }}</p>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleActivateTemplate" class="btn-primary px-4 py-2 rounded-lg">
            Activate
          </button>
          <button type="button" @click="showTemplateModal = false" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
    </div>

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmation />
  </AppLayout>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { smartUpdateArray } from '@/utils/deepCompare'
import { useScreensStore } from '@/stores/screens'
import { useTemplatesStore } from '@/stores/templates'
import { useCommandsStore } from '@/stores/commands'
import { useLogsStore } from '@/stores/logs'
import { screensAPI } from '@/services/api'
import { useNotification } from '@/composables/useNotification'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import { normalizeApiError } from '@/utils/apiError'
import AppLayout from '@/components/layout/AppLayout.vue'
import Modal from '@/components/common/Modal.vue'
import DeleteConfirmation from '@/components/common/DeleteConfirmation.vue'
import HealthGauge from '@/components/screens/HealthGauge.vue'
import VirtualMonitor from '@/components/screens/VirtualMonitor.vue'
import CommandTimeline from '@/components/screens/CommandTimeline.vue'

const route = useRoute()
const router = useRouter()
const screensStore = useScreensStore()
const templatesStore = useTemplatesStore()
const commandsStore = useCommandsStore()
const logsStore = useLogsStore()
const notify = useNotification()
const { confirmDelete } = useDeleteConfirmation()

const screen = computed(() => screensStore.currentScreen)
const templates = computed(() => templatesStore.templates)
const isOnline = computed(() => screensStore.getScreenStatus(screen.value) === 'online')
const activeTemplateId = computed(() => screen.value?.active_template?.id || null)
const activeTemplatePreview = computed(() => {
  if (!activeTemplateId.value) return null
  const fromList = templatesStore.templates.find(t => t.id === activeTemplateId.value)
  if (fromList?.layers) return fromList
  if (templatesStore.currentTemplate?.id === activeTemplateId.value) return templatesStore.currentTemplate
  return screen.value?.active_template || null
})
const playerUrl = computed(() => {
  const screenId = screen.value?.id || getScreenId()
  if (!screenId) return ''
  const origin = window.location.origin
  return `${origin}/player/${screenId}`
})

const pendingCommands = ref([])
const commandHistory = ref([])
const recentLogs = ref([])
const healthMetrics = ref({
  cpu_usage: 0,
  memory_usage: 0,
  latency: 0,
})

const activityTab = ref('commands')
const showCommandModal = ref(false)
const showTemplateModal = ref(false)
const editingName = ref(false)
const editableName = ref('')
const actionLoading = ref(false)
const screenshotLoading = ref(false)
const revokingToken = ref(false)
const virtualMonitorRef = ref(null)

const commandForm = ref({
  type: 'restart',
  payload: '{}',
  priority: 5,
})
const commandFormError = ref('')
const templateFormError = ref('')
const commandFieldErrors = ref({})
const templateFieldErrors = ref({})

const templateForm = ref({
  template_id: '',
})

// Combine pending and recent commands for timeline
const allCommands = computed(() => {
  return [...pendingCommands.value, ...commandHistory.value].sort((a, b) => {
    return new Date(b.created_at) - new Date(a.created_at)
  })
})

let refreshInterval = null

// Fix route parameter handling - use route.params.id
const getScreenId = () => {
  // Try route.params.id first (standard Vue Router param)
  if (route.params.id) {
    return route.params.id
  }
  // Fallback to route.query.id if params not available
  if (route.query.id) {
    return route.query.id
  }
  return null
}

const goToScreensList = () => {
  router.push({ name: 'screens' })
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const copyPlayerUrl = async () => {
  if (!playerUrl.value) return
  try {
    await navigator.clipboard.writeText(playerUrl.value)
    notify.success('Player URL copied')
  } catch (_) {
    notify.error('Failed to copy player URL')
  }
}

const formatLastHeartbeat = (dateString) => {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffSecs = Math.floor((diffMs % 60000) / 1000)
  
  if (diffMins < 1) {
    return `${diffSecs}s ago`
  } else if (diffMins < 60) {
    return `${diffMins}m ago`
  } else {
    const diffHours = Math.floor(diffMins / 60)
    return `${diffHours}h ago`
  }
}

const startEditName = () => {
  editingName.value = true
  editableName.value = screen.value?.name || ''
}

const cancelEditName = () => {
  editingName.value = false
  editableName.value = ''
}

const getErrorMessage = (error, fallback) => {
  const parsed = error?.apiError || normalizeApiError(error)
  return parsed.userMessage || fallback
}

const handleSaveName = async () => {
  if (!editableName.value.trim()) {
    cancelEditName()
    return
  }
  
  try {
    await screensStore.updateScreen(screen.value.id, { name: editableName.value.trim() })
    editingName.value = false
    notify.success('Screen name updated')
  } catch (error) {
    notify.error(getErrorMessage(error, 'Failed to update name'))
  }
}

const handleSendCommand = async () => {
  commandFormError.value = ''
  commandFieldErrors.value = {}
  try {
    let payload = {}
    try {
      payload = JSON.parse(commandForm.value.payload)
    } catch (e) {
      payload = { message: commandForm.value.payload }
    }
    
    await commandsStore.createCommand({
      screen_id: screen.value.id,
      type: commandForm.value.type,
      payload,
      priority: commandForm.value.priority,
    })
    
    notify.success('Command sent successfully')
    showCommandModal.value = false
    commandForm.value = { type: 'restart', payload: '{}', priority: 5 }
    await loadCommands()
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    commandFormError.value = parsed.formError
    commandFieldErrors.value = parsed.fieldErrors || {}
    if (!parsed.isValidation || !Object.keys(commandFieldErrors.value).length) {
      notify.error(parsed.userMessage || 'Failed to send command')
    }
  }
}

const handleActivateTemplate = async () => {
  templateFormError.value = ''
  templateFieldErrors.value = {}
  try {
    await templatesStore.activateOnScreen(
      templateForm.value.template_id,
      screen.value.id,
      true
    )
    
    notify.success('Template activated successfully')
    showTemplateModal.value = false
    templateForm.value = { template_id: '' }
    
    // Refresh screen data
    await screensStore.fetchScreen(screen.value.id)
    if (activeTemplateId.value) {
      await templatesStore.fetchTemplate(activeTemplateId.value)
    }
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    templateFormError.value = parsed.formError
    templateFieldErrors.value = parsed.fieldErrors || {}
    if (!parsed.isValidation || !Object.keys(templateFieldErrors.value).length) {
      notify.error(parsed.userMessage || 'Failed to activate template')
    }
  }
}

const handleRefresh = async () => {
  actionLoading.value = true
  try {
    await commandsStore.createCommand({
      screen_id: screen.value.id,
      type: 'refresh',
      payload: {},
      priority: 5,
    })
    notify.success('Refresh command sent')
    await loadCommands()
  } catch (error) {
    notify.error(getErrorMessage(error, 'Failed to send refresh command'))
  } finally {
    actionLoading.value = false
  }
}

const handleReboot = async () => {
  actionLoading.value = true
  try {
    await commandsStore.createCommand({
      screen_id: screen.value.id,
      type: 'restart',
      payload: {},
      priority: 8,
    })
    notify.success('Reboot command sent')
    await loadCommands()
  } catch (error) {
    notify.error(getErrorMessage(error, 'Failed to send reboot command'))
  } finally {
    actionLoading.value = false
  }
}

const handleIdentify = async () => {
  actionLoading.value = true
  try {
    await commandsStore.createCommand({
      screen_id: screen.value.id,
      type: 'display_message',
      payload: {
        message: 'This screen is being identified',
        duration: 15,
      },
      priority: 7,
    })
    notify.success('Identify command sent')
    await loadCommands()
  } catch (error) {
    notify.error(getErrorMessage(error, 'Failed to send identify command'))
  } finally {
    actionLoading.value = false
  }
}

const handleTakeScreenshot = async () => {
  screenshotLoading.value = true
  try {
    await nextTick()
    if (document.fonts?.ready) {
      await document.fonts.ready
    }

    const captureElement = virtualMonitorRef.value?.getCaptureElement?.()
    if (!captureElement) {
      throw new Error('Preview surface not available for capture')
    }

    const html2canvas = window.html2canvas
    if (typeof html2canvas !== 'function') {
      throw new Error('Screenshot library is not loaded yet')
    }

    const canvas = await html2canvas(captureElement, {
      backgroundColor: '#000000',
      useCORS: true,
      allowTaint: false,
      scale: Math.max(2, window.devicePixelRatio || 1),
      logging: false,
    })

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob((outputBlob) => {
        if (!outputBlob) {
          reject(new Error('Failed to generate image blob'))
          return
        }
        resolve(outputBlob)
      }, 'image/png', 1)
    })

    const safeName = (screen.value?.name || `screen-${screen.value?.id || 'preview'}`)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'screen-preview'
    const fileName = `${safeName}-${new Date().toISOString().replace(/[:.]/g, '-')}.png`

    const downloadUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    link.rel = 'noopener'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(downloadUrl)

    notify.success('Screenshot captured and downloaded')
  } catch (error) {
    notify.error(getErrorMessage(error, 'Failed to capture screenshot'))
  } finally {
    screenshotLoading.value = false
  }
}

const handleRevokeToken = async () => {
  if (!screen.value?.id) return
  if (!confirm('Revoke the device token? The TV will be forced back to pairing mode.')) return
  revokingToken.value = true
  try {
    await screensAPI.revokeToken(screen.value.id)
    notify.success('Device token revoked. The TV will return to pairing mode.')
    await loadScreenData()
  } catch (error) {
    notify.error(getErrorMessage(error, 'Failed to revoke token'))
  } finally {
    revokingToken.value = false
  }
}

const handleDeleteScreen = async () => {
  try {
    await confirmDelete(
      screen.value.id,
      async (id) => {
        await screensStore.deleteScreen(id)
        notify.success('Screen deleted successfully')
        router.push({ name: 'screens' })
      },
      {
        title: 'Unpair Screen?',
        message: 'Are you sure you want to unpair this screen? This action is permanent and cannot be undone.',
        itemName: screen.value.name || screen.value.device_id,
        confirmText: 'Yes, Unpair',
        cancelText: 'Cancel',
      }
    )
  } catch (error) {
    if (error.message !== 'Delete cancelled') {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to delete screen'
      notify.error(errorMsg)
    }
  }
}

const loadCommands = async () => {
  if (!screen.value?.id) return
  
  try {
    const response = await commandsStore.fetchCommands({ screen: screen.value.id })
    const commands = response.results || response.data?.results || response.data || response || []
    
    const newPending = commands.filter(c => c.status === 'pending' || c.status === 'executing')
    const newHistory = commands.filter(c => c.status !== 'pending' && c.status !== 'executing').slice(0, 10)
    
    pendingCommands.value = smartUpdateArray(pendingCommands.value || [], newPending, 'id')
    commandHistory.value = smartUpdateArray(commandHistory.value || [], newHistory, 'id')
  } catch (error) {
    console.error('Failed to load commands:', error)
  }
}

const loadLogs = async () => {
  if (!screen.value?.id) return
  
  try {
    const response = await logsStore.fetchScreenStatusLogs({ screen_id: screen.value.id, page_size: 10 })
    const newLogs = response.results || response.data?.results || response.data || response || []
    
    recentLogs.value = smartUpdateArray(recentLogs.value || [], newLogs, 'id')
    
    // Update health metrics from most recent log
    if (recentLogs.value.length > 0) {
      const latestLog = recentLogs.value[0]
      healthMetrics.value = {
        cpu_usage: latestLog.cpu_usage || 0,
        memory_usage: latestLog.memory_usage || 0,
        latency: latestLog.heartbeat_latency || 0,
      }
    }
  } catch (error) {
    console.error('Failed to load logs:', error)
  }
}

const loadScreenData = async () => {
  const screenId = getScreenId()
  if (!screenId) {
    notify.error('Screen ID not found in route')
    return
  }
  
  try {
    await screensStore.fetchScreen(screenId)
    await templatesStore.fetchTemplates()
    if (screensStore.currentScreen?.active_template?.id) {
      await templatesStore.fetchTemplate(screensStore.currentScreen.active_template.id)
    }
    await loadCommands()
    await loadLogs()
  } catch (error) {
    console.error('Failed to load screen data:', error)
  }
}

// Real-time polling every 20 seconds
const startPolling = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  
  refreshInterval = setInterval(async () => {
    const screenId = getScreenId()
    if (screenId && screen.value?.id) {
      try {
        await screensStore.fetchScreen(screenId)
        await loadCommands()
        await loadLogs()
      } catch (error) {
        console.error('Failed to refresh screen data:', error)
      }
    }
  }, 20000) // 20 seconds
}

// Watch for route changes
watch(() => route.params.id, async (newId) => {
  if (newId) {
    await loadScreenData()
    startPolling()
  }
}, { immediate: false })

watch(activeTemplateId, async (newTemplateId, oldTemplateId) => {
  if (!newTemplateId || newTemplateId === oldTemplateId) return
  try {
    await templatesStore.fetchTemplate(newTemplateId)
  } catch (error) {
    console.error('Failed to fetch active template preview:', error)
  }
})

onMounted(async () => {
  await loadScreenData()
  startPolling()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.danger-zone-details[open] summary svg {
  transform: rotate(180deg);
}
</style>
