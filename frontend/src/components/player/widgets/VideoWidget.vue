<template>
  <div class="video-widget">
    <div
      v-for="content in sortedContents"
      :key="content.id"
      class="content-item"
      :style="contentStyle"
    >
      <video
        v-if="content.secure_url"
        :src="ensureAbsoluteUrl(content.secure_url)"
        :data-content-id="content.id"
        class="content-video"
        :style="videoStyle"
        autoplay
        loop
        muted
        playsinline
        @loadedmetadata="onVideoLoaded"
        @play="onVideoPlay"
        @pause="onVideoPause"
        @ended="onVideoEnded"
        @error="onVideoError"
      />
      <div
        v-else
        class="content-error"
        style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: rgba(255,0,0,0.1); color: white; font-size: 12px; padding: 10px; text-align: center;"
      >
        No video URL for content: {{ content.name || content.id }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ensureAbsoluteUrl } from '@/utils/url'

const props = defineProps({
  widget: {
    type: Object,
    required: true
  }
})

const loadedVideos = ref(new Set())
const failedVideos = ref(new Set())
const playingVideos = ref(new Set())

// Sort contents by order
// Filter only active content (safety check - backend should already filter)
const sortedContents = computed(() => {
  if (!props.widget.contents) {
    console.warn(`[VideoWidget] Widget ${props.widget.id} has no contents array`)
    return []
  }
  
  // Filter active content and sort by order
  const contents = [...props.widget.contents]
    .filter(content => content.is_active !== false) // Only render active content
    .sort((a, b) => (a.order || 0) - (b.order || 0))
  
  if (contents.length === 0) {
    console.warn(`[VideoWidget] Widget ${props.widget.id} has no active contents`, {
      totalContents: props.widget.contents.length,
      contents: props.widget.contents.map(c => ({ id: c.id, name: c.name, is_active: c.is_active, secure_url: c.secure_url }))
    })
  } else {
    console.log(`[VideoWidget] Widget ${props.widget.id} rendering ${contents.length} contents`, {
      contents: contents.map(c => ({ id: c.id, name: c.name, secure_url: c.secure_url ? `${c.secure_url.substring(0, 50)}...` : 'NO URL' }))
    })
  }
  
  return contents
})

// Content container style
const contentStyle = computed(() => {
  // Get background color from widget style or use black as default
  const widgetStyle = props.widget.content_json || {}
  const backgroundColor = widgetStyle.backgroundColor || '#000000'
  
  return {
    width: '100%',
    height: '100%',
    position: 'absolute',
    top: 0,
    left: 0,
    overflow: 'hidden', // Prevent bleed-out with contain mode
    backgroundColor: backgroundColor // Fill gaps with background color
  }
})

/**
 * Video style with responsive object-fit
 * CRITICAL: Use 'contain' to ensure full content visibility without cropping
 */
const videoStyle = computed(() => {
  const contentJson = props.widget.content_json || {}
  // CRITICAL: Default to 'contain' to ensure full content visibility
  // Force contain mode to prevent cropping
  const objectFit = 'contain'
  
  return {
    width: '100%',
    height: '100%',
    objectFit: objectFit,
    display: 'block',
    // Center the video (important for contain mode - centers video within container)
    objectPosition: 'center center'
  }
})


const onVideoLoaded = (event) => {
  const video = event.target
  const contentId = video.getAttribute('data-content-id')
  if (contentId) {
    loadedVideos.value.add(contentId)
    failedVideos.value.delete(contentId)
    console.log(`[VideoWidget] Video loaded successfully for content: ${contentId}`, {
      src: video.src.substring(0, 100),
      videoWidth: video.videoWidth,
      videoHeight: video.videoHeight,
      duration: video.duration
    })
    
    // Try to play (autoplay attribute is set, but we also try programmatically as fallback)
    video.play().catch(err => {
      console.warn(`[VideoWidget] Autoplay failed for content ${contentId}:`, err)
    })
  }
}

const onVideoPlay = (event) => {
  const video = event.target
  const contentId = video.getAttribute('data-content-id')
  if (contentId) {
    playingVideos.value.add(contentId)
    console.log(`[VideoWidget] Video playing for content: ${contentId}`)
  }
}

const onVideoPause = (event) => {
  const video = event.target
  const contentId = video.getAttribute('data-content-id')
  if (contentId) {
    playingVideos.value.delete(contentId)
    console.log(`[VideoWidget] Video paused for content: ${contentId}`)
  }
}

const onVideoEnded = (event) => {
  const video = event.target
  const contentId = video.getAttribute('data-content-id')
  if (contentId) {
    console.log(`[VideoWidget] Video ended for content: ${contentId}`)
    // If looping is enabled, video will automatically restart
    // Otherwise, we could trigger next content here
  }
}

const onVideoError = (event) => {
  const video = event.target
  const contentId = video.getAttribute('data-content-id')
  if (contentId) {
    failedVideos.value.add(contentId)
    // Hide failed video gracefully without breaking layout
    video.style.display = 'none'
    
    // Enhanced error logging with full details
    const errorDetails = {
      contentId: contentId,
      attemptedUrl: video.src,
      widgetId: props.widget.id,
      widgetName: props.widget.name,
      widgetType: props.widget.type,
      content: props.widget.contents?.find(c => c.id === contentId),
      error: event.type,
      errorCode: video.error?.code,
      errorMessage: video.error?.message,
      timestamp: new Date().toISOString()
    }
    
    console.error(`[VideoWidget] Failed to load video for content: ${contentId}`, errorDetails)
    
    // Log the full URL that failed
    console.error(`[VideoWidget] Broken video URL: ${video.src}`)
    
    // Check if URL is relative vs absolute
    if (!video.src.startsWith('http://') && !video.src.startsWith('https://')) {
      console.warn(`[VideoWidget] Video URL is relative, might need absolute URL: ${video.src}`)
    }
  }
}
</script>

<style scoped>
.video-widget {
  width: 100%;
  height: 100%;
  position: relative;
  /* CRITICAL: Use black background to fill gaps when object-fit: contain creates letterboxing
     This ensures no transparent gaps are visible when aspect ratios don't match */
  background-color: #000000;
  overflow: hidden; /* Prevent any content from bleeding outside widget bounds */
}

.content-item {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  /* CRITICAL: Use black background to fill gaps when object-fit: contain creates letterboxing
     Background color can be overridden via widget.content_json.backgroundColor */
  background-color: #000000;
  overflow: hidden; /* Prevent video from bleeding outside container with contain mode */
}

.content-video {
  width: 100%;
  height: 100%;
  /* CRITICAL: Use 'contain' to ensure full content visibility without cropping
     Force with !important to override any inline styles */
  object-fit: contain !important;
  display: block;
  /* Center the video - important for contain mode - centers video within container */
  object-position: center center;
  /* Hardware acceleration for smooth playback */
  backface-visibility: hidden;
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  will-change: transform;
  /* Prevent dragging */
  -webkit-user-drag: none;
  -khtml-user-drag: none;
  -moz-user-drag: none;
  -o-user-drag: none;
  pointer-events: auto;
  /* Video rendering optimization */
  image-rendering: auto;
  -webkit-image-rendering: auto;
  /* Prevent layout shifts */
  contain: layout style;
  /* Ensure video fits within widget bounds */
  max-width: 100%;
  max-height: 100%;
  /* Ensure video controls are hidden for digital signage */
  outline: none;
}

/* Hide video controls completely for digital signage */
.content-video::-webkit-media-controls {
  display: none !important;
}

.content-video::-webkit-media-controls-enclosure {
  display: none !important;
}

.content-video::-webkit-media-controls-panel {
  display: none !important;
}

.content-video::-webkit-media-controls-play-button {
  display: none !important;
}

.content-video::-webkit-media-controls-start-playback-button {
  display: none !important;
}

/* Hide controls for Firefox */
.content-video::-moz-media-controls {
  display: none !important;
}

/* Hide controls for other browsers */
.content-video::-ms-media-controls {
  display: none !important;
}
</style>

