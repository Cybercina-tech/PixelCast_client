<template>
  <div
    class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-border-color bg-surface-inset"
  >
    <div class="flex items-start gap-3 min-w-0">
      <component :is="icon" class="w-5 h-5 text-muted shrink-0 mt-0.5" />
      <div class="min-w-0">
        <p class="text-sm font-medium text-primary truncate">{{ title }}</p>
        <p v-if="subtitle" class="text-xs text-muted truncate">{{ subtitle }}</p>
        <p class="text-xs text-muted mt-0.5">
          IP: {{ session.ip_address || '—' }}
        </p>
        <p class="text-xs text-muted">
          Last activity: {{ formatSessionActivity(session.last_activity) }}
        </p>
      </div>
    </div>
    <div class="flex items-center gap-3 shrink-0">
      <span
        v-if="session.current"
        class="px-2 py-0.5 rounded text-xs font-medium bg-forest-green/15 text-forest-green border border-forest-green/30"
      >
        Current
      </span>
      <button
        v-else-if="showRevoke"
        type="button"
        class="btn-outline px-3 py-1.5 rounded-lg text-sm text-error border-error/30 hover:bg-error/10 disabled:opacity-50"
        :disabled="revoking"
        @click="$emit('revoke', session.id)"
      >
        <span v-if="revoking">Revoking…</span>
        <span v-else>{{ revokeLabel }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  ComputerDesktopIcon,
  DevicePhoneMobileIcon,
} from '@heroicons/vue/24/outline'
import {
  formatSessionActivity,
  sessionDeviceKind,
  sessionSubtitle,
  sessionTitle,
} from '@/utils/sessionDisplay'

const props = defineProps({
  session: { type: Object, required: true },
  revoking: { type: Boolean, default: false },
  showRevoke: { type: Boolean, default: true },
  revokeLabel: { type: String, default: 'Revoke' },
})

defineEmits(['revoke'])

const title = computed(() => sessionTitle(props.session))
const subtitle = computed(() => sessionSubtitle(props.session))

const icon = computed(() => {
  const kind = sessionDeviceKind(props.session)
  if (kind === 'mobile' || kind === 'tablet') return DevicePhoneMobileIcon
  return ComputerDesktopIcon
})
</script>
