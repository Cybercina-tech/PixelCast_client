<template>
  <div
    ref="viewportRef"
    class="absolute inset-0 flex items-center justify-center overflow-hidden bg-black"
  >
    <template v-if="hasRenderable">
      <div :style="clipWrapperStyle" class="shrink-0">
        <div :style="innerStageStyle" class="relative preview-canvas">
          <LayerRenderer
            v-for="layer in sortedLayers"
            :key="layer.id"
            :layer="layer"
            :template-width="templateWidth"
            :template-height="templateHeight"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import LayerRenderer from '@/components/player/LayerRenderer.vue'
import { useTemplatePreviewScale } from '@/composables/useTemplatePreviewScale.js'
import {
  buildPlaybackLayers,
  templateHasRenderablePlayback,
} from '@/utils/templatePlaybackLayers'

const props = defineProps({
  template: {
    type: Object,
    required: true,
  },
})

const viewportRef = ref(null)
const templateWidth = computed(() => Number(props.template?.width) || 1920)
const templateHeight = computed(() => Number(props.template?.height) || 1080)

const { clipWrapperStyle, innerStageStyle } = useTemplatePreviewScale(
  viewportRef,
  templateWidth,
  templateHeight
)

/** Same layer tree as WebPlayer (merges config_json.widgets with DB widgets). */
const sortedLayers = computed(() => buildPlaybackLayers(props.template))

const hasRenderable = computed(() => templateHasRenderablePlayback(props.template))
</script>

<style scoped>
.preview-canvas {
  isolation: isolate;
}
</style>
