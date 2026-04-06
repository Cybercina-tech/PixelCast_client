<template>
  <div
    class="group relative screen-card rounded-xl overflow-hidden transition-all duration-400"
    :class="{
      'screen-card-online': status === 'online',
      'screen-card-offline': status === 'offline'
    }"
  >
    <!-- Status Indicator -->
    <div class="absolute top-4 right-4 z-10 pointer-events-none">
      <StatusIndicator :status="status" />
    </div>

    <!-- Monitor Preview -->
    <div class="relative bg-card border-b border-border-color p-4">
      <div class="aspect-video bg-base rounded-lg overflow-hidden relative">
        <!-- Monitor Frame Effect -->
        <div class="absolute inset-0 border-2 border-border-color rounded-lg pointer-events-none"></div>
        
        <!-- Live template preview (same layout as player) -->
        <ScreenTemplatePreview :screen="screen" />
      </div>
    </div>

    <!-- Card Content -->
    <div class="p-4 space-y-3">
      <!-- Header -->
      <div>
        <h3 class="text-lg font-semibold text-primary mb-1 truncate">
          {{ screen.name || 'Unnamed Screen' }}
        </h3>
        <div class="flex items-center gap-2 text-sm text-muted">
          <span class="font-mono">{{ screen.pairing_code || 'N/A' }}</span>
        </div>
      </div>

      <!-- Metadata -->
      <div class="space-y-2 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-muted">Last Seen</span>
          <span class="text-primary">{{ formatLastSeen(screen.last_heartbeat_at) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-muted">IP Address</span>
          <span class="text-primary font-mono text-xs">{{ screen.current_ip || 'N/A' }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-muted">Player Version</span>
          <span class="text-primary text-xs">{{ screen.player_version || 'Unknown' }}</span>
        </div>
      </div>
    </div>

    <!-- Hover overlay: wrap + padding so buttons never overlap or clip -->
    <div
      class="absolute inset-0 z-20 flex flex-wrap items-center justify-center content-center gap-2 sm:gap-3 px-4 py-5 sm:px-5 bg-base/95 dark:bg-black/80 backdrop-blur-sm opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity duration-400 overflow-y-auto"
    >
      <button
        type="button"
        @click="$emit('identify', screen)"
        class="btn-secondary px-4 sm:px-5 py-2 rounded-lg font-medium inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap"
        title="Identify Screen"
      >
        <FingerPrintIcon class="w-4 h-4 shrink-0" />
        Identify
      </button>
      <button
        type="button"
        @click="$emit('edit', screen)"
        class="btn-success px-4 sm:px-5 py-2 rounded-lg font-medium inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap"
        title="Manage Screen"
      >
        <PencilIcon class="w-4 h-4 shrink-0" />
        Manage
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useScreensStore } from '@/stores/screens'
import { FingerPrintIcon, PencilIcon } from '@heroicons/vue/24/outline'
import StatusIndicator from './StatusIndicator.vue'
import ScreenTemplatePreview from './ScreenTemplatePreview.vue'

const props = defineProps({
  screen: {
    type: Object,
    required: true,
  },
})

defineEmits(['identify', 'edit'])

const screensStore = useScreensStore()

const status = computed(() => {
  return screensStore.getScreenStatus(props.screen)
})

const formatLastSeen = (timestamp) => {
  if (!timestamp) return 'Never'
  const now = new Date()
  const lastSeen = new Date(timestamp)
  const diffMs = now - lastSeen
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return lastSeen.toLocaleDateString()
}
</script>

<style scoped>
/* Screen Card - Soft White with Floating Shadow */
.screen-card {
  background: var(--cream-bg);
  border: 1px solid var(--border-color);
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 2px 4px -1px rgba(0, 0, 0, 0.03);
  transition: all 0.4s ease;
}

.dark .screen-card {
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
}

.screen-card:hover {
  box-shadow: 
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.dark .screen-card:hover {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
  transform: none;
}

/* Online Screen - Outer Glow Effect */
.screen-card-online {
  position: relative;
}

.screen-card-online::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 0.875rem;
  background: linear-gradient(135deg, rgba(22, 101, 52, 0.15), rgba(22, 101, 52, 0.05));
  opacity: 0;
  transition: opacity 0.4s ease;
  z-index: -1;
  pointer-events: none;
}

.screen-card-online:hover::before {
  opacity: 1;
}

.dark .screen-card-online::before {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1));
}

/* Offline Screen - Muted Effect */
.screen-card-offline {
  opacity: 0.85;
}

.screen-card-offline::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 0.75rem;
  background: rgba(185, 28, 28, 0.02);
  pointer-events: none;
}

.dark .screen-card-offline {
  opacity: 0.7;
}
</style>

