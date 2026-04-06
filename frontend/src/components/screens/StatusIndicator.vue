<template>
  <div class="flex items-center gap-2">
    <div
      :class="[
        'w-3 h-3 rounded-full',
        statusClasses[status] || statusClasses.offline,
        darkStatusClasses[status] || darkStatusClasses.offline,
        status === 'online' ? 'animate-pulse' : ''
      ]"
    ></div>
    <span
      :class="[
        'text-xs font-medium',
        textClasses[status] || textClasses.offline,
        darkTextClasses[status] || darkTextClasses.offline
      ]"
    >
      {{ statusText[status] || 'Offline' }}
    </span>
  </div>
</template>

<script setup>
const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['online', 'offline', 'connecting'].includes(value),
  },
})

const statusClasses = {
  online: 'bg-forest-green',
  offline: 'bg-dusty-red',
  connecting: 'bg-amber-500 animate-pulse',
}

const textClasses = {
  online: 'text-forest-green',
  offline: 'text-dusty-red',
  connecting: 'text-amber-600',
}

// Dark mode overrides
const darkStatusClasses = {
  online: 'dark:bg-emerald-400',
  offline: 'dark:bg-red-400',
  connecting: 'dark:bg-yellow-400',
}

const darkTextClasses = {
  online: 'dark:text-emerald-400',
  offline: 'dark:text-red-400',
  connecting: 'dark:text-yellow-400',
}

const statusText = {
  online: 'Online',
  offline: 'Offline',
  connecting: 'Connecting...',
}
</script>

