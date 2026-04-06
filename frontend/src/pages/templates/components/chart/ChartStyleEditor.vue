<template>
  <div class="space-y-3">
    <h4 class="text-xs font-semibold uppercase text-gray-400">Chart Options</h4>

    <div class="grid grid-cols-2 gap-3">
      <label class="editor-switch-row editor-switch-row--compact">
        <span class="text-[11px] text-primary">Show Legend</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="legendDisplay"
            @change="updateLegendDisplay($event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
      <label class="text-[11px] text-gray-400">
        Legend Position
        <select class="select-base w-full px-2 py-1 mt-1 text-xs" :value="legendPosition" @change="updateLegendPosition($event.target.value)">
          <option value="top">Top</option>
          <option value="bottom">Bottom</option>
          <option value="left">Left</option>
          <option value="right">Right</option>
        </select>
      </label>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <label class="text-[11px] text-gray-400">
        Title
        <input class="input-base w-full px-2 py-1 mt-1 text-xs" :value="titleText" @input="updateTitle($event.target.value)" placeholder="Chart title" />
      </label>
      <label class="editor-switch-row editor-switch-row--compact mt-5">
        <span class="text-[11px] text-primary">Show Title</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="titleDisplay"
            @change="updateTitleDisplay($event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <label class="editor-switch-row editor-switch-row--compact">
        <span class="text-[11px] text-primary">X Grid</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="xGridDisplay"
            @change="updateXGrid($event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
      <label class="editor-switch-row editor-switch-row--compact">
        <span class="text-[11px] text-primary">Y Grid</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="yGridDisplay"
            @change="updateYGrid($event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:options'])

const legendDisplay = computed(() => props.options?.plugins?.legend?.display !== false)
const legendPosition = computed(() => props.options?.plugins?.legend?.position || 'top')
const titleText = computed(() => props.options?.plugins?.title?.text || '')
const titleDisplay = computed(() => props.options?.plugins?.title?.display === true)
const xGridDisplay = computed(() => props.options?.scales?.x?.grid?.display !== false)
const yGridDisplay = computed(() => props.options?.scales?.y?.grid?.display !== false)

const patchOptions = (fn) => {
  const next = JSON.parse(JSON.stringify(props.options || {}))
  fn(next)
  emit('update:options', next)
}

const updateLegendDisplay = (checked) => {
  patchOptions((o) => {
    if (!o.plugins) o.plugins = {}
    if (!o.plugins.legend) o.plugins.legend = {}
    o.plugins.legend.display = checked
  })
}

const updateLegendPosition = (position) => {
  patchOptions((o) => {
    if (!o.plugins) o.plugins = {}
    if (!o.plugins.legend) o.plugins.legend = {}
    o.plugins.legend.position = position
  })
}

const updateTitle = (text) => {
  patchOptions((o) => {
    if (!o.plugins) o.plugins = {}
    if (!o.plugins.title) o.plugins.title = {}
    o.plugins.title.text = text
  })
}

const updateTitleDisplay = (checked) => {
  patchOptions((o) => {
    if (!o.plugins) o.plugins = {}
    if (!o.plugins.title) o.plugins.title = {}
    o.plugins.title.display = checked
  })
}

const updateXGrid = (checked) => {
  patchOptions((o) => {
    if (!o.scales) o.scales = {}
    if (!o.scales.x) o.scales.x = {}
    if (!o.scales.x.grid) o.scales.x.grid = {}
    o.scales.x.grid.display = checked
  })
}

const updateYGrid = (checked) => {
  patchOptions((o) => {
    if (!o.scales) o.scales = {}
    if (!o.scales.y) o.scales.y = {}
    if (!o.scales.y.grid) o.scales.y.grid = {}
    o.scales.y.grid.display = checked
  })
}
</script>
