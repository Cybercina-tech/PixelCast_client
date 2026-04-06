<template>
  <div class="album-widget" :style="{ backgroundColor }">
    <div class="media-layer current" :class="currentTransitionClass" :style="layerStyle">
      <template v-if="currentItem">
        <img
          v-if="currentMediaKind !== 'video'"
          :key="`img-${currentItem.id}`"
          :src="currentSrc"
          :alt="currentItem.name || 'Album item'"
          class="album-media"
          :style="mediaStyle"
          @load="onImageLoaded"
          @error="onItemError"
        />
        <video
          v-else
          ref="videoRef"
          :key="`video-${currentItem.id}`"
          :src="currentSrc"
          class="album-media"
          :style="mediaStyle"
          :muted="isMuted"
          autoplay
          playsinline
          preload="auto"
          @ended="onVideoEnded"
          @error="onItemError"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ensureAbsoluteUrl } from '@/utils/url'

const props = defineProps({
  widget: {
    type: Object,
    required: true,
  },
})

const index = ref(0)
const timer = ref(null)
const transitionPulse = ref(false)
const videoRef = ref(null)

const contents = computed(() => {
  const raw = Array.isArray(props.widget?.contents) ? props.widget.contents : []
  return [...raw]
    .filter(item => item?.is_active !== false && (item?.secure_url || item?.file_url))
    .sort((a, b) => (a.order || 0) - (b.order || 0))
})

const styleConfig = computed(() => props.widget?.content_json || {})
const backgroundColor = computed(() => styleConfig.value.backgroundColor || '#000000')
const objectFit = computed(() => styleConfig.value.objectFit || 'contain')
const isMuted = computed(() => styleConfig.value.muted !== false)
const loopPlaylist = computed(() => styleConfig.value.loopPlaylist !== false)
const defaultDurationSec = computed(() => {
  const parsed = Number(styleConfig.value.defaultDurationSec)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 10
})
const transitionMode = computed(() => styleConfig.value.transition || 'fade')
const transitionDurationMs = computed(() => {
  const parsed = Number(styleConfig.value.transitionDurationMs)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 450
})

const currentItem = computed(() => {
  const list = contents.value
  if (!list.length) return null
  const safeIndex = Math.max(0, Math.min(index.value, list.length - 1))
  return list[safeIndex]
})

const currentSrc = computed(() => {
  const rawUrl = currentItem.value?.secure_url || currentItem.value?.file_url || ''
  return ensureAbsoluteUrl(rawUrl)
})

const currentMediaKind = computed(() => {
  const item = currentItem.value
  if (!item) return 'image'
  if (item.type === 'video') return 'video'
  const url = String(item.secure_url || item.file_url || '').toLowerCase()
  if (url.endsWith('.gif')) return 'gif'
  return 'image'
})

const mediaStyle = computed(() => ({
  objectFit: objectFit.value,
  objectPosition: 'center center',
}))
const layerStyle = computed(() => ({
  '--transition-ms': `${transitionDurationMs.value}ms`,
}))

const currentTransitionClass = computed(() => {
  if (!transitionPulse.value) return ''
  if (transitionMode.value === 'slideLeft') return 'slide-left'
  if (transitionMode.value === 'slideRight') return 'slide-right'
  if (transitionMode.value === 'none') return ''
  return 'fade'
})

const clearTimer = () => {
  if (timer.value) {
    clearTimeout(timer.value)
    timer.value = null
  }
}

const queueNext = () => {
  clearTimer()
  const list = contents.value
  if (!list.length) return
  const nextIndex = index.value + 1
  if (nextIndex >= list.length) {
    if (!loopPlaylist.value) return
    index.value = 0
  } else {
    index.value = nextIndex
  }
}

const scheduleByDuration = (durationSec) => {
  clearTimer()
  const ms = Math.max(300, Math.round(durationSec * 1000))
  timer.value = setTimeout(() => {
    transitionPulse.value = true
    queueNext()
    setTimeout(() => { transitionPulse.value = false }, transitionDurationMs.value)
  }, ms)
}

const preloadNextItem = () => {
  const list = contents.value
  if (!list.length) return
  const candidateIndex = index.value + 1 >= list.length
    ? (loopPlaylist.value ? 0 : -1)
    : index.value + 1
  if (candidateIndex < 0) return
  const nextItem = list[candidateIndex]
  if (!nextItem) return
  const src = ensureAbsoluteUrl(nextItem.secure_url || nextItem.file_url || '')
  if (!src) return
  if (nextItem.type === 'video') {
    const ghost = document.createElement('video')
    ghost.src = src
    ghost.preload = 'metadata'
  } else {
    const ghost = new Image()
    ghost.src = src
  }
}

const extractDurationForItem = (item) => {
  if (!item) return defaultDurationSec.value
  const json = item.content_json || {}
  const explicit = Number(json.durationSec ?? item.duration)
  if (Number.isFinite(explicit) && explicit > 0) return explicit
  if (currentMediaKind.value === 'gif') {
    const gifAsVideoDuration = Number(item.video_duration)
    if (Number.isFinite(gifAsVideoDuration) && gifAsVideoDuration > 0) return gifAsVideoDuration
  }
  return defaultDurationSec.value
}

const onVideoEnded = () => {
  transitionPulse.value = true
  queueNext()
  setTimeout(() => { transitionPulse.value = false }, transitionDurationMs.value)
}

const onImageLoaded = () => {
  scheduleByDuration(extractDurationForItem(currentItem.value))
}

const onItemError = () => {
  transitionPulse.value = true
  queueNext()
  setTimeout(() => { transitionPulse.value = false }, transitionDurationMs.value)
}

watch(currentItem, () => {
  clearTimer()
  if (!currentItem.value) return
  preloadNextItem()
  if (currentMediaKind.value !== 'video') {
    scheduleByDuration(extractDurationForItem(currentItem.value))
  }
}, { immediate: true })

watch(contents, (list) => {
  if (!list.length) {
    index.value = 0
    clearTimer()
    return
  }
  if (index.value >= list.length) index.value = 0
}, { deep: true })

onMounted(() => {
  if (contents.value.length > 0) {
    index.value = 0
  }
})

onBeforeUnmount(() => {
  clearTimer()
})
</script>

<style scoped>
.album-widget {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.media-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.album-media {
  width: 100%;
  height: 100%;
  display: block;
}

.media-layer.fade {
  animation: albumFade var(--transition-ms, 450ms) ease;
}

.media-layer.slide-left {
  animation: albumSlideLeft var(--transition-ms, 450ms) ease;
}

.media-layer.slide-right {
  animation: albumSlideRight var(--transition-ms, 450ms) ease;
}

@keyframes albumFade {
  from { opacity: 0.35; }
  to { opacity: 1; }
}

@keyframes albumSlideLeft {
  from { transform: translateX(8%); opacity: 0.65; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes albumSlideRight {
  from { transform: translateX(-8%); opacity: 0.65; }
  to { transform: translateX(0); opacity: 1; }
}
</style>
