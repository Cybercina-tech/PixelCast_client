<template>
  <component :is="embedded ? 'div' : AppLayout">
    <div class="space-y-6">
      <!-- Header -->
      <div v-if="!embedded" class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-primary">System Backups</h1>
          <p class="text-sm text-gray-600 mt-1">Manage database and media backups</p>
        </div>
        <div class="flex gap-3">
          <button
            @click="showTriggerModal = true"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Trigger Backup
          </button>
          <button
            @click="handleCleanup"
            class="px-4 py-2 bg-slate-600 dark:bg-slate-700 text-white rounded-lg hover:bg-slate-700 dark:hover:bg-slate-600 transition"
          >
            Cleanup Expired
          </button>
        </div>
      </div>
      <div v-else class="flex justify-end gap-3 flex-wrap">
        <button
          @click="showTriggerModal = true"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          Trigger Backup
        </button>
        <button
          @click="handleCleanup"
          class="px-4 py-2 bg-slate-600 dark:bg-slate-700 text-white rounded-lg hover:bg-slate-700 dark:hover:bg-slate-600 transition"
        >
          Cleanup Expired
        </button>
      </div>

      <!-- Filters -->
      <Card>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="label-base block text-sm mb-1">Backup Type</label>
            <select
              v-model="filters.backup_type"
              @change="applyFilters"
              class="select-base w-full px-3 py-2 rounded-lg"
            >
              <option value="">All Types</option>
              <option value="database">Database</option>
              <option value="media">Media</option>
              <option value="full">Full</option>
              <option value="incremental">Incremental</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Status</label>
            <select
              v-model="filters.status"
              @change="applyFilters"
              class="select-base w-full px-3 py-2 rounded-lg"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="expired">Expired</option>
            </select>
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

      <!-- Trigger Backup Modal -->
      <Modal :show="showTriggerModal" title="Trigger Backup" @close="showTriggerModal = false">
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">Backup Type *</label>
            <select v-model="backupForm.backup_type" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="">Select backup type</option>
              <option value="database">Database</option>
              <option value="media">Media</option>
              <option value="full">Full (Database + Media)</option>
            </select>
          </div>
          <div>
            <label class="flex items-center">
              <input
                v-model="backupForm.compression"
                type="checkbox"
                class="checkbox-base mr-2"
              />
              <span class="text-sm font-medium text-primary">Enable Compression</span>
            </label>
          </div>
          <div v-if="backupForm.backup_type === 'database'">
            <label class="flex items-center">
              <input
                v-model="backupForm.include_media"
                type="checkbox"
                class="checkbox-base mr-2"
              />
              <span class="text-sm font-medium text-primary">Include Media Files</span>
            </label>
          </div>
        </div>
        <template #footer>
          <button
            type="button"
            @click="handleTriggerBackup"
            :disabled="!backupForm.backup_type || coreStore.loading"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {{ coreStore.loading ? 'Creating...' : 'Trigger Backup' }}
          </button>
        </template>
      </Modal>

      <!-- Backups Table -->
      <Card>
        <div v-if="coreStore.loading" class="text-center py-8">Loading backups...</div>
        <div v-else-if="coreStore.error" class="text-center py-8 text-red-600">
          {{ coreStore.error }}
        </div>
        <div v-else-if="coreStore.backups.length === 0" class="text-center py-8 text-muted">
          No backups found
        </div>
        <div v-else class="table-container">
          <table class="table-base">
            <thead class="table-thead">
              <tr>
                <th class="table-th">Type</th>
                <th class="table-th">Status</th>
                <th class="table-th">File Size</th>
                <th class="table-th">Started</th>
                <th class="table-th">Completed</th>
                <th class="table-th">Duration</th>
                <th class="table-th">Created By</th>
                <th class="table-th text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="table-tbody">
              <tr v-for="backup in coreStore.backups" :key="backup.id" class="table-tr">
                <td class="table-td">
                  <span class="badge-primary px-2 py-1 rounded text-xs capitalize">
                    {{ backup.backup_type || 'N/A' }}
                  </span>
                </td>
                <td class="table-td">
                  <span :class="getStatusClass(backup.status)" class="px-2 py-1 rounded text-xs font-medium">
                    {{ backup.status || 'unknown' }}
                  </span>
                </td>
                <td class="table-td text-number">
                  {{ formatFileSize(backup.file_size) }}
                </td>
                <td class="table-td text-number">
                  {{ formatDate(backup.started_at) }}
                </td>
                <td class="table-td text-number">
                  {{ formatDate(backup.completed_at) || '-' }}
                </td>
                <td class="table-td text-number">
                  {{ formatDuration(backup.duration_seconds) }}
                </td>
                <td class="table-td text-number">
                  {{ backup.created_by_username || 'System' }}
                </td>
                <td class="table-td text-right">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      @click="viewBackup(backup)"
                      class="action-btn-view"
                      title="View"
                    >
                      <EyeIcon class="w-4 h-4" />
                    </button>
                    <button
                      v-if="backup.status === 'completed'"
                      @click="verifyBackup(backup.id)"
                      class="action-btn-verify"
                      title="Verify"
                    >
                      <CheckCircleIcon class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Backup Detail Modal -->
      <Modal :show="showDetailModal" title="Backup Details" @close="showDetailModal = false">
        <div v-if="selectedBackup" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-base block text-sm">Backup Type</label>
              <div class="mt-1">
                <span class="badge-primary px-2 py-1 rounded text-xs capitalize">
                  {{ selectedBackup.backup_type }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Status</label>
              <div class="mt-1">
                <span :class="getStatusClass(selectedBackup.status)" class="px-2 py-1 rounded text-xs font-medium">
                  {{ selectedBackup.status }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">File Path</label>
              <div class="mt-1 text-sm text-primary font-mono text-xs break-all">
                {{ selectedBackup.file_path || 'N/A' }}
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">File Size</label>
              <div class="mt-1 text-sm text-primary">
                {{ formatFileSize(selectedBackup.file_size) }}
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Started At</label>
              <div class="mt-1 text-sm text-primary">{{ formatDate(selectedBackup.started_at) }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">Completed At</label>
              <div class="mt-1 text-sm text-primary">{{ formatDate(selectedBackup.completed_at) || '-' }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">Duration</label>
              <div class="mt-1 text-sm text-primary">
                {{ formatDuration(selectedBackup.duration_seconds) }}
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Created By</label>
              <div class="mt-1 text-sm text-primary">{{ selectedBackup.created_by_username || 'System' }}</div>
            </div>
            <div>
              <label class="label-base block text-sm">Compression</label>
              <div class="mt-1">
                <span :class="selectedBackup.compression ? 'badge-success' : 'badge-info'" class="px-2 py-1 rounded text-xs">
                  {{ selectedBackup.compression ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Include Media</label>
              <div class="mt-1">
                <span :class="selectedBackup.include_media ? 'badge-success' : 'badge-info'" class="px-2 py-1 rounded text-xs">
                  {{ selectedBackup.include_media ? 'Yes' : 'No' }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Scheduled</label>
              <div class="mt-1">
                <span :class="selectedBackup.scheduled ? 'badge-primary' : 'badge-info'" class="px-2 py-1 rounded text-xs">
                  {{ selectedBackup.scheduled ? 'Yes' : 'Manual' }}
                </span>
              </div>
            </div>
            <div>
              <label class="label-base block text-sm">Expires At</label>
              <div class="mt-1 text-sm text-primary">{{ formatDate(selectedBackup.expires_at) || 'Never' }}</div>
            </div>
          </div>
          <div v-if="selectedBackup.checksum">
            <label class="label-base block text-sm">Checksum</label>
            <div class="mt-1 text-sm text-primary font-mono text-xs break-all">
              {{ selectedBackup.checksum }}
            </div>
          </div>
          <div v-if="selectedBackup.error_message">
            <label class="label-base block text-sm">Error Message</label>
            <div class="mt-1 p-3 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-800 dark:text-red-300 break-words">{{ selectedBackup.error_message }}</div>
          </div>
          <div v-if="selectedBackup.metadata">
            <label class="label-base block text-sm">Metadata</label>
            <pre class="mt-1 p-3 bg-slate-50 dark:bg-slate-800 rounded text-xs text-primary overflow-auto">{{ JSON.stringify(selectedBackup.metadata, null, 2) }}</pre>
          </div>
        </div>
      </Modal>
    </div>
  </component>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { EyeIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'
import { useCoreStore } from '@/stores/core'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'

defineProps({
  embedded: { type: Boolean, default: false },
})

const coreStore = useCoreStore()

const filters = ref({
  backup_type: '',
  status: '',
})

const showTriggerModal = ref(false)
const showDetailModal = ref(false)
const selectedBackup = ref(null)

const backupForm = ref({
  backup_type: '',
  compression: true,
  include_media: false,
})

const applyFilters = () => {
  const params = {}
  if (filters.value.backup_type) params.backup_type = filters.value.backup_type
  if (filters.value.status) params.status = filters.value.status
  coreStore.fetchBackups(params)
}

const clearFilters = () => {
  filters.value = {
    backup_type: '',
    status: '',
  }
  coreStore.fetchBackups()
}

const handleTriggerBackup = async () => {
  try {
    await coreStore.triggerBackup(backupForm.value.backup_type, {
      compression: backupForm.value.compression,
      include_media: backupForm.value.include_media,
    })
    showTriggerModal.value = false
    backupForm.value = {
      backup_type: '',
      compression: true,
      include_media: false,
    }
  } catch (error) {
    // Error handled in store
  }
}

const handleCleanup = async () => {
  if (!confirm('Are you sure you want to cleanup expired backups?')) return
  try {
    await coreStore.cleanupBackups()
  } catch (error) {
    // Error handled in store
  }
}

const viewBackup = (backup) => {
  selectedBackup.value = backup
  showDetailModal.value = true
}

const verifyBackup = async (id) => {
  try {
    await coreStore.verifyBackup(id)
  } catch (error) {
    // Error handled in store
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const formatFileSize = (bytes) => {
  if (!bytes) return 'N/A'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

const formatDuration = (seconds) => {
  if (!seconds) return 'N/A'
  if (seconds < 60) return seconds + 's'
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm ' + (seconds % 60) + 's'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${hours}h ${minutes}m ${secs}s`
}

const getStatusClass = (status) => {
  const classes = {
    pending: 'badge-warning',
    in_progress: 'badge-primary',
    completed: 'badge-success',
    failed: 'badge-error',
    expired: 'badge-info',
  }
  return classes[status] || 'badge-info'
}

onMounted(() => {
  coreStore.fetchBackups()
})
</script>
