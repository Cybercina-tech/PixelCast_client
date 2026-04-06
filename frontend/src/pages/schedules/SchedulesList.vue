<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-primary">Schedules</h1>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          Create Schedule
        </button>
      </div>
      
      <Card>
        <div v-if="schedulesStore.loading" class="text-center py-8">Loading...</div>
        <div v-else-if="schedulesStore.error" class="text-center py-8 text-red-600">
          {{ schedulesStore.error }}
        </div>
        <Table
          v-else
          :columns="columns"
          :data="schedulesStore.filteredSchedules"
          :actions="['view', 'edit', 'delete']"
          @view="handleView"
          @edit="handleEdit"
          @delete="handleDelete"
        >
          <template #cell-is_active="{ value }">
            <span
              :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                value ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300',
              ]"
            >
              {{ value ? 'Active' : 'Inactive' }}
            </span>
          </template>
          <template #cell-template="{ value }">
            <span v-if="value">{{ value.name || 'N/A' }}</span>
            <span v-else class="text-muted">None</span>
          </template>
          <template #cell-repeat_type="{ value }">
            <span class="capitalize">{{ value || 'none' }}</span>
          </template>
          <template #actions="{ row }">
            <div class="flex items-center justify-end gap-1">
              <router-link
                :to="`/schedules/${row.id}`"
                class="action-btn-view"
                title="View"
              >
                <EyeIcon class="w-4 h-4" />
              </router-link>
              <button
                @click="handleEdit(row)"
                class="action-btn-edit"
                title="Edit"
              >
                <PencilIcon class="w-4 h-4" />
              </button>
              <button
                @click="handleExecute(row)"
                class="action-btn-execute"
                title="Execute"
              >
                <PlayIcon class="w-4 h-4" />
              </button>
              <button
                @click="handleToggleActive(row)"
                :class="row.is_active ? 'action-btn-delete' : 'action-btn-edit'"
                :title="row.is_active ? 'Deactivate' : 'Activate'"
              >
                <span class="text-xs font-semibold">
                  {{ row.is_active ? 'Off' : 'On' }}
                </span>
              </button>
              <button
                @click="handleDelete(row)"
                class="action-btn-delete"
                title="Delete"
              >
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </template>
        </Table>
      </Card>
      
      <Modal
        :show="showCreateModal || showEditModal"
        :title="showEditModal ? 'Edit Schedule' : 'Create Schedule'"
        @close="closeModal"
      >
        <div class="space-y-4">
          <div v-if="formError" class="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {{ formError }}
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Name</label>
            <input v-model="form.name" type="text" required class="input-base w-full px-3 py-2 rounded-lg" />
            <p v-if="fieldErrors.name" class="mt-1 text-xs text-red-400">{{ fieldErrors.name[0] }}</p>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Template</label>
            <select v-model="form.template" required class="select-base w-full px-3 py-2 rounded-lg">
              <option value="">Select template</option>
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}
              </option>
            </select>
            <p v-if="fieldErrors.template" class="mt-1 text-xs text-red-400">{{ fieldErrors.template[0] }}</p>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-base block text-sm mb-1">Start Time</label>
              <input v-model="form.start_time" type="datetime-local" required class="input-base w-full px-3 py-2 rounded-lg" />
              <p v-if="fieldErrors.start_time" class="mt-1 text-xs text-red-400">{{ fieldErrors.start_time[0] }}</p>
            </div>
            <div>
              <label class="label-base block text-sm mb-1">End Time</label>
              <input v-model="form.end_time" type="datetime-local" required class="input-base w-full px-3 py-2 rounded-lg" />
              <p v-if="fieldErrors.end_time" class="mt-1 text-xs text-red-400">{{ fieldErrors.end_time[0] }}</p>
            </div>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Repeat</label>
            <select v-model="form.repeat_type" class="select-base w-full px-3 py-2 rounded-lg">
              <option value="none">None</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
            <p v-if="fieldErrors.repeat_type" class="mt-1 text-xs text-red-400">{{ fieldErrors.repeat_type[0] }}</p>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleSubmit" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            {{ showEditModal ? 'Update' : 'Create' }}
          </button>
          <button type="button" @click="closeModal" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { EyeIcon, PencilIcon, TrashIcon, PlayIcon } from '@heroicons/vue/24/outline'
import { useSchedulesStore } from '@/stores/schedules'
import { useTemplatesStore } from '@/stores/templates'
import { useNotification } from '@/composables/useNotification'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import { normalizeApiError } from '@/utils/apiError'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Table from '@/components/common/Table.vue'
import Modal from '@/components/common/Modal.vue'

const router = useRouter()
const schedulesStore = useSchedulesStore()
const templatesStore = useTemplatesStore()
const notify = useNotification()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingSchedule = ref(null)
const templates = computed(() => templatesStore.templates)
const formError = ref('')
const fieldErrors = ref({})

const form = ref({
  name: '',
  template: '',
  start_time: '',
  end_time: '',
  repeat_type: 'none',
})

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'template', label: 'Template' },
  { key: 'start_time', label: 'Start Time' },
  { key: 'end_time', label: 'End Time' },
  { key: 'repeat_type', label: 'Repeat' },
  { key: 'is_active', label: 'Status' },
]

const handleView = (row) => {
  router.push(`/schedules/${row.id}`)
}

const handleEdit = (row) => {
  formError.value = ''
  fieldErrors.value = {}
  editingSchedule.value = row
  form.value = {
    name: row.name || '',
    template: row.template?.id || row.template || '',
    start_time: row.start_time ? new Date(row.start_time).toISOString().slice(0, 16) : '',
    end_time: row.end_time ? new Date(row.end_time).toISOString().slice(0, 16) : '',
    repeat_type: row.repeat_type || 'none',
  }
  showEditModal.value = true
}

const handleExecute = async (row) => {
  try {
    await schedulesStore.executeSchedule(row.id)
    notify.success('Schedule executed')
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to execute schedule')
  }
}

const handleDelete = async (row) => {
  try {
    const { confirmDelete } = useDeleteConfirmation()
    await confirmDelete(
      row.id,
      async () => {
        await schedulesStore.deleteSchedule(row.id)
      },
      {
        title: 'Delete Schedule?',
        message: 'This will permanently delete the schedule. This action cannot be undone.',
        itemName: row.name,
        confirmText: 'Yes, Delete Schedule',
        cancelText: 'Cancel'
      }
    )
    notify.success('Schedule deleted successfully')
  } catch (error) {
    if (error.message !== 'Delete cancelled') {
      const parsed = error.apiError || normalizeApiError(error)
      notify.error(parsed.userMessage || 'Failed to delete schedule')
    }
  }
}

const handleToggleActive = async (row) => {
  try {
    await schedulesStore.updateSchedule(row.id, { is_active: !row.is_active })
    notify.success(`Schedule ${row.is_active ? 'deactivated' : 'activated'}`)
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to update status')
  }
}

const handleSubmit = async () => {
  formError.value = ''
  fieldErrors.value = {}
  try {
    if (showEditModal.value) {
      await schedulesStore.updateSchedule(editingSchedule.value.id, form.value)
      notify.success('Schedule updated')
    } else {
      await schedulesStore.createSchedule({ ...form.value, is_active: true })
      notify.success('Schedule created')
    }
    closeModal()
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    formError.value = parsed.formError
    fieldErrors.value = parsed.fieldErrors || {}
    if (!parsed.isValidation || !Object.keys(fieldErrors.value).length) {
      notify.error(parsed.userMessage || 'Operation failed')
    }
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingSchedule.value = null
  formError.value = ''
  fieldErrors.value = {}
  form.value = {
    name: '',
    template: '',
    start_time: '',
    end_time: '',
    repeat_type: 'none',
  }
}

onMounted(async () => {
  await schedulesStore.fetchSchedules()
  await templatesStore.fetchTemplates()
})
</script>
