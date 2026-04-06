<template>
  <div class="w-full h-52 min-h-[13rem] sm:h-64 sm:min-h-[16rem]">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Chart as ChartJS } from 'chart.js'

// Chart.js components are registered globally in plugins/chartjs.js
// No need to register here - they're already available

const props = defineProps({
  type: {
    type: String,
    default: 'line',
    validator: (value) => ['line', 'bar', 'doughnut', 'pie'].includes(value),
  },
  data: {
    type: Object,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({}),
  },
})

const chartCanvas = ref(null)
let chartInstance = null

const createChart = () => {
  if (!chartCanvas.value) return
  
  // Destroy existing chart if it exists
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  
  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return
  
  // Ensure data is valid
  const chartData = props.data || { labels: [], datasets: [] }
  
  chartInstance = new ChartJS(ctx, {
    type: props.type,
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...props.options,
    },
  })
}

onMounted(() => {
  createChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})

watch(
  () => props.data,
  (newData) => {
    if (chartInstance) {
      chartInstance.data = newData
      chartInstance.update()
    } else {
      createChart()
    }
  },
  { deep: true }
)

watch(
  () => props.type,
  (newType) => {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
      createChart()
    }
  }
)

watch(
  () => props.options,
  () => {
    if (chartInstance) {
      chartInstance.options = {
        responsive: true,
        maintainAspectRatio: false,
        ...props.options,
      }
      chartInstance.update()
    }
  },
  { deep: true }
)
</script>
