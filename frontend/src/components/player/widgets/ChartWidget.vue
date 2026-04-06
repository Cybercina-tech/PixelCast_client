<template>
  <div class="chart-widget">
    <canvas ref="canvasEl" />
    <div v-if="hasError" class="chart-error">Invalid chart configuration</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import { normalizeChartConfig, validateChartConfig } from '@/utils/chartConfig'

Chart.register(...registerables)

const props = defineProps({
  widget: {
    type: Object,
    required: true
  }
})

const canvasEl = ref(null)
const hasError = ref(false)
let chartInstance = null

const chartConfig = computed(() => {
  const content = props.widget?.contents?.[0]
  const rawConfig = content?.content_json?.chart || props.widget?.content_json?.chart
  const normalized = normalizeChartConfig(rawConfig)
  return {
    ...normalized,
    options: {
      ...normalized.options,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        ...(normalized.options?.plugins || {}),
        legend: {
          labels: { color: '#fff' },
          ...(normalized.options?.plugins?.legend || {}),
        },
      },
      scales: normalized.options?.scales
        ? Object.fromEntries(
            Object.entries(normalized.options.scales).map(([key, value]) => [
              key,
              {
                ticks: { color: '#cbd5e1' },
                grid: { color: 'rgba(255,255,255,0.08)' },
                ...value,
              },
            ]),
          )
        : {},
    },
  }
})

const destroyChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

const renderChart = () => {
  destroyChart()
  hasError.value = false
  if (!canvasEl.value) return

  try {
    const validation = validateChartConfig(chartConfig.value)
    if (!validation.isValid) {
      hasError.value = true
      return
    }
    chartInstance = new Chart(canvasEl.value, chartConfig.value)
  } catch {
    hasError.value = true
  }
}

onMounted(renderChart)
watch(chartConfig, renderChart, { deep: true })
onUnmounted(destroyChart)
</script>

<style scoped>
.chart-widget {
  position: relative;
  width: 100%;
  height: 100%;
  background: #0f172a;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
}
</style>
