<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto" @click.self="$emit('close')">
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
          <div class="fixed inset-0 transition-opacity bg-black/40 dark:bg-black/60 backdrop-blur-md" aria-hidden="true"></div>
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
          <div
            class="inline-block align-bottom bg-card backdrop-blur-lg rounded-2xl text-left overflow-hidden shadow-2xl border border-border-color transform transition-all duration-400 sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full"
            style="animation: modalFadeUp 0.3s ease-out;"
          >
            <!-- Header -->
            <div class="bg-card px-6 pt-6 pb-4 border-b border-border-color">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-xl font-semibold text-primary">Media Library</h3>
                <button
                  @click="$emit('close')"
                  class="text-muted hover:text-primary transition-colors duration-400 p-2 rounded-lg hover:bg-card"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <!-- Tabs -->
              <div class="flex gap-2 border-b border-border-color">
                <button
                  @click="activeTab = 'gallery'"
                  :class="[
                    'px-4 py-2 text-sm font-medium transition-colors duration-400 border-b-2',
                    activeTab === 'gallery'
                      ? 'text-accent-color border-accent-color'
                      : 'text-muted border-transparent hover:text-primary'
                  ]"
                  style="--accent-color: var(--accent-color);"
                >
                  <span class="flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Gallery
                  </span>
                </button>
                <button
                  @click="activeTab = 'upload'"
                  :class="[
                    'px-4 py-2 text-sm font-medium transition-colors duration-400 border-b-2',
                    activeTab === 'upload'
                      ? 'text-accent-color border-accent-color'
                      : 'text-muted border-transparent hover:text-primary'
                  ]"
                  style="--accent-color: var(--accent-color);"
                >
                  <span class="flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload
                  </span>
                </button>
              </div>
            </div>

            <!-- Tab Content -->
            <div class="bg-card">
              <!-- Gallery Tab -->
              <div v-if="activeTab === 'gallery'" class="px-6 py-4">
                <!-- Search and Filter -->
                <div class="flex gap-3 mb-4">
                  <div class="flex-1">
                    <input
                      v-model="searchQuery"
                      type="text"
                      placeholder="Search media..."
                      class="input-base w-full px-4 py-2 text-sm"
                    />
                  </div>
                  <div class="flex gap-2">
                    <button
                      @click="filterType = null"
                      :class="[
                        'filter-button',
                        filterType === null ? 'filter-button-active' : 'filter-button-inactive'
                      ]"
                    >
                      All Types
                    </button>
                    <button
                      @click="filterType = 'image'"
                      :class="[
                        'filter-button',
                        filterType === 'image' ? 'filter-button-active' : 'filter-button-inactive'
                      ]"
                    >
                      Images
                    </button>
                    <button
                      @click="filterType = 'video'"
                      :class="[
                        'filter-button',
                        filterType === 'video' ? 'filter-button-active' : 'filter-button-inactive'
                      ]"
                    >
                      Videos
                    </button>
                  </div>
                </div>

                <!-- Loading State -->
                <div v-if="contentStore.loading" class="flex items-center justify-center py-12">
                  <div class="animate-spin rounded-full h-10 w-10 border-b-2" style="border-color: var(--accent-color);"></div>
                  <span class="ml-3 text-muted">Loading media...</span>
                </div>

                <!-- Error State -->
                <div v-else-if="contentStore.error" class="text-center py-12">
                  <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/30 mb-4">
                    <svg class="w-8 h-8 text-red-500 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p class="text-red-600 dark:text-red-400 font-medium mb-2">{{ contentStore.error }}</p>
                  <button
                    @click="loadContents"
                    class="btn-primary px-4 py-2 rounded-lg text-sm"
                  >
                    Retry
                  </button>
                </div>

                <!-- Empty State -->
                <div v-else-if="filteredContents.length === 0" class="text-center py-12">
                  <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-card mb-4">
                    <svg class="w-8 h-8 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-primary mb-2">No media found</h3>
                  <p class="text-muted text-sm mb-4">{{ searchQuery || filterType ? 'Try adjusting your search or filters' : 'Upload some content to get started' }}</p>
                  <button
                    @click="activeTab = 'upload'"
                    class="btn-primary px-4 py-2 rounded-lg text-sm"
                  >
                    Upload Media
                  </button>
                </div>

                <!-- Media Grid with Sidebar: items-start prevents the gallery column stretching to sidebar height -->
                <div v-else class="flex gap-6 items-start">
                  <!-- Media Grid -->
                  <div
                    class="flex-1 min-h-0 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 max-h-[60vh] overflow-y-auto content-start items-start auto-rows-auto"
                  >
                    <div
                      v-for="content in filteredContents"
                      :key="content.id"
                      @click="selectContent(content)"
                      :class="[
                        'relative group cursor-pointer rounded-lg overflow-hidden transition-all duration-400 media-thumbnail h-fit max-w-full self-start',
                        selectedContentId === content.id
                          ? 'media-thumbnail-selected'
                          : 'media-thumbnail-default'
                      ]"
                    >
                      <!-- Thumbnail/Preview -->
                      <div class="aspect-square bg-card relative overflow-hidden">
                        <!-- Smart Media Preview -->
                        <SmartMediaPreview
                          :file-url="content.secure_url || content.absolute_file_url || content.file_url"
                          :file-type="content.type"
                          :alt="content.name || 'Media'"
                          :video-duration="content.video_duration"
                          :enable-hover-zoom="true"
                          :play-on-hover="true"
                          :show-duration="true"
                          class="w-full h-full"
                        />

                        <!-- Selection Indicator - Navy Blue -->
                        <div
                          v-if="selectedContentId === content.id"
                          class="absolute inset-0 z-30 flex items-center justify-center pointer-events-none"
                          :style="{ background: 'rgba(9, 132, 227, 0.15)' }"
                        >
                          <div class="w-8 h-8 rounded-full flex items-center justify-center" style="background: var(--accent-color);">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        </div>

                        <!-- Type Badge -->
                        <div class="absolute top-2 right-2 z-10">
                          <span
                            :class="[
                              'px-2 py-1 rounded text-xs font-medium backdrop-blur-sm',
                              content.type === 'image' ? 'bg-green-500/80 text-white' : 'bg-purple-500/80 text-white'
                            ]"
                          >
                            {{ content.type === 'image' ? 'IMG' : 'VID' }}
                          </span>
                        </div>

                        <!-- Hover overlay: padded, wrap-safe (match ScreenCard / Contents list) -->
                        <div
                          class="absolute inset-0 z-20 flex flex-wrap items-center justify-center content-center gap-2 px-3 py-4 sm:px-4 bg-black/50 backdrop-blur-sm opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity duration-400 overflow-y-auto"
                        >
                          <button
                            type="button"
                            @click.stop="handleDeleteContent(content)"
                            class="px-4 sm:px-5 py-2 bg-red-600/90 hover:bg-red-600 text-white rounded-lg text-sm font-medium inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap transition-colors duration-200"
                            title="Delete"
                          >
                            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Delete
                          </button>
                        </div>

                        <!-- Frosted Glass File Name Overlay -->
                        <div class="absolute bottom-0 left-0 right-0 z-10 p-2 media-name-overlay pointer-events-none">
                          <p class="text-xs text-primary font-medium truncate" :title="content.name">
                            {{ content.name || 'Untitled' }}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- File Information Sidebar -->
                  <div
                    v-if="selectedContentId"
                    class="w-80 flex-shrink-0 media-sidebar"
                  >
                    <div class="card-base rounded-xl p-6 h-full">
                      <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-primary">File Details</h3>
                        <button
                          @click="selectedContentId = null"
                          class="text-muted hover:text-primary transition-colors duration-400 p-1 rounded"
                        >
                          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      
                      <div v-if="selectedContent" class="space-y-4">
                        <!-- Preview -->
                        <div class="aspect-video bg-card rounded-lg overflow-hidden mb-4">
                          <SmartMediaPreview
                            :file-url="selectedContent.secure_url || selectedContent.absolute_file_url || selectedContent.file_url"
                            :file-type="selectedContent.type"
                            :alt="selectedContent.name || 'Media'"
                            :video-duration="selectedContent.video_duration"
                            class="w-full h-full"
                          />
                        </div>

                        <!-- Metadata -->
                        <div class="space-y-3">
                          <div>
                            <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Name</dt>
                            <dd class="text-sm text-primary font-medium">{{ selectedContent.name || 'Untitled' }}</dd>
                          </div>
                          
                          <div v-if="selectedContent.description">
                            <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Description</dt>
                            <dd class="text-sm text-primary">{{ selectedContent.description }}</dd>
                          </div>

                          <div>
                            <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Type</dt>
                            <dd class="text-sm text-primary capitalize">{{ selectedContent.type || 'Unknown' }}</dd>
                          </div>

                          <div v-if="selectedContent.file_size">
                            <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Size</dt>
                            <dd class="text-sm text-primary">{{ formatFileSize(selectedContent.file_size) }}</dd>
                          </div>

                          <div v-if="selectedContent.width && selectedContent.height">
                            <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Resolution</dt>
                            <dd class="text-sm text-primary">{{ selectedContent.width }} × {{ selectedContent.height }}</dd>
                          </div>

                          <div v-if="selectedContent.created_at">
                            <dt class="text-xs font-medium text-muted uppercase tracking-wider mb-1">Date</dt>
                            <dd class="text-sm text-primary">{{ formatDate(selectedContent.created_at) }}</dd>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Upload Tab -->
              <div v-if="activeTab === 'upload'" class="px-6 py-4">
                <!-- Drag & Drop Zone -->
                <div
                  @drop.prevent="handleDrop"
                  @dragover.prevent="isDragging = true"
                  @dragleave.prevent="isDragging = false"
                  @dragenter.prevent="isDragging = true"
                  :class="[
                    'upload-zone rounded-lg p-8 text-center transition-all duration-400',
                    isDragging
                      ? 'upload-zone-active'
                      : 'upload-zone-default'
                  ]"
                >
                  <input
                    ref="fileInput"
                    type="file"
                    :accept="filterByType === 'image' ? 'image/*' : filterByType === 'video' ? 'video/*' : 'image/*,video/*'"
                    multiple
                    class="hidden"
                    @change="handleFileSelect"
                  />
                  
                  <div v-if="!uploadingFiles.length && !uploadedFiles.length">
                    <svg class="w-16 h-16 mx-auto text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p class="text-primary font-medium mb-2">Drag & drop files here</p>
                    <p class="text-muted text-sm mb-4">or</p>
                    <button
                      @click="fileInput?.click()"
                      class="btn-primary px-6 py-2 rounded-lg text-sm font-medium"
                    >
                      Browse Files
                    </button>
                    <p class="text-muted text-xs mt-3">
                      Supported: {{ filterByType === 'image' ? 'Images' : filterByType === 'video' ? 'Videos' : 'Images & Videos' }}
                    </p>
                  </div>

                  <!-- Upload Progress -->
                  <div v-if="uploadingFiles.length" class="space-y-3">
                    <div
                      v-for="file in uploadingFiles"
                      :key="file.id"
                      class="bg-card rounded-lg p-4"
                    >
                      <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-primary font-medium truncate flex-1">{{ file.name }}</span>
                        <span class="text-xs text-muted ml-2">{{ Math.round(file.progress) }}%</span>
                      </div>
                      <div class="w-full bg-card rounded-full h-2" style="background: rgba(0, 0, 0, 0.1);">
                        <div
                          class="h-2 rounded-full transition-all duration-300"
                          :style="{ width: `${file.progress}%`, background: 'var(--accent-color)' }"
                        ></div>
                      </div>
                    </div>
                  </div>

                  <!-- Uploaded Files -->
                  <div v-if="uploadedFiles.length" class="space-y-3 mt-4">
                    <div
                      v-for="file in uploadedFiles"
                      :key="file.id"
                      class="bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-center justify-between"
                    >
                      <div class="flex items-center gap-3 flex-1 min-w-0">
                        <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span class="text-sm text-white font-medium truncate">{{ file.name }}</span>
                      </div>
                      <button
                        @click="selectUploadedFile(file)"
                        class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition-colors duration-200 ml-2"
                      >
                        Use This
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Upload Form (if needed for additional metadata) -->
                <div v-if="selectedFiles.length > 0 && !uploadingFiles.length && !uploadedFiles.length" class="mt-4 space-y-3">
                  <div>
                    <label class="block text-xs font-medium text-muted mb-1.5">Content Name</label>
                    <input
                      v-model="uploadForm.name"
                      type="text"
                      placeholder="Enter a name for the content"
                      class="input-base w-full px-3 py-2 text-sm"
                    />
                  </div>
                  <button
                    @click="handleUpload"
                    :disabled="!uploadForm.name || uploadingFiles.length > 0"
                    class="btn-primary w-full px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Upload {{ selectedFiles.length }} {{ selectedFiles.length === 1 ? 'File' : 'Files' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="bg-card px-6 py-4 border-t border-border-color flex items-center justify-between">
              <div class="text-sm text-muted">
                <span v-if="activeTab === 'gallery'">
                  {{ filteredContents.length }} {{ filteredContents.length === 1 ? 'item' : 'items' }}
                  <span v-if="searchQuery || filterType" class="opacity-70">(filtered)</span>
                </span>
                <span v-else-if="activeTab === 'upload'">
                  {{ selectedFiles.length }} {{ selectedFiles.length === 1 ? 'file' : 'files' }} selected
                </span>
              </div>
              <div class="flex gap-3">
                <button
                  @click="$emit('close')"
                  class="btn-outline px-4 py-2 rounded-lg text-sm font-medium"
                >
                  {{ activeTab === 'upload' && uploadedFiles.length ? 'Done' : 'Cancel' }}
                </button>
                <button
                  v-if="activeTab === 'gallery' && selectedContentId"
                  @click="confirmSelection"
                  class="btn-primary px-4 py-2 rounded-lg text-sm font-medium"
                >
                  Select
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useContentStore } from '@/stores/content'
import { useNotification } from '@/composables/useNotification'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import SmartMediaPreview from './SmartMediaPreview.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  filterByType: {
    type: String,
    default: null, // 'image' or 'video' to filter by type
    validator: (value) => !value || ['image', 'video'].includes(value)
  },
  widgetId: {
    type: String,
    default: null // Widget ID to associate content with (optional - allows standalone uploads)
  }
})

const emit = defineEmits(['close', 'select'])

const contentStore = useContentStore()
const notify = useNotification()
const { confirmDelete } = useDeleteConfirmation()

// Tab state
const activeTab = ref('gallery')

// Gallery state
const searchQuery = ref('')
const filterType = ref(props.filterByType)
const selectedContentId = ref(null)

// Get selected content object
const selectedContent = computed(() => {
  if (!selectedContentId.value) return null
  return contentStore.contents.find(c => c.id === selectedContentId.value)
})

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) return 'Unknown'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Upload state
const fileInput = ref(null)
const isDragging = ref(false)
const selectedFiles = ref([])
const uploadingFiles = ref([])
const uploadedFiles = ref([])
const uploadForm = ref({
  name: ''
})

// Filter contents based on search and type
const filteredContents = computed(() => {
  let filtered = contentStore.contents || []

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(c =>
      c.name?.toLowerCase().includes(query) ||
      c.description?.toLowerCase().includes(query)
    )
  }

  // Filter by type
  if (filterType.value) {
    filtered = filtered.filter(c => c.type === filterType.value)
  }

  // Only show contents with secure_url (uploaded files)
  filtered = filtered.filter(c => c.secure_url)

  // Standalone library uploads only (never widget-bound rows from template sync)
  filtered = filtered.filter(c => c.widget == null || c.widget === '')

  return filtered
})

// Load contents when modal opens
const loadContents = async () => {
  try {
    await contentStore.fetchContents({ library_only: 1 })
  } catch (error) {
    console.error('Failed to load contents:', error)
    notify.error('Failed to load media library')
  }
}

// Watch for modal opening
watch(() => props.show, (isOpen) => {
  if (isOpen) {
    activeTab.value = 'gallery'
    selectedContentId.value = null
    searchQuery.value = ''
    filterType.value = props.filterByType
    selectedFiles.value = []
    uploadingFiles.value = []
    uploadedFiles.value = []
    uploadForm.value = { name: '' }
    loadContents()
  }
})

// Watch for filterByType changes
watch(() => props.filterByType, (newType) => {
  filterType.value = newType
})

// Select content
const selectContent = (content) => {
  selectedContentId.value = content.id
}

// Confirm selection and emit
const confirmSelection = () => {
  if (!selectedContentId.value || !selectedContent.value) return

  if (selectedContent.value.secure_url) {
    emit('select', {
      url: selectedContent.value.secure_url,
      content: selectedContent.value
    })
    emit('close')
  }
}

// Handle file selection
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files || [])
  processFiles(files)
}

// Handle drag and drop
const handleDrop = (event) => {
  isDragging.value = false
  const files = Array.from(event.dataTransfer.files || [])
  processFiles(files)
}

// Process selected files
const processFiles = (files) => {
  // Filter by type if specified
  let filtered = files
  if (props.filterByType === 'image') {
    filtered = files.filter(f => f.type.startsWith('image/'))
  } else if (props.filterByType === 'video') {
    filtered = files.filter(f => f.type.startsWith('video/'))
  }

  if (filtered.length === 0) {
    notify.error(`Please select ${props.filterByType || 'image or video'} files`)
    return
  }

  selectedFiles.value = filtered.map(file => ({
    file,
    id: `${Date.now()}-${Math.random()}`,
    name: file.name,
    type: file.type.startsWith('image/') ? 'image' : 'video'
  }))

  // Auto-generate name from first file if not set
  if (!uploadForm.value.name && selectedFiles.value.length > 0) {
    const firstFile = selectedFiles.value[0]
    uploadForm.value.name = firstFile.name.replace(/\.[^/.]+$/, '')
  }
}

// Handle upload
const handleUpload = async () => {
  if (selectedFiles.value.length === 0) {
    notify.error('Please select files to upload')
    return
  }

  if (!uploadForm.value.name?.trim()) {
    notify.error('Please enter a name for the content')
    return
  }

  // Upload each file
  for (const fileItem of selectedFiles.value) {
    await uploadSingleFile(fileItem)
  }
}

// Upload single file
const uploadSingleFile = async (fileItem) => {
  const { file, name, type } = fileItem
  
  // Create upload progress tracker
  const uploadTracker = {
    id: fileItem.id,
    name: file.name,
    progress: 0
  }
  uploadingFiles.value.push(uploadTracker)

  try {
    // Step 1: Create content record
    // CRITICAL: Backend requires 'widget' field - Content model has ForeignKey to Widget
    // For standalone media library uploads, we need to handle this requirement
    const contentName = uploadForm.value.name.trim() || name.replace(/\.[^/.]+$/, '')
    
    if (!contentName) {
      throw new Error('Content name is required')
    }

    // Prepare content data - widget is now optional
    const contentData = {
      name: contentName,
      type: type,
    }

    // Only add widget if provided (allows standalone media library uploads)
    if (props.widgetId) {
      contentData.widget = props.widgetId
      
      // Validate widget ID format if provided
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      const isBackendId = uuidRegex.test(props.widgetId)
      
      if (!isBackendId) {
        // Widget ID is not a UUID - it's likely a local ID
        throw new Error('Widget must be saved to the backend before uploading content. Please save the template first, then try uploading again.')
      }
    }

    console.log('[MediaLibraryModal] Creating content:', contentData)

    let content
    try {
      content = await contentStore.createContent(contentData)
      console.log('[MediaLibraryModal] Content created:', content)
    } catch (createError) {
      // DETAILED ERROR LOGGING - Log the actual server response
      console.error('[MediaLibraryModal] Content creation failed - Full Error Details:', {
        error: createError,
        response: createError.response,
        responseData: createError.response?.data,
        responseStatus: createError.response?.status,
        responseStatusText: createError.response?.statusText,
        requestConfig: {
          url: createError.config?.url,
          method: createError.config?.method,
          headers: createError.config?.headers,
          data: createError.config?.data
        },
        contentData: contentData
      })
      
      // Log validation errors specifically
      console.error('[MediaLibraryModal] Validation Errors:', createError.response?.data)

      // Extract error information - IMPROVED ERROR PARSING
      const errorData = createError.response?.data || {}
      
      // Log the actual error structure for debugging
      console.error('[MediaLibraryModal] Error Data Structure:', JSON.stringify(errorData, null, 2))
      console.error('[MediaLibraryModal] Full Error Response:', createError.response)
      
      // Handle different error response formats
      let errorDetail = ''
      let errorFields = {}
      
      // Check for nested error structure (api_error format from middleware)
      if (errorData.error === 'api_error' || errorData.error) {
        // Handle api_error format: { error: 'api_error', message: '...', details: {...} }
        // The middleware wraps DRF exceptions in this format
        errorDetail = errorData.message || 'An error occurred'
        
        // Extract details - handle both object and string formats
        if (errorData.details) {
          if (typeof errorData.details === 'object' && errorData.details !== null) {
            // DRF exceptions often have a 'detail' field inside details
            if (errorData.details.detail) {
              // This is the actual error message from DRF
              errorDetail = typeof errorData.details.detail === 'string' 
                ? errorData.details.detail 
                : JSON.stringify(errorData.details.detail)
            } else if (errorData.details.errors) {
              // Field-specific errors
              errorFields = errorData.details.errors
            } else if (errorData.details.message) {
              errorDetail = errorData.details.message
            } else {
              // If details is an object with keys, try to extract field errors
              const detailKeys = Object.keys(errorData.details)
              if (detailKeys.length > 0) {
                // Check if it's a field error structure (like { widget: ['This field is required.'] })
                const hasFieldErrors = detailKeys.some(key => 
                  Array.isArray(errorData.details[key]) || 
                  typeof errorData.details[key] === 'string'
                )
                if (hasFieldErrors) {
                  errorFields = errorData.details
                } else {
                  // Stringify the details object to show what's inside
                  try {
                    const detailsStr = JSON.stringify(errorData.details, null, 2)
                    errorDetail = `${errorDetail}\n\nDetails:\n${detailsStr}`
                  } catch (e) {
                    errorDetail = `${errorDetail}\n\nDetails: ${String(errorData.details)}`
                  }
                }
              }
            }
          } else if (typeof errorData.details === 'string') {
            errorDetail = `${errorDetail}\n\nDetails: ${errorData.details}`
          }
        }
      } else if (errorData.detail) {
        // Standard DRF error format: { detail: '...' }
        errorDetail = errorData.detail
        errorFields = errorData.errors || {}
      } else if (errorData.message) {
        // Simple message format: { message: '...' }
        errorDetail = errorData.message
        errorFields = errorData.errors || errorData
      } else if (errorData.error) {
        // Error field format: { error: '...' }
        errorDetail = errorData.error
        errorFields = errorData.errors || errorData
      } else if (typeof errorData === 'object' && Object.keys(errorData).length > 0) {
        // If errorData is an object with keys, try to extract meaningful info
        errorFields = errorData
        // Try to find a message-like field
        const possibleMessages = ['message', 'error', 'detail', 'msg', 'description']
        for (const key of possibleMessages) {
          if (errorData[key]) {
            errorDetail = errorData[key]
            break
          }
        }
        // If no message found, stringify the whole object
        if (!errorDetail) {
          errorDetail = JSON.stringify(errorData, null, 2)
        }
      } else {
        errorDetail = 'An error occurred'
      }

      // Check for specific field errors
      if (errorFields && typeof errorFields === 'object' && Object.keys(errorFields).length > 0) {
        const fieldErrorMessages = Object.keys(errorFields)
          .map(field => {
            const fieldError = errorFields[field]
            if (Array.isArray(fieldError)) {
              return `${field}: ${fieldError.join(', ')}`
            }
            if (typeof fieldError === 'object') {
              return `${field}: ${JSON.stringify(fieldError)}`
            }
            return `${field}: ${fieldError}`
          })
          .join('; ')
        
        if (fieldErrorMessages) {
          throw new Error(`Validation failed: ${fieldErrorMessages}`)
        }
      }

      // Check if error is about missing widget
      if (errorDetail.includes('widget') || errorDetail.includes('Widget') || errorFields?.widget) {
        const widgetError = errorFields?.widget
        const widgetErrorMsg = Array.isArray(widgetError) 
          ? widgetError.join(', ') 
          : (typeof widgetError === 'string' ? widgetError : 'Widget is required')
        throw new Error(`Widget Error: ${widgetErrorMsg}. Please ensure the widget is saved to the backend before uploading content.`)
      }
      
      // Check if error is about invalid widget ID
      if (errorDetail.includes('not found') || errorDetail.includes('does not exist') || errorDetail.includes('Invalid')) {
        throw new Error('Widget not found. The widget may not be saved to the backend yet. Please save the template first, then try uploading again.')
      }

      // Use detailed error message - ensure it's a string
      const errorMessage = typeof errorDetail === 'string' 
        ? errorDetail 
        : JSON.stringify(errorDetail) || 'Failed to create content record'
      throw new Error(errorMessage)
    }

    // Step 2: Upload the file using FormData
    // Backend expects 'file' field in multipart/form-data (see views.py line 1040)
    console.log('[MediaLibraryModal] Starting file upload:', {
      contentId: content.id,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type
    })

    // Simulate progress (real progress would come from axios upload progress event)
    const progressInterval = setInterval(() => {
      if (uploadTracker.progress < 90) {
        uploadTracker.progress += 10
      }
    }, 200)

    try {
      // uploadContent uses contentsAPI.upload which properly constructs FormData
      await contentStore.uploadContent(content.id, file)
      clearInterval(progressInterval)
      uploadTracker.progress = 100

      console.log('[MediaLibraryModal] File upload successful')

      // Refresh content to get updated secure_url
      await contentStore.fetchContent(content.id)
      const updatedContent = contentStore.currentContent || content

      // Move to uploaded files
      setTimeout(() => {
        const index = uploadingFiles.value.findIndex(f => f.id === fileItem.id)
        if (index > -1) {
          uploadingFiles.value.splice(index, 1)
        }
        
        uploadedFiles.value.push({
          id: updatedContent.id,
          name: updatedContent.name,
          url: updatedContent.secure_url || updatedContent.file_url || updatedContent.absolute_file_url,
          content: updatedContent
        })

        // Refresh gallery
        loadContents()
      }, 500)
    } catch (uploadError) {
      clearInterval(progressInterval)
      
      // DETAILED ERROR LOGGING for file upload
      console.error('[MediaLibraryModal] File upload failed - Full Error Details:', {
        error: uploadError,
        response: uploadError.response,
        responseData: uploadError.response?.data,
        responseStatus: uploadError.response?.status,
        responseStatusText: uploadError.response?.statusText,
        requestConfig: {
          url: uploadError.config?.url,
          method: uploadError.config?.method,
          headers: uploadError.config?.headers,
          data: uploadError.config?.data
        },
        contentId: content.id,
        fileName: file.name
      })
      
      // Log validation errors specifically
      console.error('[MediaLibraryModal] Upload Validation Errors:', uploadError.response?.data)

      const index = uploadingFiles.value.findIndex(f => f.id === fileItem.id)
      if (index > -1) {
        uploadingFiles.value.splice(index, 1)
      }

      // Extract detailed error information
      const errorData = uploadError.response?.data || {}
      const errorDetail = errorData.detail || errorData.message || errorData.error || ''
      const errorFields = errorData.errors || errorData
      const receivedFields = errorData.received_fields || []

      // Build detailed error message
      let errorMessage = errorDetail
      if (errorFields && typeof errorFields === 'object' && Object.keys(errorFields).length > 0) {
        const fieldErrors = Object.keys(errorFields)
          .map(field => {
            const fieldError = errorFields[field]
            if (Array.isArray(fieldError)) {
              return `${field}: ${fieldError.join(', ')}`
            }
            return `${field}: ${fieldError}`
          })
          .join('; ')
        errorMessage = fieldErrors || errorMessage
      }

      if (receivedFields.length > 0 && !receivedFields.includes('file')) {
        errorMessage = `File field not found. Received fields: ${receivedFields.join(', ')}. Expected: 'file'`
      }

      throw new Error(errorMessage || 'Failed to upload file')
    }
  } catch (error) {
    const index = uploadingFiles.value.findIndex(f => f.id === fileItem.id)
    if (index > -1) {
      uploadingFiles.value.splice(index, 1)
    }
    
    // Final error handling with detailed logging
    console.error('[MediaLibraryModal] Upload error summary:', {
      message: error.message,
      fullError: error,
      responseData: error.response?.data,
      validationErrors: error.response?.data
    })

    const errorMessage = error.message || 
                         error.response?.data?.detail || 
                         error.response?.data?.message || 
                         error.response?.data?.error ||
                         'Failed to upload file'
    
    notify.error(`Upload failed: ${errorMessage}`)
  }
}

// Select uploaded file
const selectUploadedFile = (file) => {
  if (file.url) {
    emit('select', {
      url: file.url,
      content: file.content
    })
    emit('close')
  }
}

// Handle delete content
const handleDeleteContent = async (content) => {
  try {
    await confirmDelete(
      content.id,
      async () => {
        await contentStore.deleteContent(content.id)
      },
      {
        title: 'Delete Media?',
        message: 'This media will be permanently deleted from your library and cannot be recovered.',
        itemName: content.name || 'Untitled media',
        confirmText: 'Yes, Delete Media',
        loadingText: 'Deleting media...'
      }
    )

    notify.success('Content deleted successfully')
    
    // Refresh gallery
    await loadContents()
    
    // Clear selection if deleted
    if (selectedContentId.value === content.id) {
      selectedContentId.value = null
    }
  } catch (error) {
    if (error.message === 'Delete cancelled') return
    const errorMessage = error.response?.data?.detail || 
                         error.response?.data?.message || 
                         error.message || 
                         'Failed to delete content'
    notify.error(`Delete failed: ${errorMessage}`)
    console.error('Delete error:', error)
  }
}


onMounted(() => {
  // Pre-load contents if not already loaded
  if (contentStore.contents.length === 0) {
    loadContents()
  }
})
</script>

<style scoped>
.modal-enter-active {
  transition: opacity 0.3s ease-out;
}

.modal-leave-active {
  transition: opacity 0.2s ease-in;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

@keyframes modalFadeUp {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Media Thumbnails - 1px Subtle Border */
.media-thumbnail {
  border: 1px solid var(--border-color);
  background: var(--card-bg);
}

.media-thumbnail-default {
  border-color: var(--border-color);
}

.media-thumbnail-default:hover {
  border-color: var(--accent-color);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.media-thumbnail-selected {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.2), 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.dark .media-thumbnail {
  border-color: rgba(255, 255, 255, 0.1);
}

.dark .media-thumbnail-selected {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px rgba(9, 132, 227, 0.3), 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

/* Frosted Glass File Name Overlay */
.media-name-overlay {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.dark .media-name-overlay {
  background: rgba(30, 41, 59, 0.85);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* File Information Sidebar - Paper White */
.media-sidebar {
  background: var(--card-bg);
  border-left: 1px solid var(--border-color);
  transition: all 0.4s ease;
}

.dark .media-sidebar {
  background: var(--card-bg);
}

/* Upload Zone - Dashed Border with Warm Grey */
.upload-zone-default {
  border: 2px dashed var(--border-color);
  background: var(--card-bg);
  transition: all 0.4s ease;
}

.upload-zone-default:hover {
  border-color: var(--accent-color);
  background: rgba(9, 132, 227, 0.05);
}

.upload-zone-active {
  border: 2px dashed var(--accent-color);
  background: rgba(9, 132, 227, 0.1);
  box-shadow: 0 0 0 4px rgba(9, 132, 227, 0.1);
}

.dark .upload-zone-default {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(30, 41, 59, 0.5);
}

.dark .upload-zone-default:hover {
  border-color: var(--accent-color);
  background: rgba(9, 132, 227, 0.1);
}

.dark .upload-zone-active {
  border-color: var(--accent-color);
  background: rgba(9, 132, 227, 0.2);
  box-shadow: 0 0 0 4px rgba(9, 132, 227, 0.2);
}

/* Physical Button Look for Filters */
.filter-button {
  @apply px-4 py-2 text-sm font-medium rounded-lg transition-all;
  transition-duration: 0.4s;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.7));
  border: 1px solid var(--border-color);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  color: var(--text-primary);
}

.filter-button:hover {
  background: linear-gradient(to bottom, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.85));
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.filter-button-active {
  background: linear-gradient(to bottom, var(--accent-color), var(--accent-color));
  color: var(--button-text);
  border-color: var(--accent-color);
  box-shadow: var(--button-shadow);
}

.filter-button-active:hover {
  background: linear-gradient(to bottom, var(--accent-color), var(--accent-color));
  box-shadow: var(--button-shadow-hover);
}

.dark .filter-button {
  background: linear-gradient(to bottom, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.6));
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.dark .filter-button:hover {
  background: linear-gradient(to bottom, rgba(30, 41, 59, 0.9), rgba(30, 41, 59, 0.7));
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.dark .filter-button-active {
  background: linear-gradient(to bottom, var(--accent-color), var(--accent-color));
  box-shadow: var(--button-shadow);
}
</style>
