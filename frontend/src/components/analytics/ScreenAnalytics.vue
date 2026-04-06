<template>
  <div class="space-y-6">
    <!-- Screen Statistics Summary -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 min-w-0">
      <Card title="Screen Status Overview">
        <div v-if="analyticsStore.screenStats" class="space-y-4">
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Online Screens</span>
            <span class="text-xl sm:text-2xl font-bold text-success tabular-nums shrink-0">
              {{ analyticsStore.screenStats.status_breakdown?.online || 0 }}
            </span>
          </div>
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Offline Screens</span>
            <span class="text-xl sm:text-2xl font-bold text-error tabular-nums shrink-0">
              {{ analyticsStore.screenStats.status_breakdown?.offline || 0 }}
            </span>
          </div>
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Total Screens</span>
            <span class="text-xl sm:text-2xl font-bold text-primary tabular-nums shrink-0">
              {{ analyticsStore.screenStats.status_breakdown?.total || 0 }}
            </span>
          </div>
        </div>
        <div v-else class="text-center text-muted py-8">
          No screen statistics available
        </div>
      </Card>

      <Card title="Health Metrics">
        <div v-if="analyticsStore.screenStats?.health_metrics" class="space-y-4">
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Avg CPU Usage</span>
            <span class="text-base sm:text-lg font-semibold text-primary tabular-nums shrink-0">
              {{ formatPercent(analyticsStore.screenStats.health_metrics.avg_cpu_usage) }}%
            </span>
          </div>
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Avg Memory Usage</span>
            <span class="text-base sm:text-lg font-semibold text-primary tabular-nums shrink-0">
              {{ formatPercent(analyticsStore.screenStats.health_metrics.avg_memory_usage) }}%
            </span>
          </div>
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Avg Latency</span>
            <span class="text-base sm:text-lg font-semibold text-primary tabular-nums shrink-0">
              {{ formatLatency(analyticsStore.screenStats.health_metrics.avg_latency_ms) }} ms
            </span>
          </div>
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Max CPU Usage</span>
            <span class="text-base sm:text-lg font-semibold text-error tabular-nums shrink-0">
              {{ formatPercent(analyticsStore.screenStats.health_metrics.max_cpu_usage) }}%
            </span>
          </div>
          <div class="flex items-center justify-between gap-3 min-w-0">
            <span class="text-muted shrink min-w-0">Max Memory Usage</span>
            <span class="text-base sm:text-lg font-semibold text-error tabular-nums shrink-0">
              {{ formatPercent(analyticsStore.screenStats.health_metrics.max_memory_usage) }}%
            </span>
          </div>
        </div>
        <div v-else class="text-center text-muted py-8">
          No health metrics available
        </div>
      </Card>
    </div>

    <!-- Screen List with Details Link -->
    <Card title="Screens">
      <div class="overflow-x-auto">
        <Table
          :columns="screenTableHeaders"
          :data="screenTableData"
        >
          <template #cell-is_online="{ value }">
            <span
              :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                value ? 'badge-success' : 'badge-error'
              ]"
            >
              {{ value ? 'Online' : 'Offline' }}
            </span>
          </template>
          <template #actions="{ row }">
            <button
              @click="viewScreenDetails(row.id)"
              class="action-btn-view text-sm font-medium"
            >
              View Details
            </button>
          </template>
        </Table>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalyticsStore } from '@/stores/analytics'
import { useScreensStore } from '@/stores/screens'
import Card from '@/components/common/Card.vue'
import Table from '@/components/common/Table.vue'

const router = useRouter()
const analyticsStore = useAnalyticsStore()
const screensStore = useScreensStore()

const screenTableHeaders = [
  { key: 'name', label: 'Name' },
  { key: 'device_id', label: 'Device ID' },
  { key: 'location', label: 'Location' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' },
]

const screenTableData = computed(() => {
  return screensStore.screens.map(screen => ({
    id: screen.id,
    name: screen.name,
    device_id: screen.device_id,
    location: screen.location || 'N/A',
    is_online: screen.is_online,
  }))
})

const normalizeMetricNumber = (value) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

const formatPercent = (value) => normalizeMetricNumber(value).toFixed(1)
const formatLatency = (value) => normalizeMetricNumber(value).toFixed(1)

const viewScreenDetails = async (screenId) => {
  try {
    await analyticsStore.fetchScreenDetail(screenId)
    // Navigate to screen details page (not analytics-specific route)
    router.push(`/screens/${screenId}`)
  } catch (error) {
    console.error('Failed to fetch screen details:', error)
  }
}
</script>
