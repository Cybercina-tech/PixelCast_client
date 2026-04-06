<template>
  <div class="image-widget">
    <div
      v-for="content in sortedContents"
      :key="content.id"
      class="content-item"
      :style="contentStyle"
    >
      <img
        v-if="content.secure_url"
        :src="getImageSrc(content)"
        :alt="content.name || 'Content'"
        :data-content-id="content.id"
        class="content-image"
        :style="imageStyle"
        @load="onImageLoad"
        @error="onImageError"
      />
      <div
        v-else
        class="content-error"
        style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: rgba(255,0,0,0.1); color: white; font-size: 12px; padding: 10px; text-align: center;"
      >
        No image URL for content: {{ content.name || content.id }}
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

const loadedImages = ref(new Set())
const failedImages = ref(new Set())

// Sort contents by order
// Filter only active content (safety check - backend should already filter)
const sortedContents = computed(() => {
  if (!props.widget.contents) return []
  
  // Filter active content and sort by order
  const contents = [...props.widget.contents]
    .filter(content => content.is_active !== false) // Only render active content
    .sort((a, b) => (a.order || 0) - (b.order || 0))
  
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
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden', // Prevent bleed-out with contain mode
    backgroundColor: backgroundColor // Fill gaps with background color
  }
})

/**
 * Image style with responsive object-fit
 * CRITICAL: Use 'contain' to ensure full content visibility without cropping
 * 'contain' ensures the entire image is visible, with background color filling any gaps
 */
const imageStyle = computed(() => {
  // CRITICAL: Force 'contain' mode to ensure full content visibility
  // This prevents any cropping of images
  const objectFit = 'contain'
  
  return {
    width: '100%',
    height: '100%',
    objectFit: objectFit,
    display: 'block',
    // Center the image (important for contain mode - centers the image within container)
    objectPosition: 'center center',
    // Prevent image distortion
    imageRendering: 'auto',
    // Smooth scaling
    imageRendering: '-webkit-optimize-contrast'
  }
})

const onImageLoad = (event) => {
  const img = event.target
  const contentId = img.getAttribute('data-content-id')
  if (contentId) {
    loadedImages.value.add(contentId)
    failedImages.value.delete(contentId)
  }
}

const onImageError = (event) => {
  const img = event.target
  const contentId = img.getAttribute('data-content-id')
  if (contentId) {
    failedImages.value.add(contentId)
    // Hide failed image gracefully without breaking layout
    img.style.display = 'none'
    
    console.error(`[ImageWidget] Failed to load image content: ${contentId}`)
  }
}

const getImageSrc = (content) => {
  const absoluteUrl = ensureAbsoluteUrl(content?.secure_url || '')
  if (!absoluteUrl) return absoluteUrl

  // Cache-busting token priority:
  // 1) backend content fingerprint (file_hash)
  // 2) backend content update timestamp
  // 3) explicit widget version flag (set by editor on URL change/select)
  // 4) content id (stable fallback per item)
  const widgetJson = props.widget?.content_json || {}
  const token = content?.file_hash || content?.updated_at || widgetJson?.imageVersion || content?.id
  if (!token) return absoluteUrl

  const separator = absoluteUrl.includes('?') ? '&' : '?'
  return `${absoluteUrl}${separator}v=${encodeURIComponent(String(token))}`
}
</script>

<style scoped>
.image-widget {
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
  /* CRITICAL: Use flexbox to center image content */
  display: flex;
  align-items: center;
  justify-content: center;
  /* CRITICAL: Use black background to fill gaps when object-fit: contain creates letterboxing
     Background color can be overridden via widget.content_json.backgroundColor */
  background-color: #000000;
  overflow: hidden; /* Prevent image from bleeding outside container with contain mode */
}

.content-image {
  width: 100%;
  height: 100%;
  /* CRITICAL: Use 'contain' to ensure full content visibility without cropping
     This ensures the entire image is visible, with background color filling any gaps
     Force with !important to override any inline styles */
  object-fit: contain !important;
  display: block;
  /* CRITICAL: Center the image both horizontally and vertically
     object-position centers the image in contain mode
     This ensures image is perfectly centered in widget container */
  object-position: center center;
  /* Hardware acceleration for smooth scaling */
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
  /* Image rendering optimization */
  image-rendering: auto;
  -webkit-image-rendering: auto;
  /* Prevent layout shifts */
  contain: layout style;
  /* Ensure image fits within widget bounds */
  max-width: 100%;
  max-height: 100%;
}
</style>

