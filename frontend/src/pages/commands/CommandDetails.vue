<template>
  <AppLayout>
    <div v-if="commandsStore.loading" class="text-center py-8">Loading...</div>
    <div v-else-if="command" class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ command.name || command.type }}</h1>
          <p class="text-gray-600">Command Details</p>
        </div>
        <div class="flex gap-2">
          <button
            v-if="command.status === 'failed'"
            @click="handleRetry"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Command Information">
          <dl class="space-y-3">
            <div>
              <dt class="text-sm font-medium text-gray-500">Type</dt>
              <dd class="mt-1 text-sm text-gray-900 capitalize">{{ command.type }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Status</dt>
              <dd class="mt-1">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    command.status === 'done' ? 'bg-green-100 text-green-800' : '',
                    command.status === 'failed' ? 'bg-red-100 text-red-800' : '',
                    command.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : '',
                    command.status === 'executing' ? 'bg-blue-100 text-blue-800' : '',
                  ]"
                >
                  {{ command.status }}
                </span>
              </dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Screen</dt>
              <dd class="mt-1 text-sm text-gray-900">
                {{ command.screen?.name || command.screen?.device_id || 'N/A' }}
              </dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Priority</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ command.priority }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Created</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(command.created_at) }}</dd>
            </div>
            <div v-if="command.executed_at">
              <dt class="text-sm font-medium text-gray-500">Executed</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(command.executed_at) }}</dd>
            </div>
            <div v-if="command.completed_at">
              <dt class="text-sm font-medium text-gray-500">Completed</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(command.completed_at) }}</dd>
            </div>
          </dl>
        </Card>
        
        <Card title="Payload">
          <pre class="bg-gray-50 p-4 rounded-lg text-sm overflow-auto">{{ JSON.stringify(command.payload, null, 2) }}</pre>
        </Card>
      </div>
      
      <Card v-if="command.error_message" title="Error">
        <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded break-words">
          {{ command.error_message }}
        </div>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useCommandsStore } from '@/stores/commands'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'

const route = useRoute()
const commandsStore = useCommandsStore()
const notify = useNotification()

const command = computed(() => commandsStore.currentCommand)

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const handleRetry = async () => {
  try {
    await commandsStore.retryCommand(command.value.id)
    notify.success('Command retry initiated')
    await commandsStore.fetchCommand(command.value.id)
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to retry command')
  }
}

onMounted(async () => {
  const commandId = route.params.id
  await commandsStore.fetchCommand(commandId)
})
</script>
