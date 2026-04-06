<template>
  <AppLayout>
    <div class="space-y-6 min-w-0 max-w-full">
      <!-- Header -->
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <h1 class="text-xl sm:text-2xl font-bold text-primary shrink-0">
          Analytics Dashboard
        </h1>
        <!-- Date Range Filter -->
        <div
          class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center w-full lg:w-auto lg:max-w-none min-w-0"
        >
          <div class="flex flex-col sm:flex-row sm:items-center gap-2 min-w-0 flex-1 sm:flex-initial">
            <input
              v-model="dateRange.start"
              type="date"
              class="input-base px-3 py-2 rounded-lg text-sm w-full min-w-0 sm:w-auto sm:min-w-[10.5rem]"
            />
            <span class="text-muted shrink-0 hidden sm:inline">to</span>
            <input
              v-model="dateRange.end"
              type="date"
              class="input-base px-3 py-2 rounded-lg text-sm w-full min-w-0 sm:w-auto sm:min-w-[10.5rem]"
            />
          </div>
          <button
            type="button"
            @click="applyFilters"
            :disabled="analyticsStore.loading"
            class="btn-primary px-4 py-2 rounded-lg disabled:opacity-50 text-sm w-full sm:w-auto shrink-0"
          >
            Apply
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="analyticsStore.loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-color"></div>
        <p class="mt-2 text-muted">Loading analytics...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="analyticsStore.error" class="badge-error border border-red-200 dark:border-red-800 px-4 py-3 rounded-lg">
        {{ analyticsStore.error }}
      </div>

      <!-- Analytics Content -->
      <div v-else class="space-y-6">
        <!-- Overview Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-6">
          <Card>
            <div class="flex items-center justify-between gap-3 min-w-0">
              <div class="min-w-0">
                <p class="text-sm text-muted">Total Screens</p>
                <p class="text-2xl sm:text-3xl font-bold text-primary tabular-nums">
                  {{ analyticsStore.screenStats?.total_screens || 0 }}
                </p>
              </div>
              <TvIcon class="w-10 h-10 sm:w-12 sm:h-12 shrink-0 text-primary-color" />
            </div>
          </Card>

          <Card>
            <div class="flex items-center justify-between gap-3 min-w-0">
              <div class="min-w-0">
                <p class="text-sm text-muted">Health Score</p>
                <p class="text-2xl sm:text-3xl font-bold text-success tabular-nums">
                  {{ analyticsStore.screenStats?.health_score?.toFixed(1) || 0 }}%
                </p>
              </div>
              <ChartBarIcon class="w-10 h-10 sm:w-12 sm:h-12 shrink-0 text-success" />
            </div>
          </Card>

          <Card>
            <div class="flex items-center justify-between gap-3 min-w-0">
              <div class="min-w-0">
                <p class="text-sm text-muted">Commands Success Rate</p>
                <p class="text-2xl sm:text-3xl font-bold text-info tabular-nums">
                  {{ analyticsStore.commandStats?.overall?.success_rate?.toFixed(1) || 0 }}%
                </p>
              </div>
              <CheckCircleIcon class="w-10 h-10 sm:w-12 sm:h-12 shrink-0 text-info" />
            </div>
          </Card>

          <Card>
            <div class="flex items-center justify-between gap-3 min-w-0">
              <div class="min-w-0">
                <p class="text-sm text-muted">Content Error Rate</p>
                <p class="text-2xl sm:text-3xl font-bold text-error tabular-nums">
                  {{ analyticsStore.contentStats?.download_statistics?.error_rate?.toFixed(1) || 0 }}%
                </p>
              </div>
              <ExclamationTriangleIcon class="w-10 h-10 sm:w-12 sm:h-12 shrink-0 text-error" />
            </div>
          </Card>
        </div>

        <!-- Tabs: horizontal scroll on narrow viewports -->
        <div class="border-b border-border-color -mx-4 px-4 sm:mx-0 sm:px-0">
          <nav
            class="-mb-px flex gap-1 sm:gap-6 overflow-x-auto pb-px touch-pan-x"
            aria-label="Analytics sections"
          >
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              @click="activeTab = tab.id"
              :class="[
                'shrink-0 whitespace-nowrap py-3 sm:py-4 px-2 sm:px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-primary-color text-primary-color'
                  : 'border-transparent text-muted hover:text-secondary hover:border-border-color',
              ]"
            >
              {{ tab.label }}
            </button>
          </nav>
        </div>

        <!-- Screen Analytics Tab -->
        <div v-show="activeTab === 'screens'">
          <ScreenAnalytics />
        </div>

        <!-- Command Analytics Tab -->
        <div v-show="activeTab === 'commands'">
          <CommandAnalytics />
        </div>

        <!-- Content Analytics Tab -->
        <div v-show="activeTab === 'content'">
          <ContentAnalytics />
        </div>

        <!-- Template Analytics Tab -->
        <div v-show="activeTab === 'templates'">
          <TemplateAnalytics />
        </div>

        <!-- Activity Trends Tab -->
        <div v-show="activeTab === 'activity'">
          <ActivityTrends />
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import ScreenAnalytics from '@/components/analytics/ScreenAnalytics.vue'
import CommandAnalytics from '@/components/analytics/CommandAnalytics.vue'
import ContentAnalytics from '@/components/analytics/ContentAnalytics.vue'
import TemplateAnalytics from '@/components/analytics/TemplateAnalytics.vue'
import ActivityTrends from '@/components/analytics/ActivityTrends.vue'
import {
  TvIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

const analyticsStore = useAnalyticsStore()

const activeTab = ref('screens')
const dateRange = ref({
  start: null,
  end: null,
})

const tabs = [
  { id: 'screens', label: 'Screens' },
  { id: 'commands', label: 'Commands' },
  { id: 'content', label: 'Content' },
  { id: 'templates', label: 'Templates' },
  { id: 'activity', label: 'Activity Trends' },
]

const applyFilters = async () => {
  const params = {}
  if (dateRange.value.start) {
    params.start_date = dateRange.value.start
  }
  if (dateRange.value.end) {
    params.end_date = dateRange.value.end
  }

  analyticsStore.setFilters(params)

  // Fetch all analytics data
  try {
    await Promise.all([
      analyticsStore.fetchScreenStatistics(params),
      analyticsStore.fetchCommandStatistics(params),
      analyticsStore.fetchContentStatistics(params),
      analyticsStore.fetchTemplateStatistics(params),
    ])
  } catch (error) {
    console.error('Failed to fetch analytics:', error)
  }
}

onMounted(async () => {
  // Set default date range (last 30 days)
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  
  dateRange.value.end = end.toISOString().split('T')[0]
  dateRange.value.start = start.toISOString().split('T')[0]

  await applyFilters()
  
  // Also fetch activity trends
  try {
    await analyticsStore.fetchActivityTrends()
  } catch (error) {
    console.error('Failed to fetch activity trends:', error)
  }
})
</script>
