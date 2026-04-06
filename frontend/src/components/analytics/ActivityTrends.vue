<template>
  <div class="space-y-6">
    <!-- Period Selector -->
    <Card>
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4 min-w-0">
        <h3 class="text-lg font-semibold text-primary shrink-0">Activity Trends</h3>
        <div class="flex flex-wrap items-center gap-2 w-full sm:w-auto min-w-0">
          <select
            v-model="selectedPeriod"
            @change="updatePeriod"
            class="select-base px-3 py-2 rounded-lg text-sm flex-1 min-w-0 sm:flex-initial sm:min-w-[8rem]"
          >
            <option value="day">Daily</option>
            <option value="week">Weekly</option>
            <option value="month">Monthly</option>
          </select>
          <input
            v-model.number="days"
            @change="updateDays"
            type="number"
            min="1"
            max="365"
            class="input-base w-full sm:w-20 min-w-0 px-3 py-2 rounded-lg text-sm"
            placeholder="Days"
          />
        </div>
      </div>
    </Card>

    <!-- Activity Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card title="Screen Registrations">
        <Chart
          v-if="screenRegistrationsData"
          type="bar"
          :data="screenRegistrationsData"
          :options="chartOptions"
        />
        <div v-else class="text-center text-muted py-8">
          No registration data available
        </div>
      </Card>

      <Card title="Commands Created">
        <Chart
          v-if="commandsCreatedData"
          type="bar"
          :data="commandsCreatedData"
          :options="chartOptions"
        />
        <div v-else class="text-center text-muted py-8">
          No command data available
        </div>
      </Card>

      <Card title="Templates Created">
        <Chart
          v-if="templatesCreatedData"
          type="bar"
          :data="templatesCreatedData"
          :options="chartOptions"
        />
        <div v-else class="text-center text-muted py-8">
          No template data available
        </div>
      </Card>

      <Card title="Content Uploads">
        <Chart
          v-if="contentUploadsData"
          type="bar"
          :data="contentUploadsData"
          :options="chartOptions"
        />
        <div v-else class="text-center text-muted py-8">
          No content upload data available
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import Card from '@/components/common/Card.vue'
import Chart from '@/components/common/Chart.vue'

const analyticsStore = useAnalyticsStore()
const selectedPeriod = ref('day')
const days = ref(30)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
    },
  },
}

const formatChartData = (timeSeries) => {
  if (!timeSeries || timeSeries.length === 0) return null
  
  return {
    labels: timeSeries.map(item => {
      if (!item.period) return ''
      const date = new Date(item.period)
      return selectedPeriod.value === 'day'
        ? date.toLocaleDateString()
        : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }),
    datasets: [
      {
        label: 'Count',
        data: timeSeries.map(item => item.count || 0),
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
        borderColor: 'rgb(99, 102, 241)',
        borderWidth: 1,
      },
    ],
  }
}

const screenRegistrationsData = computed(() => {
  return formatChartData(analyticsStore.activityTrends?.screen_registrations)
})

const commandsCreatedData = computed(() => {
  return formatChartData(analyticsStore.activityTrends?.commands_created)
})

const templatesCreatedData = computed(() => {
  return formatChartData(analyticsStore.activityTrends?.templates_created)
})

const contentUploadsData = computed(() => {
  return formatChartData(analyticsStore.activityTrends?.content_uploads)
})

const updatePeriod = async () => {
  analyticsStore.setFilters({ period: selectedPeriod.value })
  await analyticsStore.fetchActivityTrends({ period: selectedPeriod.value, days: days.value })
}

const updateDays = async () => {
  if (days.value < 1) days.value = 1
  if (days.value > 365) days.value = 365
  analyticsStore.setFilters({ days: days.value })
  await analyticsStore.fetchActivityTrends({ period: selectedPeriod.value, days: days.value })
}

// Initialize
if (!analyticsStore.activityTrends) {
  analyticsStore.fetchActivityTrends({ period: selectedPeriod.value, days: days.value })
}
</script>
