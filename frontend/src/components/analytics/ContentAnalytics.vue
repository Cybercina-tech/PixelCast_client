<template>
  <div class="space-y-6">
    <!-- Download Statistics -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-6">
      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Total Downloads</p>
          <p class="text-2xl sm:text-3xl font-bold text-primary tabular-nums">
            {{ analyticsStore.contentStats?.download_statistics?.total_downloads || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Successful</p>
          <p class="text-2xl sm:text-3xl font-bold text-success tabular-nums">
            {{ analyticsStore.contentStats?.download_statistics?.successful || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Failed</p>
          <p class="text-2xl sm:text-3xl font-bold text-error tabular-nums">
            {{ analyticsStore.contentStats?.download_statistics?.failed || 0 }}
          </p>
        </div>
      </Card>

      <Card>
        <div class="text-center">
          <p class="text-sm text-muted mb-2">Error Rate</p>
          <p class="text-2xl sm:text-3xl font-bold text-error tabular-nums">
            {{ analyticsStore.contentStats?.download_statistics?.error_rate?.toFixed(1) || 0 }}%
          </p>
        </div>
      </Card>
    </div>

    <!-- Type Distribution -->
    <Card title="Content Type Distribution">
      <div v-if="analyticsStore.contentStats?.type_distribution?.length > 0" class="space-y-4">
        <div
          v-for="type in analyticsStore.contentStats.type_distribution"
          :key="type.type"
          class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg min-w-0"
        >
          <div class="flex flex-wrap items-baseline gap-x-3 gap-y-1 min-w-0">
            <span class="font-medium text-primary break-words">{{ type.type }}</span>
            <span class="text-sm text-muted">({{ type.count }} items)</span>
          </div>
          <div class="flex items-center gap-2 w-full sm:w-auto sm:min-w-[11rem] shrink-0">
            <div class="flex-1 sm:w-32 min-w-0 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div
                class="bg-primary-color h-2 rounded-full max-w-full"
                :style="{ width: `${type.percentage}%` }"
              ></div>
            </div>
            <span class="text-sm font-medium text-primary w-12 shrink-0 text-right tabular-nums">
              {{ type.percentage.toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>
      <div v-else class="text-center text-muted py-8">
        No content type distribution available
      </div>
    </Card>

    <!-- Downloads by Type -->
    <Card title="Downloads by Content Type">
      <div v-if="analyticsStore.contentStats?.downloads_by_type?.length > 0" class="table-container">
        <table class="table-base">
          <thead class="table-thead">
            <tr>
              <th class="table-th">Type</th>
              <th class="table-th">Total</th>
              <th class="table-th">Successful</th>
              <th class="table-th">Failed</th>
            </tr>
          </thead>
          <tbody class="table-tbody">
            <tr v-for="stat in analyticsStore.contentStats.downloads_by_type" :key="stat.type" class="table-tr">
              <td class="table-td font-medium">
                {{ stat.type }}
              </td>
              <td class="table-td text-number">{{ stat.total }}</td>
              <td class="table-td text-success">{{ stat.successful }}</td>
              <td class="table-td text-error">{{ stat.failed }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-center text-muted py-8">
        No download statistics by type available
      </div>
    </Card>
  </div>
</template>

<script setup>
import { useAnalyticsStore } from '@/stores/analytics'
import Card from '@/components/common/Card.vue'

const analyticsStore = useAnalyticsStore()
</script>
