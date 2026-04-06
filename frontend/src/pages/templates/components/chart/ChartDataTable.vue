<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h4 class="text-xs font-semibold uppercase text-gray-400">Data Table</h4>
      <div class="flex gap-2">
        <button class="btn-outline px-2 py-1 rounded text-xs" @click="addRow">Add Row</button>
        <button class="btn-outline px-2 py-1 rounded text-xs" @click="addDataset">Add Series</button>
      </div>
    </div>

    <div class="overflow-x-auto rounded-lg border border-slate-700">
      <table class="min-w-full text-xs">
        <thead class="bg-slate-800/70 text-gray-300">
          <tr>
            <th class="px-2 py-2 text-left w-36">Label</th>
            <th v-for="(dataset, datasetIndex) in localDatasets" :key="`h-${datasetIndex}`" class="px-2 py-2 text-left min-w-32">
              <div class="flex items-center gap-2">
                <input
                  :value="dataset.label"
                  class="input-base px-2 py-1 text-xs w-full"
                  @input="updateDatasetLabel(datasetIndex, $event.target.value)"
                />
                <button
                  class="text-red-400 hover:text-red-300"
                  title="Remove series"
                  @click="removeDataset(datasetIndex)"
                >x</button>
              </div>
            </th>
            <th class="px-2 py-2 w-10"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(label, rowIndex) in localLabels" :key="`r-${rowIndex}`" class="border-t border-slate-800 bg-slate-900/40">
            <td class="px-2 py-2">
              <input
                :value="label"
                class="input-base px-2 py-1 text-xs w-full"
                @input="updateLabel(rowIndex, $event.target.value)"
              />
            </td>
            <td v-for="(dataset, datasetIndex) in localDatasets" :key="`c-${rowIndex}-${datasetIndex}`" class="px-2 py-2">
              <input
                :value="dataset.data[rowIndex]"
                type="number"
                class="input-base px-2 py-1 text-xs w-full"
                @input="updateValue(datasetIndex, rowIndex, $event.target.value)"
              />
            </td>
            <td class="px-2 py-2 text-right">
              <button class="text-red-400 hover:text-red-300" title="Delete row" @click="removeRow(rowIndex)">x</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  labels: {
    type: Array,
    default: () => [],
  },
  datasets: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:labels', 'update:datasets'])

const localLabels = computed(() => props.labels || [])
const localDatasets = computed(() => props.datasets || [])

const cloneDatasets = () => (props.datasets || []).map((dataset) => ({
  ...dataset,
  data: Array.isArray(dataset.data) ? [...dataset.data] : [],
}))

const addRow = () => {
  const labels = [...localLabels.value, `Label ${localLabels.value.length + 1}`]
  const datasets = cloneDatasets().map((dataset) => ({
    ...dataset,
    data: [...dataset.data, 0],
  }))
  emit('update:labels', labels)
  emit('update:datasets', datasets)
}

const removeRow = (rowIndex) => {
  if (localLabels.value.length <= 1) return
  const labels = localLabels.value.filter((_, i) => i !== rowIndex)
  const datasets = cloneDatasets().map((dataset) => ({
    ...dataset,
    data: dataset.data.filter((_, i) => i !== rowIndex),
  }))
  emit('update:labels', labels)
  emit('update:datasets', datasets)
}

const addDataset = () => {
  const nextIndex = localDatasets.value.length + 1
  const datasets = [
    ...cloneDatasets(),
    {
      label: `Series ${nextIndex}`,
      data: localLabels.value.map(() => 0),
      backgroundColor: '#3b82f6',
      borderColor: '#3b82f6',
      borderWidth: 2,
      fill: false,
      tension: 0.3,
    },
  ]
  emit('update:datasets', datasets)
}

const removeDataset = (datasetIndex) => {
  if (localDatasets.value.length <= 1) return
  emit('update:datasets', localDatasets.value.filter((_, i) => i !== datasetIndex))
}

const updateDatasetLabel = (datasetIndex, value) => {
  const datasets = cloneDatasets()
  datasets[datasetIndex].label = value
  emit('update:datasets', datasets)
}

const updateLabel = (rowIndex, value) => {
  const labels = [...localLabels.value]
  labels[rowIndex] = value
  emit('update:labels', labels)
}

const updateValue = (datasetIndex, rowIndex, value) => {
  const datasets = cloneDatasets()
  datasets[datasetIndex].data[rowIndex] = value === '' ? 0 : Number(value)
  emit('update:datasets', datasets)
}
</script>
