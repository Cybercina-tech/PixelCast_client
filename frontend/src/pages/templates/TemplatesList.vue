<template>
  <AppLayout>
    <div class="space-y-6">
      <!-- Stats Header -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Total Templates</p>
              <p class="text-2xl font-bold text-primary">{{ stats.total }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-surface-inset border border-border-color flex items-center justify-center">
              <DocumentTextIcon class="w-6 h-6 text-muted" />
            </div>
          </div>
        </div>
        
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Active</p>
              <p class="text-2xl font-bold text-emerald-400">{{ stats.active }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
              <div class="w-3 h-3 rounded-full bg-emerald-400"></div>
            </div>
          </div>
        </div>
        
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Inactive</p>
              <p class="text-2xl font-bold text-muted">{{ stats.inactive }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-surface-inset border border-border-color flex items-center justify-center">
              <div class="w-3 h-3 rounded-full bg-slate-400"></div>
            </div>
          </div>
        </div>
        
        <div class="card-base rounded-xl p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted mb-1">Most Used</p>
              <p class="text-2xl font-bold text-blue-400">{{ stats.mostUsed }}</p>
            </div>
            <div class="w-12 h-12 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
              <ChartBarIcon class="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>
      </div>

      <!-- Header -->
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-primary">Templates</h1>
        <button
          v-if="canCreateTemplates"
          @click="showCreateModal = true"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
        >
          <PlusIcon class="w-5 h-5" />
          Create New Template
        </button>
      </div>

      <!-- Search & Filters -->
      <div class="card-base rounded-xl p-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="md:col-span-2">
            <label class="block text-sm text-muted mb-2">Search</label>
            <div class="relative">
              <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted" />
              <input
                v-model="templatesStore.filters.search"
                type="text"
                placeholder="Search by name or description..."
                class="input-base w-full pl-10 pr-4 py-2 rounded-lg"
                @input="handleSearch"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm text-muted mb-2">Status</label>
            <select
              v-model="templatesStore.filters.is_active"
              class="select-base w-full px-4 py-2 rounded-lg"
              @change="handleFilter"
            >
              <option :value="null">All Status</option>
              <option :value="true">Active</option>
              <option :value="false">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div v-if="templatesStore.loading && templatesStore.templates.length === 0" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p class="mt-4 text-muted">Loading templates...</p>
      </div>
      
      <div v-else-if="templatesStore.error && templatesStore.templates.length === 0" class="text-center py-12">
        <p class="text-error">{{ templatesStore.error }}</p>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="templatesStore.filteredTemplates.length === 0" class="text-center py-16">
        <div class="max-w-md mx-auto">
          <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-surface-inset border border-border-color flex items-center justify-center">
            <DocumentTextIcon class="w-12 h-12 text-muted" />
          </div>
          <h3 class="text-xl font-semibold text-primary mb-2">No Templates Found</h3>
          <p class="text-muted mb-6">
            {{ templatesStore.filters.search || templatesStore.filters.is_active !== null
              ? 'Try adjusting your filters to see more results.' 
              : 'Get started by creating your first template.' }}
          </p>
          <button
            v-if="canCreateTemplates && !templatesStore.filters.search && templatesStore.filters.is_active === null"
            @click="showCreateModal = true"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all inline-flex items-center gap-2"
          >
            <PlusIcon class="w-5 h-5" />
            Create New Template
          </button>
        </div>
      </div>

      <!-- Templates Grid -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        <TemplateCard
          v-for="template in templatesStore.filteredTemplates"
          :key="template.id"
          :template="template"
          :can-duplicate="canDuplicateTemplate"
          :can-push="canPushTemplate"
          :can-delete="canDeleteTemplate"
          @edit="handleEdit"
          @duplicate="handleDuplicate"
          @push="handlePush"
          @delete="handleDelete"
        />
      </div>

      <!-- Create/Edit Template Modal -->
      <Modal
        :show="showCreateModal || showEditModal"
        :title="showEditModal ? 'Edit Template' : 'Create Template'"
        @close="closeModal"
      >
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">Name <span class="text-red-500">*</span></label>
            <input v-model="form.name" type="text" required class="input-base w-full px-3 py-2 rounded-lg" placeholder="Template name" />
          </div>
          <div v-if="!showEditModal">
            <label class="label-base block text-sm mb-1">Target Screen <span class="text-gray-500 text-xs">(Optional)</span></label>
            <select 
              v-model="form.target_screen" 
              class="select-base w-full px-3 py-2 rounded-lg"
              @change="handleScreenSelection"
            >
              <option :value="null">None (Custom Resolution)</option>
              <option 
                v-for="screen in screens" 
                :key="screen.id" 
                :value="screen.id"
              >
                {{ screen.name }} ({{ screen.screen_width }}x{{ screen.screen_height }})
              </option>
            </select>
            <p class="text-xs text-muted mt-1">
              Select a screen to automatically set the resolution, or leave empty to specify custom dimensions.
            </p>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Description</label>
            <textarea v-model="form.description" rows="3" class="textarea-base w-full px-3 py-2 rounded-lg" placeholder="Template description"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-base block text-sm mb-1">Width <span class="text-red-500">*</span></label>
              <input 
                v-model.number="form.width" 
                type="number" 
                required 
                :disabled="!!form.target_screen && !showEditModal"
                class="input-base w-full px-3 py-2 rounded-lg"
                :class="{ 'opacity-50 cursor-not-allowed': !!form.target_screen && !showEditModal }"
              />
            </div>
            <div>
              <label class="label-base block text-sm mb-1">Height <span class="text-red-500">*</span></label>
              <input 
                v-model.number="form.height" 
                type="number" 
                required 
                :disabled="!!form.target_screen && !showEditModal"
                class="input-base w-full px-3 py-2 rounded-lg"
                :class="{ 'opacity-50 cursor-not-allowed': !!form.target_screen && !showEditModal }"
              />
            </div>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Orientation</label>
            <select v-model="form.orientation" class="select-base w-full px-3 py-2 rounded-lg">
              <option value="landscape">Landscape</option>
              <option value="portrait">Portrait</option>
              <option value="reverse">Reverse</option>
            </select>
          </div>
          <div v-if="showEditModal">
            <label class="flex items-center text-primary">
              <input
                v-model="form.is_active"
                type="checkbox"
                class="checkbox-base mr-2"
              />
              <span class="text-sm font-medium">Active</span>
            </label>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleSubmit" class="btn-primary px-4 py-2 rounded-lg">
            {{ showEditModal ? 'Update' : 'Create & Edit' }}
          </button>
          <button type="button" @click="closeModal" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>

      <!-- Push to Screen Modal -->
      <PushToScreenModal
        :show="showPushModal"
        :template="selectedTemplate"
        :online-screens="onlineScreens"
        :loading="pushLoading"
        @close="showPushModal = false"
        @select="handlePushToScreen"
      />
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { hasPermission } from '@/utils/permissions'
import { useTemplatesStore } from '@/stores/templates'
import { useScreensStore } from '@/stores/screens'
import { useNotification } from '@/composables/useNotification'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import { normalizeApiError } from '@/utils/apiError'
import { templatesAPI } from '@/services/api'
import {
  DocumentTextIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
} from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'
import Modal from '@/components/common/Modal.vue'
import TemplateCard from '@/components/templates/TemplateCard.vue'
import PushToScreenModal from '@/components/templates/PushToScreenModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const templatesStore = useTemplatesStore()
const screensStore = useScreensStore()
const notify = useNotification()

const canCreateTemplates = computed(() => hasPermission(authStore.user, 'create_templates'))
const canDuplicateTemplate = computed(() => hasPermission(authStore.user, 'create_templates'))
const canPushTemplate = computed(() => hasPermission(authStore.user, 'edit_templates'))
const canDeleteTemplate = computed(() => hasPermission(authStore.user, 'delete_templates'))

const showCreateModal = ref(false)
const screens = computed(() => screensStore.screens)
const showEditModal = ref(false)
const editingTemplate = ref(null)
const showPushModal = ref(false)
const selectedTemplate = ref(null)
const pushLoading = ref(false)

// Get online screens only
const onlineScreens = computed(() => {
  return screensStore.onlineScreens || screens.value.filter(s => screensStore.getScreenStatus(s) === 'online')
})

const form = ref({
  name: '',
  description: '',
  target_screen: null,
  width: 1920,
  height: 1080,
  orientation: 'landscape',
  is_active: true,
  config_json: {},
})

// Computed stats
const stats = computed(() => {
  const templates = templatesStore.templates
  const total = templates.length
  const active = templates.filter(t => t.is_active).length
  const inactive = templates.filter(t => !t.is_active).length
  const mostUsed = Math.max(...templates.map(t => t.screens_count || 0), 0)
  
  return { total, active, inactive, mostUsed }
})

const handleSearch = () => {
  // Filtering is handled by getter
}

const handleFilter = () => {
  // Filtering is handled by getter
}

const handleEdit = (template) => {
  router.push(`/templates/${template.id}/edit`)
}

const handleDuplicate = async (template) => {
  try {
    const newTemplate = await templatesStore.duplicateTemplate(template.id)
    notify.success(`Template "Copy of ${template.name}" created successfully`)
    // Refresh templates list
    await templatesStore.fetchTemplates()
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to duplicate template')
  }
}

const handlePush = async (template) => {
  // Fetch screens to ensure we have the latest online status
  try {
    await screensStore.fetchScreens()
    selectedTemplate.value = template
    showPushModal.value = true
  } catch (error) {
    notify.error('Failed to load screens')
  }
}

const handlePushToScreen = async (screen) => {
  if (!selectedTemplate.value) return
  
  pushLoading.value = true
  try {
    // Step 1: Activate template on the screen
    await templatesStore.activateOnScreen(
      selectedTemplate.value.id,
      screen.id,
      true // sync_content
    )
    
    // Step 2: Send RELOAD command to the screen
    const { useCommandsStore } = await import('@/stores/commands')
    const commandsStore = useCommandsStore()
    
    await commandsStore.createCommand({
      screen_id: screen.id,
      type: 'refresh', // This is the RELOAD command
      payload: {},
      priority: 8, // High priority
    })
    
    notify.success(`Template successfully pushed to ${screen.name || screen.device_id}`)
    showPushModal.value = false
    selectedTemplate.value = null
    
    // Refresh templates to update screen counts
    await templatesStore.fetchTemplates()
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to push template to screen')
  } finally {
    pushLoading.value = false
  }
}

const handleDelete = async (template) => {
  try {
    const { confirmDelete } = useDeleteConfirmation()
    await confirmDelete(
      template.id,
      async () => {
        await templatesStore.deleteTemplate(template.id)
      },
      {
        title: 'Delete Template?',
        message: 'This will permanently delete the template and all its layers, widgets, and content. This action cannot be undone.',
        itemName: template.name,
        confirmText: 'Yes, Delete Template',
        cancelText: 'Cancel'
      }
    )
    notify.success('Template deleted successfully')
  } catch (error) {
    if (error.message !== 'Delete cancelled') {
      const parsed = error.apiError || normalizeApiError(error)
      notify.error(parsed.userMessage || 'Failed to delete template')
    }
  }
}

const handleScreenSelection = () => {
  if (form.value.target_screen && !showEditModal.value) {
    const selectedScreen = screens.value.find(s => s.id === form.value.target_screen)
    if (selectedScreen && selectedScreen.screen_width && selectedScreen.screen_height) {
      form.value.width = selectedScreen.screen_width
      form.value.height = selectedScreen.screen_height
    }
  }
}

const handleSubmit = async () => {
  if (showEditModal.value) {
    // Edit mode: Save to database
    try {
      await templatesStore.updateTemplate(editingTemplate.value.id, form.value)
      notify.success('Template updated')
      closeModal()
    } catch (error) {
      const parsed = error.apiError || normalizeApiError(error)
      notify.error(parsed.userMessage || 'Operation failed')
    }
  } else {
    // Create mode: Navigate to editor with query params
    if (!form.value.name || form.value.name.trim() === '') {
      notify.error('Please enter a template name')
      return
    }
    
    // Build query params
    const queryParams = {
      name: form.value.name,
      width: form.value.width,
      height: form.value.height,
    }
    
    if (form.value.description) {
      queryParams.description = form.value.description
    }
    
    if (form.value.target_screen) {
      queryParams.screen_id = form.value.target_screen
    }
    
    if (form.value.orientation) {
      queryParams.orientation = form.value.orientation
    }
    
    // Navigate to template editor
    router.push({
      path: '/templates/new/edit',
      query: queryParams
    })
    
    closeModal()
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingTemplate.value = null
  form.value = {
    name: '',
    description: '',
    target_screen: null,
    width: 1920,
    height: 1080,
    orientation: 'landscape',
    is_active: true,
    config_json: {},
  }
}

// Watch for modal opening to fetch screens
watch(showCreateModal, async (isOpen) => {
  if (isOpen && !showEditModal.value) {
    // Fetch screens when create modal opens
    try {
      await screensStore.fetchScreens()
    } catch (error) {
      console.error('Failed to fetch screens:', error)
    }
  }
})

// Watch for push modal opening to fetch screens
watch(showPushModal, async (isOpen) => {
  if (isOpen) {
    // Fetch screens when push modal opens to get latest online status
    try {
      await screensStore.fetchScreens()
    } catch (error) {
      console.error('Failed to fetch screens:', error)
    }
  }
})

const PREFETCH_TEMPLATE_CONCURRENCY = 8

/** List API omits layers; prefetch full templates with bounded concurrency to avoid rate-limit bursts. */
async function prefetchTemplateLayersForList() {
  const ids = templatesStore.templates.map((t) => t.id).filter(Boolean)
  const pending = [...ids]

  async function worker() {
    while (pending.length) {
      const id = pending.shift()
      if (!id) continue
      const existing = templatesStore.templates.find((t) => t.id === id)
      if (existing?.layers?.length) continue
      try {
        const { data } = await templatesAPI.detail(id)
        const idx = templatesStore.templates.findIndex((t) => t.id === id)
        if (idx !== -1) {
          templatesStore.templates[idx] = data
        }
      } catch {
        /* ignore */
      }
    }
  }

  const n = Math.min(PREFETCH_TEMPLATE_CONCURRENCY, Math.max(1, ids.length))
  await Promise.all(Array.from({ length: n }, () => worker()))
}

onMounted(async () => {
  await templatesStore.fetchTemplates()
  await prefetchTemplateLayersForList()
})
</script>
