<template>
  <AppLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-primary">Logs & Reports</h1>
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <input
              v-model="dateRange.start"
              type="date"
              class="input-base px-3 py-2 rounded-lg text-sm"
            />
            <span class="text-muted">to</span>
            <input
              v-model="dateRange.end"
              type="date"
              class="input-base px-3 py-2 rounded-lg text-sm"
            />
            <button
              @click="applyFilters"
              :disabled="logsStore.loading"
              class="btn-primary px-4 py-2 rounded-lg disabled:opacity-50 text-sm"
            >
              Apply
            </button>
          </div>
          <button
            @click="exportLogs"
            :disabled="logsStore.loading"
            class="btn-primary px-4 py-2 rounded-lg disabled:opacity-50 text-sm"
          >
            Export
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-border-color">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-primary-color text-primary-color'
                : 'border-transparent text-muted hover:text-secondary hover:border-border-color'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Loading State -->
      <div v-if="logsStore.loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-color"></div>
        <p class="mt-2 text-muted">Loading logs...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="logsStore.error" class="badge-error border border-red-200 dark:border-red-800 px-4 py-3 rounded-lg">
        {{ logsStore.error }}
      </div>

      <!-- Screen Status Logs -->
      <Card v-else-if="activeTab === 'screen-status'">
        <div class="overflow-x-auto">
          <table class="table-base">
            <thead class="table-thead">
              <tr>
                <th class="table-th">Screen</th>
                <th class="table-th">Status</th>
                <th class="table-th">Recorded At</th>
              </tr>
            </thead>
            <tbody class="table-tbody">
              <tr v-for="log in logsStore.screenStatusLogs" :key="log.id" class="table-tr">
                <td class="table-td text-primary">{{ log.screen?.name || log.screen_id || 'N/A' }}</td>
                <td class="table-td">
                  <span
                    :class="log.status === 'online' ? 'badge-success' : 'badge-error'"
                    class="px-2 py-1 rounded text-xs"
                  >
                    {{ log.status || 'N/A' }}
                  </span>
                </td>
                <td class="table-td text-number">{{ formatDate(log.recorded_at) }}</td>
              </tr>
              <tr v-if="logsStore.screenStatusLogs.length === 0">
                <td colspan="3" class="table-td text-center text-muted">No screen status logs found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Content Download Logs -->
      <Card v-else-if="activeTab === 'content-download'">
        <div class="overflow-x-auto">
          <table class="table-base">
            <thead class="table-thead">
              <tr>
                <th class="table-th">Content</th>
                <th class="table-th">Screen</th>
                <th class="table-th">Status</th>
                <th class="table-th">Created At</th>
              </tr>
            </thead>
            <tbody class="table-tbody">
              <tr v-for="log in logsStore.contentDownloadLogs" :key="log.id" class="table-tr">
                <td class="table-td text-primary">{{ log.content?.name || log.content_id || 'N/A' }}</td>
                <td class="table-td text-primary">{{ log.screen?.name || log.screen_id || 'N/A' }}</td>
                <td class="table-td">
                  <span
                    :class="log.status === 'success' ? 'badge-success' : 'badge-error'"
                    class="px-2 py-1 rounded text-xs"
                  >
                    {{ log.status || 'N/A' }}
                  </span>
                </td>
                <td class="table-td text-number">{{ formatDate(log.created_at) }}</td>
              </tr>
              <tr v-if="logsStore.contentDownloadLogs.length === 0">
                <td colspan="4" class="table-td text-center text-muted">No content download logs found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Command Execution Logs -->
      <Card v-else-if="activeTab === 'command-execution'">
        <div class="overflow-x-auto">
          <table class="table-base">
            <thead class="table-thead">
              <tr>
                <th class="table-th">Command</th>
                <th class="table-th">Screen</th>
                <th class="table-th">Status</th>
                <th class="table-th">Started</th>
                <th class="table-th">Finished</th>
              </tr>
            </thead>
            <tbody class="table-tbody">
              <tr v-for="log in logsStore.commandExecutionLogs" :key="log.id" class="table-tr">
                <td class="table-td text-primary">{{ log.command?.name || log.command_id || 'N/A' }}</td>
                <td class="table-td text-primary">{{ log.screen?.name || log.screen_id || 'N/A' }}</td>
                <td class="table-td">
                  <span
                    :class="getCommandStatusClass(log.status)"
                    class="px-2 py-1 rounded text-xs"
                  >
                    {{ log.status || 'N/A' }}
                  </span>
                </td>
                <td class="table-td text-number">{{ formatDate(log.started_at) }}</td>
                <td class="table-td text-number">{{ formatDate(log.finished_at) }}</td>
              </tr>
              <tr v-if="logsStore.commandExecutionLogs.length === 0">
                <td colspan="5" class="table-td text-center text-muted">No command execution logs found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useLogsStore } from '@/stores/logs.js'
import { useNotificationStore } from '@/stores/notification.js'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'

const logsStore = useLogsStore()
const notifyStore = useNotificationStore()

const activeTab = ref('screen-status')
const dateRange = ref({
  start: null,
  end: null,
})

const tabs = [
  { id: 'screen-status', label: 'Screen Status' },
  { id: 'content-download', label: 'Content Download' },
  { id: 'command-execution', label: 'Command Execution' },
]

const applyFilters = async () => {
  const params = {}
  if (dateRange.value.start) params.start_date = dateRange.value.start
  if (dateRange.value.end) params.end_date = dateRange.value.end

  logsStore.setFilters(params)

  try {
    if (activeTab.value === 'screen-status') {
      await logsStore.fetchScreenStatusLogs(params)
    } else if (activeTab.value === 'content-download') {
      await logsStore.fetchContentDownloadLogs(params)
    } else if (activeTab.value === 'command-execution') {
      await logsStore.fetchCommandExecutionLogs(params)
    }
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

const loadTabData = async () => {
  const params = {}
  if (dateRange.value.start) params.start_date = dateRange.value.start
  if (dateRange.value.end) params.end_date = dateRange.value.end

  try {
    if (activeTab.value === 'screen-status') {
      await logsStore.fetchScreenStatusLogs(params)
    } else if (activeTab.value === 'content-download') {
      await logsStore.fetchContentDownloadLogs(params)
    } else if (activeTab.value === 'command-execution') {
      await logsStore.fetchCommandExecutionLogs(params)
    }
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

const exportLogs = async () => {
  try {
    const format = 'csv'
    const typeMap = {
      'screen-status': 'screen-status',
      'content-download': 'content-download',
      'command-execution': 'command-execution',
    }
    const type = typeMap[activeTab.value]
    const params = {}
    if (dateRange.value.start) params.start_date = dateRange.value.start
    if (dateRange.value.end) params.end_date = dateRange.value.end

    const data = await logsStore.exportLogs(type, format, params)
    const blob = new Blob([data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${activeTab.value}-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    notifyStore.success('Logs exported successfully')
  } catch (error) {
    notifyStore.error(error?.message || 'Failed to export logs')
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const getCommandStatusClass = (status) => {
  const classes = {
    done: 'badge-success',
    success: 'badge-success',
    failed: 'badge-error',
    pending: 'badge-warning',
    running: 'badge-info',
  }
  return classes[status?.toLowerCase()] || 'badge-info'
}

onMounted(async () => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  dateRange.value.end = end.toISOString().split('T')[0]
  dateRange.value.start = start.toISOString().split('T')[0]
  await loadTabData()
})

watch(activeTab, () => {
  loadTabData()
})
</script>
