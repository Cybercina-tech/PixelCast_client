<template>
  <div class="relative">
    <!-- Monitor Frame -->
    <div class="relative bg-gray-900 rounded-lg p-4 border-2 border-gray-700 shadow-2xl">
      <!-- Monitor Screen -->
      <div
        ref="monitorScreenRef"
        class="relative bg-black rounded overflow-hidden aspect-video flex items-center justify-center"
        :class="{ 'border-2 border-green-500': isOnline, 'border-2 border-gray-600': !isOnline }"
      >
        <!-- Active Template Preview: scale entire template to fit (same coordinate space as player) -->
        <div
          v-if="hasRenderableTemplate"
          class="absolute inset-0 flex items-center justify-center overflow-hidden"
        >
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
        </div>
        <div v-else-if="activeTemplate" class="w-full h-full relative">
          <div class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center text-gray-300">
            <h3 class="text-sm font-semibold mb-1">{{ activeTemplate.name }}</h3>
            <p class="text-xs text-gray-500">Template has no visible layers</p>
          </div>
        </div>
        <!-- No Template State -->
        <div v-else class="text-center text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p class="text-sm">No Active Template</p>
        </div>
        <!-- Online Indicator -->
        <div class="absolute top-2 right-2">
          <div
            :class="[
              'w-3 h-3 rounded-full',
              isOnline ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]' : 'bg-gray-500',
            ]"
          ></div>
        </div>
      </div>
      <!-- Monitor Stand -->
      <div class="mt-2 flex justify-center">
        <div class="w-24 h-2 bg-gray-800 rounded-b"></div>
      </div>
    </div>
    <!-- Take Screenshot Button -->
    <button
      type="button"
      class="mt-4 w-full min-h-[44px] px-4 py-3 bg-blue-600/80 hover:bg-blue-600 text-white rounded-lg transition-all duration-200 flex items-center justify-center gap-2 backdrop-blur-sm border border-blue-500/30"
      :disabled="!isOnline || loading"
      @click="$emit('take-screenshot')"
    >
      <svg
        v-if="!loading"
        class="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <svg
        v-else
        class="animate-spin w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>{{ loading ? 'Capturing...' : 'Take Screenshot' }}</span>
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import LayerRenderer from '@/components/player/LayerRenderer.vue'
import { useTemplatePreviewScale } from '@/composables/useTemplatePreviewScale.js'
import { buildPlaybackLayers, templateHasRenderablePlayback } from '@/utils/templatePlaybackLayers'

const props = defineProps({
  activeTemplate: {
    type: Object,
    default: null,
  },
  isOnline: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['take-screenshot'])
const monitorScreenRef = ref(null)

const templateWidth = computed(() => Number(props.activeTemplate?.width) || 1920)
const templateHeight = computed(() => Number(props.activeTemplate?.height) || 1080)

const { clipWrapperStyle, innerStageStyle } = useTemplatePreviewScale(
  monitorScreenRef,
  templateWidth,
  templateHeight
)

const sortedLayers = computed(() =>
  props.activeTemplate ? buildPlaybackLayers(props.activeTemplate) : []
)

const hasRenderableTemplate = computed(
  () => !!props.activeTemplate && templateHasRenderablePlayback(props.activeTemplate)
)

function getCaptureElement() {
  return monitorScreenRef.value
}

defineExpose({
  getCaptureElement,
})
</script>

<style scoped>
.preview-canvas {
  isolation: isolate;
}
</style>

