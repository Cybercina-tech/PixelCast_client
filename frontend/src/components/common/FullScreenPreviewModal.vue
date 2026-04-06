<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="$emit('close')"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity" aria-hidden="true"></div>

        <!-- Modal Content -->
        <div class="flex items-center justify-center min-h-screen px-4 py-8">
          <div
            class="relative backdrop-blur-lg bg-gray-900/95 border border-white/10 rounded-2xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden"
            @click.stop
          >
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
              <div class="flex items-center gap-3">
                <div class="w-2 h-2 rounded-full bg-green-500"></div>
                <h3 class="text-lg font-semibold text-white">{{ mediaName || 'Media Preview' }}</h3>
                <span
                  v-if="mediaType"
                  :class="[
                    'px-2 py-1 rounded text-xs font-medium',
                    mediaType === 'image' ? 'bg-blue-500/80 text-white' : 'bg-purple-500/80 text-white'
                  ]"
                >
                  {{ mediaType === 'image' ? 'IMAGE' : 'VIDEO' }}
                </span>
              </div>
              <button
                @click="$emit('close')"
                class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors duration-200"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Media Container -->
            <div class="relative bg-black flex items-center justify-center h-[calc(90vh-120px)] overflow-hidden">
              <!-- Image Preview -->
              <div v-if="mediaType === 'image' && fileUrl" class="w-full h-full flex items-center justify-center p-4">
                <img
                  :src="resolvedUrl"
                  :alt="mediaName || 'Image preview'"
                  class="w-full h-full object-contain rounded-lg shadow-2xl"
                  @load="handleLoad"
                  @error="handleError"
                />
              </div>

              <!-- Video Preview -->
              <div v-else-if="mediaType === 'video' && fileUrl" class="w-full h-full flex items-center justify-center p-4">
                <div class="relative w-full h-full">
                  <video
                    ref="videoRef"
                    :src="resolvedUrl"
                    :poster="posterUrl"
                    controls
                    autoplay
                    loop
                    muted
                    playsinline
                    class="w-full h-full object-contain rounded-lg shadow-2xl"
                    @loadedmetadata="handleVideoMetadata"
                    @error="handleError"
                  />
                  <!-- Video Info Overlay -->
                  <div
                    v-if="videoDuration"
                    class="absolute bottom-4 left-4 px-3 py-2 bg-black/70 backdrop-blur-sm text-white text-sm rounded-lg"
                  >
                    Duration: {{ formatDuration(videoDuration) }}
                  </div>
                </div>
              </div>

              <!-- Loading State -->
              <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black/50">
                <div class="flex flex-col items-center gap-3">
                  <div class="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                  <span class="text-gray-400">Loading media...</span>
                </div>
              </div>

              <!-- Error State -->
              <div v-if="error" class="absolute inset-0 flex items-center justify-center bg-black/50">
                <div class="text-center">
                  <svg class="w-20 h-20 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p class="text-gray-400 font-medium mb-2">Failed to load media</p>
                  <p class="text-gray-500 text-sm">{{ fileExtension ? `File type: ${fileExtension.toUpperCase()}` : '' }}</p>
                </div>
              </div>
            </div>

            <!-- Footer with Metadata -->
            <div
              v-if="metadata && !error"
              class="px-6 py-4 border-t border-white/10 bg-gray-900/50"
            >
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div v-if="metadata.width && metadata.height">
                  <span class="text-gray-400">Dimensions:</span>
                  <span class="text-white ml-2">{{ metadata.width }}×{{ metadata.height }}</span>
                </div>
                <div v-if="metadata.fileSize">
                  <span class="text-gray-400">Size:</span>
                  <span class="text-white ml-2">{{ formatFileSize(metadata.fileSize) }}</span>
                </div>
                <div v-if="metadata.duration">
                  <span class="text-gray-400">Duration:</span>
                  <span class="text-white ml-2">{{ formatDuration(metadata.duration) }}</span>
                </div>
                <div v-if="metadata.createdAt">
                  <span class="text-gray-400">Uploaded:</span>
                  <span class="text-white ml-2">{{ formatDate(metadata.createdAt) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { resolveMediaFileUrl } from '@/utils/mediaUrl'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  fileUrl: {
    type: String,
    default: null
  },
  fileType: {
    type: String,
    default: null
  },
  mediaName: {
    type: String,
    default: 'Media Preview'
  },
  videoDuration: {
    type: Number,
    default: null
  },
  posterUrl: {
    type: String,
    default: null
  },
  metadata: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

// State
const loading = ref(true)
const error = ref(false)
const videoRef = ref(null)

// Computed
const mediaType = computed(() => {
  if (props.fileType) {
    return props.fileType
  }
  if (props.fileUrl) {
    const url = props.fileUrl.toLowerCase()
    if (url.match(/\.(jpg|jpeg|png|gif|webp|svg|bmp)$/)) {
      return 'image'
    }
    if (url.match(/\.(mp4|webm|ogg|mov|avi|mkv)$/)) {
      return 'video'
    }
  }
  return null
})

const fileExtension = computed(() => {
  if (!props.fileUrl) return null
  const match = props.fileUrl.match(/\.([^.]+)(\?|$)/)
  return match ? match[1] : null
})

const resolvedUrl = computed(() => {
  if (!props.fileUrl) return null
  if (error.value) return null
  return resolveMediaFileUrl(props.fileUrl)
})

// Methods
const handleLoad = () => {
  loading.value = false
  error.value = false
}

const handleError = () => {
  loading.value = false
  error.value = true
}

const handleVideoMetadata = () => {
  loading.value = false
}

const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// Watch for show changes
watch(() => props.show, (newVal) => {
  if (newVal) {
    loading.value = true
    error.value = false
  }
})

// Watch for URL changes
watch(() => props.fileUrl, () => {
  loading.value = true
  error.value = false
}, { immediate: true })
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
</style>

