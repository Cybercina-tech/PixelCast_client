<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-2">
      <h3 class="text-sm font-semibold text-gray-300 uppercase">Chart Properties</h3>
      <div class="flex items-center gap-2">
        <button class="btn-outline px-2 py-1 rounded text-xs" @click="resetConfig">Reset</button>
        <select class="select-base px-2 py-1 text-xs" @change="applyPreset($event.target.value)">
          <option value="">Preset</option>
          <option v-for="preset in chartPresets" :key="preset.id" :value="preset.id">{{ preset.name }}</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-2 rounded-lg bg-gray-800/50 p-1">
      <button
        class="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
        :class="mode === 'basic' ? 'bg-accent-color text-white' : 'text-muted hover:text-primary'"
        @click="mode = 'basic'"
      >
        Builder
      </button>
      <button
        class="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
        :class="mode === 'json' ? 'bg-accent-color text-white' : 'text-muted hover:text-primary'"
        @click="mode = 'json'"
      >
        JSON
      </button>
    </div>

    <div class="space-y-3">
      <label class="block text-xs font-medium text-gray-400">Chart Type</label>
      <select class="select-base w-full px-3 py-2 text-sm" :value="config.type" @change="setChartType($event.target.value)">
        <option v-for="type in chartTypeOptions" :key="type" :value="type">{{ type }}</option>
      </select>
    </div>

    <template v-if="mode === 'basic'">
      <ChartDataTable
        :labels="config.data.labels"
        :datasets="config.data.datasets"
        @update:labels="patchData('labels', $event)"
        @update:datasets="patchData('datasets', $event)"
      />
      <ChartDatasetEditor
        :datasets="config.data.datasets"
        @update:datasets="patchData('datasets', $event)"
      />
      <ChartStyleEditor
        :options="config.options"
        @update:options="patchOptions"
      />
      <button class="btn-outline px-2 py-1 rounded text-xs" @click="randomizeValues">Randomize Sample</button>
    </template>

    <template v-else>
      <ChartJsonEditor
        v-model="jsonText"
        :error="jsonError"
      />
      <button class="btn-outline px-2 py-1 rounded text-xs" @click="applyJson">Apply JSON</button>
    </template>

    <div v-if="validationErrors.length" class="rounded-lg border border-red-500/40 bg-red-500/10 p-2">
      <p class="text-xs text-red-300 font-medium mb-1">Validation</p>
      <ul class="text-xs text-red-300 space-y-1">
        <li v-for="error in validationErrors" :key="error">- {{ error }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import ChartDataTable from './ChartDataTable.vue'
import ChartDatasetEditor from './ChartDatasetEditor.vue'
import ChartStyleEditor from './ChartStyleEditor.vue'
import ChartJsonEditor from './ChartJsonEditor.vue'
import {
  chartPresets,
  chartTypeOptions,
  createDefaultChartConfig,
  fromWidgetChartPayload,
  normalizeChartConfig,
  toWidgetChartPayload,
  validateChartConfig,
} from '@/utils/chartConfig'

const props = defineProps({
  widget: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update'])

const mode = ref('basic')
const jsonText = ref('')
const jsonError = ref('')
const config = ref(createDefaultChartConfig('bar'))
const validationErrors = ref([])

const syncFromWidget = () => {
  config.value = fromWidgetChartPayload(props.widget)
  jsonText.value = JSON.stringify(config.value, null, 2)
  validationErrors.value = validateChartConfig(config.value).errors
}

watch(
  () => props.widget,
  () => {
    syncFromWidget()
  },
  { immediate: true, deep: true },
)

const emitConfig = () => {
  const { normalized, errors } = validateChartConfig(config.value)
  config.value = normalized
  validationErrors.value = errors
  jsonText.value = JSON.stringify(normalized, null, 2)
  const payload = toWidgetChartPayload(normalized)
  emit('update', payload)
}

const patchData = (key, value) => {
  config.value = normalizeChartConfig({
    ...config.value,
    data: {
      ...config.value.data,
      [key]: value,
    },
  })
  emitConfig()
}

const patchOptions = (value) => {
  config.value = normalizeChartConfig({
    ...config.value,
    options: value,
  })
  emitConfig()
}

const setChartType = (type) => {
  config.value = normalizeChartConfig({
    ...config.value,
    type,
  })
  emitConfig()
}

const applyPreset = (presetId) => {
  if (!presetId) return
  const preset = chartPresets.find((item) => item.id === presetId)
  if (!preset) return
  config.value = normalizeChartConfig(preset.config)
  emitConfig()
}

const resetConfig = () => {
  config.value = createDefaultChartConfig(config.value.type || 'bar')
  emitConfig()
}

const randomizeValues = () => {
  const labelsLength = config.value.data.labels.length
  const datasets = config.value.data.datasets.map((dataset) => ({
    ...dataset,
    data: Array.from({ length: labelsLength }).map(() => Math.floor(Math.random() * 200) + 1),
  }))
  patchData('datasets', datasets)
}

const applyJson = () => {
  try {
    const parsed = JSON.parse(jsonText.value)
    config.value = normalizeChartConfig(parsed)
    jsonError.value = ''
    emitConfig()
  } catch (error) {
    jsonError.value = `Invalid JSON: ${error.message}`
  }
}
</script>
