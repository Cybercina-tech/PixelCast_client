<template>
  <div
    class="layer"
    :style="layerStyle"
  >
    <WidgetRenderer
      v-for="widget in sortedWidgets"
      :key="widget.id"
      :widget="widget"
      :template-width="props.templateWidth"
      :template-height="props.templateHeight"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import WidgetRenderer from './WidgetRenderer.vue'

const props = defineProps({
  layer: {
    type: Object,
    required: true
  },
  templateWidth: {
    type: Number,
    default: 1920
  },
  templateHeight: {
    type: Number,
    default: 1080
  }
})

const layerStyle = computed(() => {
  const { x = 0, y = 0, width = 0, height = 0, z_index = 0, background_color, opacity } = props.layer
  const safeOpacity = opacity !== undefined && opacity !== null ? Math.max(0, Math.min(1, opacity)) : 1

  return {
    position: 'absolute',
    left: `${Math.max(0, Number(x) || 0)}px`,
    top: `${Math.max(0, Number(y) || 0)}px`,
    width: `${Math.max(1, Number(width) || 1)}px`,
    height: `${Math.max(1, Number(height) || 1)}px`,
    zIndex: z_index,
    backgroundColor: background_color || 'transparent',
    opacity: safeOpacity,
    overflow: 'hidden',
    transform: 'translateZ(0)',
    WebkitTransform: 'translateZ(0)',
    visibility: 'visible',
    display: 'block',
  }
})

// Sort widgets by z_index for proper rendering order
// Filter only active widgets (safety check - backend should already filter)
const sortedWidgets = computed(() => {
  if (!props.layer.widgets || !Array.isArray(props.layer.widgets)) {
    console.warn(`[LayerRenderer] Layer ${props.layer.id} has no widgets array`)
    return []
  }
  
  // Filter active widgets and sort by z_index
  const widgets = [...props.layer.widgets]
    .filter(widget => widget.is_active !== false) // Only render active widgets
    .sort((a, b) => {
      const zA = a.z_index || 0
      const zB = b.z_index || 0
      if (zA !== zB) return zA - zB
      return (a.name || '').localeCompare(b.name || '')
    })
  
  if (widgets.length === 0) {
    console.warn(`[LayerRenderer] Layer ${props.layer.id} (${props.layer.name}) has no active widgets`, {
      totalWidgets: props.layer.widgets.length,
      widgets: props.layer.widgets.map(w => ({ id: w.id, name: w.name, is_active: w.is_active }))
    })
  } else {
    console.log(`[LayerRenderer] Layer ${props.layer.id} rendering ${widgets.length} widgets`, {
      layerName: props.layer.name,
      widgets: widgets.map(w => ({ id: w.id, name: w.name, type: w.type, contentsCount: w.contents?.length || 0 }))
    })
  }
  
  return widgets
})
</script>

<style scoped>
.layer {
  position: absolute;
  box-sizing: border-box;
  will-change: transform;
  backface-visibility: hidden;
  overflow: hidden;
}
</style>

