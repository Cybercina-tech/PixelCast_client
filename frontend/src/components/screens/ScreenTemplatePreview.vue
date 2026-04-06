<template>
  <div class="relative w-full h-full min-h-0 bg-black overflow-hidden">
    <div
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center bg-card z-[1]"
    >
      <div
        class="w-7 h-7 rounded-full border-2 border-border-color border-t-[var(--accent-color,#3b82f6)] animate-spin opacity-80"
      />
    </div>
    <TemplatePreviewStage
      v-else-if="previewTemplate && hasActiveLayers"
      :template="previewTemplate"
    />
    <div
      v-else-if="screen.active_template"
      class="absolute inset-0 flex flex-col items-center justify-center p-3 text-center bg-card"
    >
      <DocumentTextIcon class="w-8 h-8 text-muted mx-auto mb-2 shrink-0" />
      <p class="text-xs text-primary font-medium truncate max-w-full">
        {{ screen.active_template.name }}
      </p>
      <p class="text-[10px] text-muted mt-1">No preview layers</p>
    </div>
    <div v-else class="absolute inset-0 flex flex-col items-center justify-center bg-card">
      <TvIcon class="w-8 h-8 text-muted mx-auto mb-2" />
      <p class="text-xs text-muted">No Template</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { DocumentTextIcon, TvIcon } from '@heroicons/vue/24/outline'
import { templatesAPI } from '@/services/api'
import { useTemplatesStore } from '@/stores/templates'
import TemplatePreviewStage from './TemplatePreviewStage.vue'
import { templateHasRenderablePlayback } from '@/utils/templatePlaybackLayers'

const props = defineProps({
  screen: {
    type: Object,
    required: true,
  },
})

const templatesStore = useTemplatesStore()
const previewTemplate = ref(null)
const loading = ref(false)

const hasActiveLayers = computed(() => templateHasRenderablePlayback(previewTemplate.value))

async function loadTemplateForPreview() {
  const id = props.screen?.active_template?.id
  if (!id) {
    previewTemplate.value = null
    return
  }

  const fromStore = templatesStore.templates.find((t) => t.id === id)
  if (fromStore && templateHasRenderablePlayback(fromStore)) {
    previewTemplate.value = fromStore
    return
  }
  if (
    templatesStore.currentTemplate?.id === id &&
    templateHasRenderablePlayback(templatesStore.currentTemplate)
  ) {
    previewTemplate.value = templatesStore.currentTemplate
    return
  }

  loading.value = true
  try {
    const { data } = await templatesAPI.detail(id)
    previewTemplate.value = data
    const idx = templatesStore.templates.findIndex((t) => t.id === id)
    if (idx !== -1) {
      templatesStore.templates[idx] = data
    }
  } catch {
    previewTemplate.value = null
  } finally {
    loading.value = false
  }
}

watch(
  () => props.screen?.active_template?.id,
  () => {
    loadTemplateForPreview()
  },
  { immediate: true }
)
</script>
