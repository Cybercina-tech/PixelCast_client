<template>
  <AppLayout>
    <div v-if="templatesStore.loading" class="text-center py-8">Loading...</div>
    <div v-else-if="templatesStore.error" class="text-center py-8 text-error">
      {{ templatesStore.error }}
    </div>
    <div v-else-if="template" class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-primary">{{ template.name }}</h1>
          <p class="text-secondary">{{ template.description || 'No description' }}</p>
        </div>
        <button
          @click="showActivateModal = true"
          class="btn-primary px-4 py-2 rounded-lg"
        >
          Activate on Screen
        </button>
      </div>
      
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Template Information" class="lg:col-span-2">
          <dl class="space-y-3">
            <div>
              <dt class="text-sm font-medium text-muted">Dimensions</dt>
              <dd class="mt-1 text-sm text-primary">{{ template.width }}x{{ template.height }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Orientation</dt>
              <dd class="mt-1 text-sm text-primary capitalize">{{ template.orientation }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Version</dt>
              <dd class="mt-1 text-sm text-primary">{{ template.version }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Status</dt>
              <dd class="mt-1">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    template.is_active ? 'badge-success' : 'badge-info',
                  ]"
                >
                  {{ template.is_active ? 'Active' : 'Inactive' }}
                </span>
              </dd>
            </div>
          </dl>
        </Card>
        
        <Card title="Preview">
          <div class="aspect-video bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
            <span class="text-muted">Template Preview</span>
          </div>
        </Card>
      </div>
      
      <!-- Hierarchy: Template → Layer → Widget → Content -->
      <Card title="Template Hierarchy">
        <div class="space-y-4">
          <div v-for="layer in (layers || [])" :key="layer.id" class="border-l-4 border-primary-color pl-4">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-primary">{{ layer.name }}</h3>
              <div class="flex items-center gap-2">
                <span class="text-xs text-muted">Layer</span>
                <button
                  @click="openCreateWidgetModal(layer.id)"
                  class="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
                  title="Add Widget to this Layer"
                >
                  + Add Widget
                </button>
              </div>
            </div>
            <div v-for="widget in getWidgetsForLayer(layer.id)" :key="widget.id" class="ml-4 mt-2 border-l-4 border-blue-400 dark:border-blue-500 pl-4">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-sm font-medium text-primary">{{ widget.name }} ({{ widget.type }})</h4>
                <span class="text-xs text-muted">Widget</span>
              </div>
              <div v-for="content in getContentsForWidget(widget.id)" :key="content.id" class="ml-4 mt-1 text-xs text-secondary">
                • {{ content.name }} ({{ content.type }})
              </div>
            </div>
          </div>
          <div v-if="!layers || layers.length === 0" class="text-center text-muted py-4">
            No layers in this template. Please create a layer first.
          </div>
        </div>
      </Card>
      
      <!-- Create Widget Modal -->
      <Modal :show="showCreateWidgetModal" title="Create Widget" @close="closeCreateWidgetModal">
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">Layer <span class="text-red-500">*</span></label>
            <select v-model="widgetForm.layer" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="">Select a layer</option>
              <option v-for="layer in layers" :key="layer.id" :value="layer.id">
                {{ layer.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Name <span class="text-red-500">*</span></label>
            <input v-model="widgetForm.name" type="text" required class="input-base w-full px-3 py-2 rounded-lg" placeholder="Widget name" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Type <span class="text-red-500">*</span></label>
            <select v-model="widgetForm.type" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="">Select widget type</option>
              <option value="text">Text</option>
              <option value="image">Image</option>
              <option value="video">Video</option>
              <option value="clock">Clock</option>
              <option value="webview">Web View</option>
              <option value="chart">Chart</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-base block text-sm mb-1">X Position</label>
              <input v-model.number="widgetForm.x" type="number" min="0" class="input-base w-full px-3 py-2 rounded-lg" />
            </div>
            <div>
              <label class="label-base block text-sm mb-1">Y Position</label>
              <input v-model.number="widgetForm.y" type="number" min="0" class="input-base w-full px-3 py-2 rounded-lg" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-base block text-sm mb-1">Width</label>
              <input v-model.number="widgetForm.width" type="number" min="1" class="input-base w-full px-3 py-2 rounded-lg" />
            </div>
            <div>
              <label class="label-base block text-sm mb-1">Height</label>
              <input v-model.number="widgetForm.height" type="number" min="1" class="input-base w-full px-3 py-2 rounded-lg" />
            </div>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Z-Index</label>
            <input v-model.number="widgetForm.z_index" type="number" min="0" class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div>
            <label class="flex items-center">
              <input v-model="widgetForm.is_active" type="checkbox" class="checkbox-base mr-2" />
              <span class="text-sm text-primary">Active</span>
            </label>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleCreateWidget" class="btn-primary px-4 py-2 rounded-lg">
            Create Widget
          </button>
          <button type="button" @click="closeCreateWidgetModal" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
      
      <Modal :show="showActivateModal" title="Activate Template on Screen" @close="showActivateModal = false">
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">Select Screen</label>
            <select v-model="activateForm.screen_id" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="">Select a screen</option>
              <option v-for="screen in screens" :key="screen.id" :value="screen.id">
                {{ screen.name }} ({{ screen.device_id }})
              </option>
            </select>
          </div>
          <div>
            <label class="flex items-center">
              <input v-model="activateForm.sync_content" type="checkbox" class="checkbox-base mr-2" />
              <span class="text-sm text-primary dark:text-slate-300">Sync content automatically</span>
            </label>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleActivate" class="btn-primary px-4 py-2 rounded-lg">
            Activate
          </button>
          <button type="button" @click="showActivateModal = false" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTemplatesStore } from '@/stores/templates'
import { useScreensStore } from '@/stores/screens'
import { useContentStore } from '@/stores/content'
import { useNotification } from '@/composables/useNotification'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'

const route = useRoute()
const templatesStore = useTemplatesStore()
const screensStore = useScreensStore()
const contentStore = useContentStore()
const notify = useNotification()

const template = computed(() => templatesStore.currentTemplate)
const screens = computed(() => screensStore.screens)
const layers = computed(() => templatesStore.layers)
const widgets = computed(() => templatesStore.widgets)
const contents = computed(() => contentStore.contents)

const showActivateModal = ref(false)
const showCreateWidgetModal = ref(false)
const activateForm = ref({
  screen_id: '',
  sync_content: true,
})
const widgetForm = ref({
  layer: '',
  name: '',
  type: '',
  x: 0,
  y: 0,
  width: 100,
  height: 100,
  z_index: 0,
  is_active: true,
})

const getWidgetsForLayer = (layerId) => {
  return (widgets.value || []).filter(w => w.layer === layerId)
}

const getContentsForWidget = (widgetId) => {
  return (contents.value || []).filter(c => c.widget === widgetId)
}

const handleActivate = async () => {
  try {
    await templatesStore.activateOnScreen(
      template.value.id,
      activateForm.value.screen_id,
      activateForm.value.sync_content
    )
    notify.success('Template activated successfully')
    showActivateModal.value = false
  } catch (error) {
    notify.error('Failed to activate template')
  }
}

const openCreateWidgetModal = (layerId = null) => {
  widgetForm.value = {
    layer: layerId || '',
    name: '',
    type: '',
    x: 0,
    y: 0,
    width: 100,
    height: 100,
    z_index: 0,
    is_active: true,
  }
  showCreateWidgetModal.value = true
}

const closeCreateWidgetModal = () => {
  showCreateWidgetModal.value = false
  widgetForm.value = {
    layer: '',
    name: '',
    type: '',
    x: 0,
    y: 0,
    width: 100,
    height: 100,
    z_index: 0,
    is_active: true,
  }
}

const handleCreateWidget = async () => {
  if (!widgetForm.value.layer) {
    notify.error('Please select a layer')
    return
  }
  if (!widgetForm.value.name) {
    notify.error('Please enter a widget name')
    return
  }
  if (!widgetForm.value.type) {
    notify.error('Please select a widget type')
    return
  }
  
  try {
    await templatesStore.createWidget(widgetForm.value)
    notify.success('Widget created successfully')
    closeCreateWidgetModal()
    // Refresh widgets for the layer
    await templatesStore.fetchWidgets(widgetForm.value.layer)
    // Refresh contents list to show new widget
    await contentStore.fetchContents()
  } catch (error) {
    const errorMessage = error.response?.data?.detail || 
                         error.response?.data?.message || 
                         error.response?.data?.errors || 
                         'Failed to create widget'
    notify.error(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage))
    console.error('Create widget error:', error)
  }
}

onMounted(async () => {
  const templateId = route.params.id
  await templatesStore.fetchTemplate(templateId)
  await templatesStore.fetchLayers(templateId)
  await screensStore.fetchScreens()
  
  // Fetch widgets for each layer
  for (const layer of (layers.value || [])) {
    await templatesStore.fetchWidgets(layer.id)
  }
  
  // Fetch contents for all widgets
  for (const widget of (widgets.value || [])) {
    await contentStore.fetchContents({ widget: widget.id })
  }
})
</script>
