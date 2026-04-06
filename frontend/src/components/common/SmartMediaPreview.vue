<template>
  <div class="relative w-full h-full overflow-hidden bg-slate-100 dark:bg-gray-900">
    <!-- Image Preview -->
    <img
      v-if="mediaType === 'image' && resolvedUrl"
      :src="resolvedUrl"
      :alt="alt || 'Media preview'"
      class="w-full h-full object-cover transition-transform duration-300"
      :class="{ 'hover:scale-105': enableHoverZoom }"
      @load="handleLoad"
      @error="handleError"
    />

    <!-- Video Preview -->
    <div
      v-else-if="mediaType === 'video' && resolvedUrl"
      class="relative w-full h-full"
      @mouseenter="handleVideoHover(true)"
      @mouseleave="handleVideoHover(false)"
    >
      <video
        ref="videoRef"
        :src="resolvedUrl"
        :poster="posterUrl"
        :muted="muted"
        :loop="loop"
        :playsinline="playsinline"
        :autoplay="autoplay"
        :preload="preload"
        class="w-full h-full object-cover"
        @loadedmetadata="handleVideoMetadata"
        @play="isVideoPlaying = true"
        @pause="isVideoPlaying = false"
        @error="handleError"
      />
      <!-- Video Play Overlay -->
      <div
        v-if="!isVideoPlaying && !playOnHover"
        class="absolute inset-0 flex items-center justify-center bg-slate-900/25 dark:bg-black/30 cursor-pointer z-10"
        @click="playVideo"
      >
        <div class="w-16 h-16 bg-white/70 dark:bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/80 dark:hover:bg-white/30 transition-colors">
          <svg class="w-8 h-8 text-slate-800 dark:text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        </div>
      </div>
      <!-- Video Duration Badge -->
      <div
        v-if="videoDuration && showDuration"
        class="absolute bottom-2 right-2 px-2 py-1 bg-slate-900/70 text-white text-xs rounded backdrop-blur-sm z-10"
      >
        {{ formatDuration(videoDuration) }}
      </div>
    </div>

    <!-- Fallback: File Not Found -->
    <div
      v-else
      class="absolute inset-0 flex flex-col items-center justify-center bg-slate-100 dark:bg-gray-800 text-slate-500 dark:text-gray-500"
    >
      <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <span v-if="fileExtension" class="text-xs font-medium">{{ fileExtension.toUpperCase() }}</span>
      <span class="text-xs mt-1">File Not Found</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { resolveMediaFileUrl } from '@/utils/mediaUrl'

const props = defineProps({
  fileUrl: {
    type: String,
    default: null
  },
  fileType: {
    type: String,
    default: null // 'image' or 'video'
  },
  alt: {
    type: String,
    default: 'Media preview'
  },
  enableHoverZoom: {
    type: Boolean,
    default: true
  },
  autoplay: {
    type: Boolean,
    default: false
  },
  muted: {
    type: Boolean,
    default: true
  },
  loop: {
    type: Boolean,
    default: true
  },
  playsinline: {
    type: Boolean,
    default: true
  },
  preload: {
    type: String,
    default: 'metadata' // 'none', 'metadata', 'auto'
  },
  showDuration: {
    type: Boolean,
    default: true
  },
  videoDuration: {
    type: Number,
    default: null
  },
  posterUrl: {
    type: String,
    default: null
  },
  playOnHover: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['load', 'error', 'play', 'pause', 'duration'])

// State
const error = ref(false)
const videoRef = ref(null)
const isVideoPlaying = ref(false)
const hoverTimeout = ref(null)

// Computed
const mediaType = computed(() => {
  if (props.fileType) {
    const explicitType = String(props.fileType).toLowerCase().trim()
    if (explicitType.startsWith('image')) return 'image'
    if (explicitType.startsWith('video')) return 'video'
  }
  // Infer from URL
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
  error.value = false
  emit('load')
}

const handleError = (event) => {
  error.value = true
  emit('error', event)
}

const handleVideoMetadata = () => {
  if (videoRef.value) {
    // Get duration if not provided
    if (!props.videoDuration && videoRef.value.duration) {
      emit('duration', videoRef.value.duration)
    }
  }
}

const handleVideoHover = async (isHovering) => {
  if (!props.playOnHover || !videoRef.value) return
  
  if (isHovering) {
    // Clear any existing timeout
    if (hoverTimeout.value) {
      clearTimeout(hoverTimeout.value)
    }
    // Play after a short delay
    hoverTimeout.value = setTimeout(async () => {
      if (videoRef.value && !isVideoPlaying.value) {
        await playVideo()
      }
    }, 300)
  } else {
    // Clear timeout
    if (hoverTimeout.value) {
      clearTimeout(hoverTimeout.value)
      hoverTimeout.value = null
    }
    // Pause video
    if (videoRef.value && isVideoPlaying.value) {
      pauseVideo()
    }
  }
}

const playVideo = async () => {
  if (!videoRef.value) return
  
  try {
    await videoRef.value.play()
    isVideoPlaying.value = true
    emit('play')
  } catch (err) {
    console.warn('Failed to play video:', err)
  }
}

const pauseVideo = () => {
  if (!videoRef.value) return
  
  videoRef.value.pause()
  isVideoPlaying.value = false
  emit('pause')
}

const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Watch for URL changes
watch(() => props.fileUrl, () => {
  error.value = false
  isVideoPlaying.value = false
}, { immediate: true })

// Watch for autoplay changes
watch(() => props.autoplay, (newVal) => {
  if (newVal && videoRef.value && mediaType.value === 'video') {
    playVideo()
  }
})

// Lifecycle
onMounted(() => {
  // Auto-play if requested
  if (props.autoplay && mediaType.value === 'video' && videoRef.value) {
    playVideo()
  }
})

onUnmounted(() => {
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value)
  }
  if (videoRef.value) {
    videoRef.value.pause()
  }
})
</script>

<style scoped>
/* Additional styles if needed */
</style>

