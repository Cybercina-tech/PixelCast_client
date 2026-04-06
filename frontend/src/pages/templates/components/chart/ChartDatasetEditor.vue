<template>
  <div class="space-y-3">
    <h4 class="text-xs font-semibold uppercase text-gray-400">Series Styling</h4>
    <div
      v-for="(dataset, index) in datasets"
      :key="`series-${index}`"
      class="rounded-lg border border-slate-700 bg-slate-900/40 p-3 space-y-2"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-300 font-medium">{{ dataset.label || `Series ${index + 1}` }}</span>
        <button class="btn-outline px-2 py-0.5 rounded text-[10px]" @click="duplicateDataset(index)">Duplicate</button>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <label class="text-[11px] text-gray-400">
          Background
          <input type="color" :value="safeColor(dataset.backgroundColor, '#3b82f6')" class="w-full h-8 mt-1" @input="patchDataset(index, 'backgroundColor', $event.target.value)" />
        </label>
        <label class="text-[11px] text-gray-400">
          Border
          <input type="color" :value="safeColor(dataset.borderColor, '#3b82f6')" class="w-full h-8 mt-1" @input="patchDataset(index, 'borderColor', $event.target.value)" />
        </label>
      </div>
      <div class="grid grid-cols-3 gap-2">
        <label class="text-[11px] text-gray-400">
          Border
          <input type="number" min="0" step="1" class="input-base w-full px-2 py-1 mt-1 text-xs" :value="dataset.borderWidth ?? 2" @input="patchDataset(index, 'borderWidth', Number($event.target.value || 0))" />
        </label>
        <label class="text-[11px] text-gray-400">
          Tension
          <input type="number" min="0" max="1" step="0.1" class="input-base w-full px-2 py-1 mt-1 text-xs" :value="dataset.tension ?? 0.3" @input="patchDataset(index, 'tension', Number($event.target.value || 0))" />
        </label>
        <label class="editor-switch-row editor-switch-row--compact mt-5">
          <span class="text-[11px] text-primary">Fill</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="Boolean(dataset.fill)"
              @change="patchDataset(index, 'fill', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  datasets: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:datasets'])

const cloneDatasets = () => (props.datasets || []).map((dataset) => ({
  ...dataset,
  data: Array.isArray(dataset.data) ? [...dataset.data] : [],
}))

const patchDataset = (index, key, value) => {
  const datasets = cloneDatasets()
  datasets[index] = { ...datasets[index], [key]: value }
  emit('update:datasets', datasets)
}

const safeColor = (input, fallback) => {
  if (Array.isArray(input)) {
    const first = input.find((item) => typeof item === 'string' && /^#[0-9a-fA-F]{6}$/.test(item))
    return first || fallback
  }
  if (typeof input === 'string' && /^#[0-9a-fA-F]{6}$/.test(input)) {
    return input
  }
  return fallback
}

const duplicateDataset = (index) => {
  const datasets = cloneDatasets()
  const source = datasets[index]
  datasets.splice(index + 1, 0, {
    ...source,
    label: `${source.label || `Series ${index + 1}`} Copy`,
    data: [...(source.data || [])],
  })
  emit('update:datasets', datasets)
}
</script>
