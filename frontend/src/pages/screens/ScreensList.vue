<template>
  <AppLayout>
    <div class="space-y-6">
      <!-- Stats Header -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Total Screens</p>
              <p class="text-2xl font-bold text-primary">{{ stats.total }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-card flex items-center justify-center">
              <TvIcon class="w-6 h-6 text-accent-color" style="color: var(--accent-color);" />
            </div>
          </div>
        </div>
        
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Online</p>
              <p class="text-2xl font-bold" style="color: var(--forest-green);">{{ stats.online }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-card flex items-center justify-center">
              <div class="w-3 h-3 rounded-full bg-forest-green animate-pulse"></div>
            </div>
          </div>
        </div>
        
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Offline</p>
              <p class="text-2xl font-bold text-dusty-red">{{ stats.offline }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-card flex items-center justify-center">
              <div class="w-3 h-3 rounded-full bg-dusty-red"></div>
            </div>
          </div>
        </div>
        
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Syncing</p>
              <p class="text-2xl font-bold" style="color: #D97706;">{{ stats.syncing }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-card flex items-center justify-center">
              <ArrowPathIcon class="w-6 h-6 animate-spin" style="color: #D97706;" />
            </div>
          </div>
        </div>
      </div>

      <!-- Header with View Toggle -->
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-primary">Screens</h1>
        <div class="flex items-center space-x-3">
          <!-- View Toggle -->
          <div class="flex items-center bg-card border border-border-color rounded-lg p-1">
            <button
              @click="viewMode = 'grid'"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-all duration-400',
                viewMode === 'grid'
                  ? 'bg-accent-color text-white'
                  : 'text-muted hover:text-primary'
              ]"
              style="--accent-color: var(--accent-color);"
            >
              <Squares2X2Icon class="w-5 h-5" />
            </button>
            <button
              @click="viewMode = 'table'"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-all duration-400',
                viewMode === 'table'
                  ? 'bg-accent-color text-white'
                  : 'text-muted hover:text-primary'
              ]"
              style="--accent-color: var(--accent-color);"
            >
              <TableCellsIcon class="w-5 h-5" />
            </button>
          </div>
          
          <button
            @click="$router.push('/screens/add')"
            class="btn-primary px-4 py-2 rounded-lg font-medium flex items-center gap-2"
          >
            <PlusIcon class="w-5 h-5" />
            Pair New Screen
          </button>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="card-base rounded-xl p-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="md:col-span-2">
            <label class="block text-sm text-muted mb-2">Search</label>
            <div class="relative">
              <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted" />
              <input
                v-model="screensStore.filters.search"
                type="text"
                placeholder="Search by name, IP, or pairing code..."
                class="input-base w-full pl-10 pr-4 py-2"
                @input="handleSearch"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm text-muted mb-2">Status</label>
            <select
              v-model="screensStore.filters.status"
              class="select-base w-full px-4 py-2"
              @change="handleFilter"
            >
              <option :value="null">All Status</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
            </select>
          </div>
          
          <div class="flex items-end">
            <button
              @click="clearFilters"
              class="btn-outline w-full px-4 py-2 rounded-lg font-medium"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div v-if="screensStore.loading && screensStore.screens.length === 0" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2" style="border-color: var(--accent-color);"></div>
        <p class="mt-4 text-muted">Loading screens...</p>
      </div>
      
      <div v-else-if="screensStore.error && screensStore.screens.length === 0" class="text-center py-12">
        <p class="text-dusty-red">{{ screensStore.error }}</p>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="filteredScreens.length === 0" class="text-center py-16">
        <div class="max-w-md mx-auto">
          <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-card border border-border-color flex items-center justify-center">
            <TvIcon class="w-12 h-12 text-muted" />
          </div>
          <h3 class="text-xl font-semibold text-primary mb-2">No Screens Found</h3>
          <p class="text-muted mb-6">
            {{ screensStore.filters.search || screensStore.filters.status 
              ? 'Try adjusting your filters to see more results.' 
              : 'Get started by pairing your first screen.' }}
          </p>
          <button
            v-if="!screensStore.filters.search && !screensStore.filters.status"
            @click="$router.push('/screens/add')"
            class="btn-primary px-6 py-3 rounded-lg font-medium inline-flex items-center gap-2"
          >
            <PlusIcon class="w-5 h-5" />
            Pair New Screen
          </button>
        </div>
      </div>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        <ScreenCard
          v-for="screen in paginatedScreens"
          :key="screen.id"
          :screen="screen"
          @identify="handleIdentify"
          @edit="handleEdit"
        />
      </div>

      <!-- Table View -->
      <div v-else class="card-base rounded-xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-card border-b border-border-color">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider w-40">Preview</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Name</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Pairing Code</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">IP Address</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Last Seen</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Template</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border-color">
              <tr
                v-for="(screen, index) in paginatedScreens"
                :key="screen.id"
                :class="[
                  'transition-colors duration-400',
                  index % 2 === 0 ? 'bg-card' : 'bg-zebra-stripe',
                  'hover:bg-card'
                ]"
              >
                <td class="px-4 py-3 align-middle w-40">
                  <div class="w-36 max-w-full aspect-video rounded-md overflow-hidden border border-border-color bg-black">
                    <ScreenTemplatePreview :screen="screen" />
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <StatusIndicator :status="getScreenStatus(screen)" />
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-primary">{{ screen.name || 'Unnamed' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-muted font-mono">{{ screen.pairing_code || 'N/A' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-muted">{{ screen.current_ip || 'N/A' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-muted">{{ formatLastSeen(screen.last_heartbeat_at) }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-muted">
                    {{ screen.active_template?.name || 'None' }}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="handleIdentify(screen)"
                      class="action-btn-view p-2 rounded-lg transition-all duration-400"
                      title="Identify"
                    >
                      <FingerPrintIcon class="w-4 h-4" />
                    </button>
                    <button
                      @click="handleEdit(screen)"
                      class="action-btn-edit p-2 rounded-lg transition-all duration-400"
                      title="Manage"
                    >
                      <PencilIcon class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination / Load More -->
      <div v-if="filteredScreens.length > itemsPerPage" class="flex justify-center">
        <button
          v-if="!showAll"
          @click="showAll = true"
          class="btn-outline px-6 py-3 rounded-lg font-medium"
        >
          Load More ({{ filteredScreens.length - itemsPerPage }} remaining)
        </button>
        <button
          v-else
          @click="showAll = false"
          class="btn-outline px-6 py-3 rounded-lg font-medium"
        >
          Show Less
        </button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScreensStore } from '@/stores/screens'
import { useCommandsStore } from '@/stores/commands'
import { useNotification } from '@/composables/useNotification'
import {
  TvIcon,
  PlusIcon,
  Squares2X2Icon,
  TableCellsIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  FingerPrintIcon,
  PencilIcon,
} from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'
import ScreenCard from '@/components/screens/ScreenCard.vue'
import ScreenTemplatePreview from '@/components/screens/ScreenTemplatePreview.vue'
import StatusIndicator from '@/components/screens/StatusIndicator.vue'
import { templatesAPI } from '@/services/api'
import { useTemplatesStore } from '@/stores/templates'

const router = useRouter()
const screensStore = useScreensStore()
const templatesStore = useTemplatesStore()
const commandsStore = useCommandsStore()
const notify = useNotification()

const viewMode = ref('grid')
const showAll = ref(false)
const itemsPerPage = 20
let statusPollInterval = null

// Computed stats
const stats = computed(() => {
  const screens = screensStore.screens
  const total = screens.length
  const online = screens.filter(s => screensStore.getScreenStatus(s) === 'online').length
  const offline = screens.filter(s => screensStore.getScreenStatus(s) === 'offline').length
  const syncing = screens.filter(s => {
    // Screens that are online but might be syncing content
    const status = screensStore.getScreenStatus(s)
    return status === 'online' && s.download_status === 'pending'
  }).length
  
  return { total, online, offline, syncing }
})

// Filtered screens
const filteredScreens = computed(() => screensStore.filteredScreens)

// Paginated screens
const paginatedScreens = computed(() => {
  if (showAll.value) {
    return filteredScreens.value
  }
  return filteredScreens.value.slice(0, itemsPerPage)
})

// Get screen status
const getScreenStatus = (screen) => {
  return screensStore.getScreenStatus(screen)
}

// Format last seen
const formatLastSeen = (timestamp) => {
  if (!timestamp) return 'Never'
  const now = new Date()
  const lastSeen = new Date(timestamp)
  const diffMs = now - lastSeen
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return lastSeen.toLocaleDateString()
}

// Handlers
const handleSearch = () => {
  // Filtering is handled by getter
}

const handleFilter = () => {
  // Filtering is handled by getter
}

const clearFilters = () => {
  screensStore.clearFilters()
  screensStore.fetchScreens()
}

/** Load full templates (with layers) for list previews; screen list API only returns template id/name. */
async function prefetchActiveTemplates() {
  const ids = [
    ...new Set(screensStore.screens.map((s) => s.active_template?.id).filter(Boolean)),
  ]
  await Promise.all(
    ids.map(async (id) => {
      const cached = templatesStore.templates.find((t) => t.id === id)
      if (cached?.layers?.length) return
      try {
        const { data } = await templatesAPI.detail(id)
        const idx = templatesStore.templates.findIndex((t) => t.id === id)
        if (idx !== -1) {
          templatesStore.templates[idx] = data
        } else {
          templatesStore.templates.push(data)
        }
      } catch {
        /* ignore */
      }
    })
  )
}

const handleIdentify = async (screen) => {
  try {
    await commandsStore.createCommand({
      screen_id: screen.id,
      type: 'display_message',
      payload: {
        message: `Screen: ${screen.name || screen.id}`,
        duration: 15,
      },
      priority: 5,
    })
    notify.success(`Identify command sent to ${screen.name || 'screen'}`)
  } catch (error) {
    notify.error(error.response?.data?.detail || 'Failed to send identify command')
  }
}

const handleEdit = (screen) => {
  router.push(`/screens/${screen.id}`)
}

// Status polling
const startStatusPolling = () => {
  // Poll every 30 seconds
  statusPollInterval = setInterval(async () => {
    try {
      await screensStore.fetchScreens()
      await prefetchActiveTemplates()
    } catch (error) {
      console.error('Error polling screen status:', error)
    }
  }, 30000)
}

const stopStatusPolling = () => {
  if (statusPollInterval) {
    clearInterval(statusPollInterval)
    statusPollInterval = null
  }
}

onMounted(async () => {
  await screensStore.fetchScreens()
  await prefetchActiveTemplates()
  startStatusPolling()
})

onUnmounted(() => {
  stopStatusPolling()
})
</script>
