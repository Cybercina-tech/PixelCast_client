<template>
  <component :is="embedded ? 'div' : AppLayout">
    <div class="space-y-6">
      <!-- Header -->
      <div v-if="!embedded" class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-primary">Audit Logs</h1>
          <p class="text-sm text-secondary mt-1">Comprehensive audit trail of all system actions</p>
        </div>
        <button
          @click="loadSummary"
          class="btn-primary px-4 py-2 rounded-lg"
        >
          View Summary
        </button>
      </div>
      <div v-else class="flex justify-end">
        <button
          @click="loadSummary"
          class="btn-primary px-4 py-2 rounded-lg"
        >
          View Summary
        </button>
      </div>

      <!-- Filters -->
      <Card>
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <label class="label-base block text-sm mb-1">Action Type</label>
            <select
              v-model="filters.action_type"
              @change="applyFilters"
              class="select-base w-full px-3 py-2 rounded-lg"
            >
              <option value="">All Actions</option>
              <option value="create">Create</option>
              <option value="update">Update</option>
              <option value="delete">Delete</option>
              <option value="login">Login</option>
              <option value="logout">Logout</option>
              <option value="backup">Backup</option>
              <option value="read">Read</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Resource Type</label>
            <input
              v-model="filters.resource_type"
              @input="applyFilters"
              type="text"
              placeholder="e.g., Screen, Template"
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Severity</label>
            <select
              v-model="filters.severity"
              @change="applyFilters"
              class="select-base w-full px-3 py-2 rounded-lg"
            >
              <option value="">All</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Status</label>
            <select
              v-model="filters.success"
              @change="applyFilters"
              class="select-base w-full px-3 py-2 rounded-lg"
            >
              <option :value="null">All</option>
              <option :value="true">Success</option>
              <option :value="false">Failed</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Start Date</label>
            <input
              v-model="filters.start_date"
              @change="applyFilters"
              type="date"
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">End Date</label>
            <input
              v-model="filters.end_date"
              @change="applyFilters"
              type="date"
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Search</label>
            <input
              v-model="filters.search"
              @input="applyFilters"
              type="text"
              placeholder="Search description, resource, user..."
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div class="flex items-end">
            <button
              @click="clearFilters"
              class="w-full px-4 py-2 bg-slate-200 dark:bg-slate-700 text-primary rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </Card>

      <!-- Summary Modal -->
      <Modal :show="showSummaryModal" title="Audit Log Summary" @close="showSummaryModal = false">
        <div v-if="coreStore.auditLogSummary" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div class="text-sm text-muted">Total Count</div>
              <div class="text-2xl font-bold text-primary">{{ coreStore.auditLogSummary.total_count || 0 }}</div>
            </div>
            <div class="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div class="text-sm text-muted">Success Count</div>
              <div class="text-2xl font-bold text-success">{{ coreStore.auditLogSummary.success_count || 0 }}</div>
            </div>
            <div class="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <div class="text-sm text-muted">Failed Count</div>
              <div class="text-2xl font-bold text-error">{{ coreStore.auditLogSummary.failed_count || 0 }}</div>
            </div>
            <div class="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
              <div class="text-sm text-muted">Success Rate</div>
              <div class="text-2xl font-bold text-primary">
                {{ (coreStore.auditLogSummary.success_rate || 0).toFixed(1) }}%
              </div>
            </div>
          </div>
          <div v-if="coreStore.auditLogSummary.action_type_counts">
            <h3 class="font-semibold mb-2 text-primary">Actions by Type</h3>
            <div class="space-y-2">
              <div
                v-for="(count, action) in coreStore.auditLogSummary.action_type_counts"
                :key="action"
                class="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-800 rounded"
              >
                <span class="capitalize text-primary">{{ action }}</span>
                <span class="font-semibold text-primary">{{ count }}</span>
              </div>
            </div>
          </div>
          <div v-if="coreStore.auditLogSummary.severity_counts">
            <h3 class="font-semibold mb-2 text-primary">Actions by Severity</h3>
            <div class="space-y-2">
              <div
                v-for="(count, severity) in coreStore.auditLogSummary.severity_counts"
                :key="severity"
                class="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-800 rounded"
              >
                <span class="capitalize text-primary">{{ severity }}</span>
                <span class="font-semibold text-primary">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-muted">Loading summary...</div>
      </Modal>

      <!-- Audit Logs Table -->
      <Card>
        <div v-if="coreStore.loading" class="text-center py-8">Loading audit logs...</div>
        <div v-else-if="coreStore.error" class="text-center py-8 text-red-600">
          {{ coreStore.error }}
        </div>
        <div v-else-if="coreStore.auditLogs.length === 0" class="text-center py-8 text-gray-500">
          No audit logs found
        </div>
        <div v-else class="table-container">
          <table class="table-base">
            <thead class="table-thead">
              <tr>
                <th class="table-th">Timestamp</th>
                <th class="table-th">User</th>
                <th class="table-th">Action</th>
                <th class="table-th">Resource</th>
                <th class="table-th">Severity</th>
                <th class="table-th">Status</th>
                <th class="table-th">Description</th>
                <th class="table-th text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="table-tbody">
              <tr v-for="log in coreStore.auditLogs" :key="log.id" class="table-tr">
                <td class="table-td text-number">
                  {{ formatDate(log.timestamp) }}
                </td>
                <td class="table-td">
                  <div class="font-medium text-primary">{{ log.username || 'N/A' }}</div>
                  <div class="text-meta">{{ log.user_role || '' }}</div>
                </td>
                <td class="table-td">
                  <span class="badge-primary px-2 py-1 rounded text-xs capitalize">
                    {{ log.action_type || 'N/A' }}
                  </span>
                </td>
                <td class="table-td">
                  <div class="font-medium text-primary">{{ log.resource_type || 'N/A' }}</div>
                  <div class="text-meta">{{ log.resource_name || '' }}</div>
                </td>
                <td class="table-td">
                  <span
                    :class="getSeverityClass(log.severity)"
                    class="px-2 py-1 rounded text-xs capitalize"
                  >
                    {{ log.severity || 'low' }}
                  </span>
                </td>
                <td class="table-td">
                  <span
                    :class="log.success ? 'badge-success' : 'badge-error'"
                    class="px-2 py-1 rounded text-xs font-medium"
                  >
                    {{ log.success ? 'Success' : 'Failed' }}
                  </span>
                </td>
                <td class="table-td text-primary max-w-md truncate">
                  {{ log.description || 'N/A' }}
                </td>
                <td class="table-td text-right">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      @click="viewLog(log)"
                      class="action-btn-view"
                      title="View"
                    >
                      <EyeIcon class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Log Detail Modal -->
      <Modal :show="showDetailModal" title="Audit Log Details" @close="showDetailModal = false">
        <div v-if="selectedLog" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-base block text-sm">Timestamp</label>
              <div class="mt-1 text-sm text-primary">{{ formatDate(selectedLog.timestamp) }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">User</label>
              <div class="mt-1 text-sm text-primary">{{ selectedLog.username }} ({{ selectedLog.user_role }})</div>
            </div>
            <div>
              <label class="label-base block text-sm">Action Type</label>
              <div class="mt-1">
                <span class="badge-primary px-2 py-1 rounded text-xs capitalize">
                  {{ selectedLog.action_type }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Severity</label>
              <div class="mt-1">
                <span :class="getSeverityClass(selectedLog.severity)" class="px-2 py-1 rounded text-xs capitalize">
                  {{ selectedLog.severity }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Resource Type</label>
              <div class="mt-1 text-sm text-primary">{{ selectedLog.resource_type || 'N/A' }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">Resource Name</label>
              <div class="mt-1 text-sm text-primary">{{ selectedLog.resource_name || 'N/A' }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">IP Address</label>
              <div class="mt-1 text-sm text-primary">{{ selectedLog.ip_address || 'N/A' }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">Status</label>
              <div class="mt-1">
                <span
                  :class="selectedLog.success ? 'badge-success' : 'badge-error'"
                  class="px-2 py-1 rounded text-xs font-medium"
                >
                  {{ selectedLog.success ? 'Success' : 'Failed' }}
                </span>
              </div>
            </div>
          </div>
          <div>
            <label class="label-base block text-sm">Description</label>
            <div class="mt-1 text-sm text-primary">{{ selectedLog.description || 'N/A' }}</div>
          </div>
          <div v-if="selectedLog.changes">
            <label class="label-base block text-sm">Changes</label>
            <pre class="mt-1 p-3 bg-slate-50 dark:bg-slate-800 rounded text-xs text-primary overflow-auto">{{ JSON.stringify(selectedLog.changes, null, 2) }}</pre>
          </div>
          <div v-if="selectedLog.metadata">
            <label class="label-base block text-sm">Metadata</label>
            <pre class="mt-1 p-3 bg-slate-50 dark:bg-slate-800 rounded text-xs text-primary overflow-auto">{{ JSON.stringify(selectedLog.metadata, null, 2) }}</pre>
          </div>
          <div v-if="selectedLog.error_message">
            <label class="label-base block text-sm">Error Message</label>
            <div class="mt-1 p-3 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-800 dark:text-red-300 break-words">{{ selectedLog.error_message }}</div>
          </div>
        </div>
      </Modal>
    </div>
  </component>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { EyeIcon } from '@heroicons/vue/24/outline'
import { useCoreStore } from '@/stores/core'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'

defineProps({
  embedded: { type: Boolean, default: false },
})

const coreStore = useCoreStore()

const filters = ref({
  action_type: '',
  resource_type: '',
  severity: '',
  success: null,
  start_date: '',
  end_date: '',
  search: '',
})

const showSummaryModal = ref(false)
const showDetailModal = ref(false)
const selectedLog = ref(null)

const applyFilters = () => {
  coreStore.setAuditLogFilters(filters.value)
  coreStore.fetchAuditLogs()
}

const clearFilters = () => {
  filters.value = {
    action_type: '',
    resource_type: '',
    severity: '',
    success: null,
    start_date: '',
    end_date: '',
    search: '',
  }
  coreStore.clearAuditLogFilters()
  coreStore.fetchAuditLogs()
}

const loadSummary = async () => {
  showSummaryModal.value = true
  await coreStore.fetchAuditLogSummary()
}

const viewLog = async (log) => {
  selectedLog.value = log
  showDetailModal.value = true
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const getSeverityClass = (severity) => {
  const classes = {
    low: 'badge-info',
    medium: 'badge-warning',
    high: 'badge-error',
    critical: 'badge-error',
  }
  return classes[severity?.toLowerCase()] || 'badge-info'
}

onMounted(() => {
  coreStore.fetchAuditLogs()
})

// Watch for filter changes
watch(filters, () => {
  // Debounce search input
  if (filters.value.search !== undefined) {
    clearTimeout(window.filterTimeout)
    window.filterTimeout = setTimeout(() => {
      applyFilters()
    }, 500)
  }
}, { deep: true })
</script>
