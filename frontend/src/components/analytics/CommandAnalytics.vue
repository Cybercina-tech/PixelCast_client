<template>
  <div class="space-y-6">
    <!-- Overall Statistics -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-6">
      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Total Commands</p>
          <p class="text-2xl sm:text-3xl font-bold text-primary tabular-nums">
            {{ analyticsStore.commandStats?.overall?.total || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Success Rate</p>
          <p class="text-2xl sm:text-3xl font-bold text-success tabular-nums">
            {{ analyticsStore.commandStats?.overall?.success_rate?.toFixed(1) || 0 }}%
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Pending</p>
          <p class="text-2xl sm:text-3xl font-bold text-warning tabular-nums">
            {{ analyticsStore.commandStats?.overall?.pending || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Failed</p>
          <p class="text-2xl sm:text-3xl font-bold text-error tabular-nums">
            {{ analyticsStore.commandStats?.overall?.failed || 0 }}
          </p>
        </div>
      </Card>
    </div>

    <!-- Statistics by Type -->
    <Card title="Commands by Type">
      <div v-if="analyticsStore.commandStats?.by_type?.length > 0" class="table-container">
        <table class="table-base">
          <thead class="table-thead">
            <tr>
              <th class="table-th">Type</th>
              <th class="table-th">Total</th>
              <th class="table-th">Pending</th>
              <th class="table-th">Done</th>
              <th class="table-th">Failed</th>
            </tr>
          </thead>
          <tbody class="table-tbody">
            <tr v-for="stat in analyticsStore.commandStats.by_type" :key="stat.type" class="table-tr">
              <td class="table-td font-medium">
                {{ stat.type }}
              </td>
              <td class="table-td text-number">{{ stat.total }}</td>
              <td class="table-td text-warning">{{ stat.pending }}</td>
              <td class="table-td text-success">{{ stat.done }}</td>
              <td class="table-td text-error">{{ stat.failed }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-center text-muted py-8">
        No command statistics available
      </div>
    </Card>

    <!-- Time Series Chart -->
    <Card title="Command Activity Over Time" v-if="analyticsStore.commandStats?.time_series?.length > 0">
      <Chart
        type="line"
        :data="timeSeriesChartData"
        :options="chartOptions"
      />
    </Card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import Card from '@/components/common/Card.vue'
import Chart from '@/components/common/Chart.vue'

const analyticsStore = useAnalyticsStore()

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
    },
  },
}

const timeSeriesChartData = computed(() => {
  const timeSeries = analyticsStore.commandStats?.time_series || []
  return {
    labels: timeSeries.map(item => {
      if (!item.period) return ''
      const date = new Date(item.period)
      return date.toLocaleDateString()
    }),
    datasets: [
      {
        label: 'Total',
        data: timeSeries.map(item => item.total || 0),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
      },
      {
        label: 'Done',
        data: timeSeries.map(item => item.done || 0),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
      },
      {
        label: 'Failed',
        data: timeSeries.map(item => item.failed || 0),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
      },
    ],
  }
})
</script>
