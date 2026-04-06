<template>
  <div class="space-y-4">
    <div v-if="commands.length === 0" class="text-center text-muted py-8">
      <svg class="w-12 h-12 mx-auto mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p class="text-sm">No commands in queue</p>
    </div>
    <div v-else class="relative">
      <!-- Timeline Line -->
      <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-700/50"></div>
      <!-- Timeline Items -->
      <div class="space-y-4">
        <div
          v-for="(command, index) in commands"
          :key="command.id"
          class="relative flex items-start gap-4"
        >
          <!-- Status Icon -->
          <div class="relative z-10 flex-shrink-0">
            <div
              :class="[
                'w-12 h-12 rounded-full flex items-center justify-center border-2',
                getStatusIconClass(command.status),
              ]"
            >
              <!-- Pending: Spinning Loader -->
              <svg
                v-if="command.status === 'pending'"
                class="animate-spin w-6 h-6 text-yellow-400"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <!-- Done: Checkmark -->
              <svg
                v-else-if="command.status === 'done'"
                class="w-6 h-6 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <!-- Failed: X -->
              <svg
                v-else-if="command.status === 'failed'"
                class="w-6 h-6 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <!-- Executing: Pulse -->
              <svg
                v-else-if="command.status === 'executing'"
                class="w-6 h-6 text-blue-400 animate-pulse"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <!-- Command Details -->
          <div class="flex-1 min-w-0 pt-1">
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-semibold text-primary truncate">{{ command.name || command.type }}</h4>
                <p class="text-xs text-muted mt-0.5">{{ formatCommandType(command.type) }}</p>
              </div>
              <span
                :class="[
                  'px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap',
                  getStatusBadgeClass(command.status),
                ]"
              >
                {{ command.status }}
              </span>
            </div>
            <p class="text-xs text-muted mt-2">{{ formatDate(command.created_at) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  commands: {
    type: Array,
    default: () => [],
  },
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatCommandType = (type) => {
  if (!type) return 'Unknown'
  return type
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const getStatusIconClass = (status) => {
  switch (status) {
    case 'pending':
      return 'bg-yellow-900/30 border-yellow-500/50'
    case 'executing':
      return 'bg-blue-900/30 border-blue-500/50'
    case 'done':
      return 'bg-green-900/30 border-green-500/50'
    case 'failed':
      return 'bg-red-900/30 border-red-500/50'
    default:
      return 'bg-gray-900/30 border-gray-500/50'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'pending':
      return 'bg-yellow-900/40 text-yellow-300'
    case 'executing':
      return 'bg-blue-900/40 text-blue-300'
    case 'done':
      return 'bg-green-900/40 text-green-300'
    case 'failed':
      return 'bg-red-900/40 text-red-300'
    default:
      return 'bg-gray-900/40 text-gray-300'
  }
}
</script>

