<template>
  <div class="text-widget">
    <div
      v-for="content in sortedContents"
      :key="content.id"
      class="content-item"
      :style="contentStyle"
    >
      <div
        class="text-content"
        :style="textStyle"
        :data-content-id="content.id"
      >
        {{ displayText(content) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { resolveWidgetBackgroundColor } from '@/utils/widgetBackground'

const props = defineProps({
  widget: {
    type: Object,
    required: true
  }
})

// Sort contents by order
// Filter only active content (safety check - backend should already filter)
const sortedContents = computed(() => {
  const baseContents = Array.isArray(props.widget.contents) ? props.widget.contents : []
  
  // Filter active content and sort by order
  const contents = [...baseContents]
    .filter(content => content.is_active !== false) // Only render active content
    .sort((a, b) => (a.order || 0) - (b.order || 0))

  if (contents.length > 0) return contents

  // Fallback when backend content rows are temporarily missing:
  // render text from widget JSON so signage does not appear blank.
  const fallbackText = props.widget?.content_json?.text
  if (typeof fallbackText === 'string' && fallbackText.trim()) {
    return [{
      id: `fallback-text-${props.widget.id || 'widget'}`,
      text_content: fallbackText,
      is_active: true,
      order: 0,
    }]
  }

  return contents
})

// Get display text from content
const displayText = (content) => {
  // Priority: text_content > content_json.text > file_url (if text file)
  if (content.text_content) {
    return content.text_content
  }
  if (content.content_json?.text) {
    return content.content_json.text
  }
  // If file_url exists, it might be a text file URL, but we can't load it here
  // The backend should provide the text content in text_content or content_json
  return '[No text content]'
}

// Content container style
const contentStyle = computed(() => {
  return {
    width: '100%',
    height: '100%',
    position: 'absolute',
    top: 0,
    left: 0
  }
})

/**
 * Text style based on widget configuration
 */
const normalizeFontSize = (fontSize) => {
  if (fontSize === undefined || fontSize === null || fontSize === '') return '24px'
  if (typeof fontSize === 'number') return `${fontSize}px`
  const value = String(fontSize).trim()
  if (!value) return '24px'
  if (value.endsWith('px') || value.endsWith('rem') || value.endsWith('em') || value.endsWith('%')) {
    return value
  }
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? `${parsed}px` : '24px'
}

const textStyle = computed(() => {
  const widgetJson = props.widget.content_json || {}
  const fontFamily = widgetJson.fontFamily || 'Arial, sans-serif'
  const fontSize = normalizeFontSize(widgetJson.fontSize || props.widget.font_size)
  const color = widgetJson.color || props.widget.color || '#000000'
  const textAlign = widgetJson.textAlign || props.widget.alignment || 'left'
  const backgroundColor = resolveWidgetBackgroundColor(widgetJson)
  const fontWeight = widgetJson.fontWeight || 'normal'
  const lineHeight = widgetJson.lineHeight || 1.5
  
  return {
    width: '100%',
    height: '100%',
    fontFamily: fontFamily,
    fontSize: fontSize,
    color: color,
    backgroundColor: backgroundColor,
    textAlign: textAlign,
    fontWeight: fontWeight,
    lineHeight: lineHeight,
    padding: '10px',
    boxSizing: 'border-box',
    overflow: 'hidden',
    wordWrap: 'break-word',
    whiteSpace: 'pre-wrap', // Preserve line breaks and spaces
    display: 'flex',
    alignItems: textAlign === 'center' ? 'center' : textAlign === 'right' ? 'flex-end' : 'flex-start',
    justifyContent: textAlign === 'center' ? 'center' : textAlign === 'right' ? 'flex-end' : 'flex-start'
  }
})
</script>

<style scoped>
.text-widget {
  width: 100%;
  height: 100%;
  position: relative;
}

.content-item {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.text-content {
  width: 100%;
  height: 100%;
  /* Hardware acceleration for smooth rendering */
  backface-visibility: hidden;
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  will-change: transform;
  /* Prevent text selection */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  /* Prevent layout shifts */
  contain: layout style paint;
}
</style>

