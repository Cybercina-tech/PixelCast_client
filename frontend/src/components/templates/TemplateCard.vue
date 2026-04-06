<template>
  <div
    class="group relative card-base rounded-xl overflow-hidden hover:ring-2 hover:ring-blue-500/50 transition-all"
  >
    <!-- Status Badge -->
    <div class="absolute top-4 right-4 z-10">
      <span
        :class="[
          'px-2 py-1 rounded-full text-xs font-medium',
          template.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-surface-inset text-muted border border-border-color'
        ]"
      >
        {{ template.is_active ? 'Active' : 'Inactive' }}
      </span>
    </div>

    <!-- Mini Canvas Preview (same LayerRenderer + contain scale as screen list) -->
    <div class="relative bg-surface-inset border-b border-border-color p-4">
      <div
        class="rounded-lg overflow-hidden relative bg-black"
        :style="{ aspectRatio: `${template.width || 16}/${template.height || 9}` }"
      >
        <div class="absolute inset-0 border-2 border-border-color rounded-lg pointer-events-none z-[2]"></div>
        <TemplateListPreview :template="template" />
      </div>
    </div>

    <!-- Card Content -->
    <div class="p-4 space-y-3">
      <!-- Header -->
      <div>
        <h3 class="text-lg font-semibold text-primary mb-1 truncate">
          {{ template.name || 'Unnamed Template' }}
        </h3>
        <p v-if="template.description" class="text-sm text-muted line-clamp-2">
          {{ template.description }}
        </p>
      </div>

      <!-- Badges -->
      <div class="flex flex-wrap gap-2">
        <span class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-md text-xs font-medium">
          {{ getAspectRatio(template.width, template.height) }}
        </span>
        <span class="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-md text-xs font-medium">
          {{ template.width }}×{{ template.height }}
        </span>
        <span v-if="template.version" class="px-2 py-1 bg-surface-inset text-muted border border-border-color rounded-md text-xs font-medium">
          v{{ template.version }}
        </span>
      </div>

      <!-- Metadata -->
      <div class="space-y-2 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-muted">Last Modified</span>
          <span class="text-primary">{{ formatLastModified(template.updated_at) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-muted">Created By</span>
          <span class="text-primary">{{ getCreatedBy(template.created_by) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-muted">Screens Using</span>
          <span class="text-primary">{{ template.screens_count || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- Hover Overlay with Miniature Action Buttons -->
    <div class="absolute inset-0 bg-slate-900/40 dark:bg-black/40 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-20">
      <div class="flex items-center gap-2 bg-slate-900/45 dark:bg-black/40 backdrop-blur-sm rounded-lg p-2 border border-white/20 dark:border-white/10">
        <!-- Edit Button -->
        <button
          @click.stop="$emit('edit', template)"
          class="p-2.5 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white transition-all duration-200 hover:scale-110 hover:shadow-lg hover:shadow-blue-500/50"
          title="Edit Template"
        >
          <PencilIcon class="w-5 h-5" />
        </button>
        
        <!-- Duplicate Button -->
        <button
          v-if="canDuplicate"
          @click.stop="$emit('duplicate', template)"
          class="p-2.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white transition-all duration-200 hover:scale-110 hover:shadow-lg hover:shadow-indigo-500/50"
          title="Duplicate Template"
        >
          <DocumentDuplicateIcon class="w-5 h-5" />
        </button>
        
        <!-- Push to Screen Button -->
        <button
          v-if="canPush"
          @click.stop="$emit('push', template)"
          class="p-2.5 rounded-lg bg-purple-600/80 hover:bg-purple-600 text-white transition-all duration-200 hover:scale-110 hover:shadow-lg hover:shadow-purple-500/50"
          title="Push to Screen"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </button>
        
        <!-- Delete Button -->
        <button
          v-if="canDelete"
          @click.stop="$emit('delete', template)"
          class="p-2.5 rounded-lg bg-red-600/80 hover:bg-red-600 text-white transition-all duration-200 hover:scale-110 hover:shadow-lg hover:shadow-red-500/50"
          title="Delete Template"
        >
          <TrashIcon class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  PencilIcon,
  DocumentDuplicateIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'
import TemplateListPreview from './TemplateListPreview.vue'

const props = defineProps({
  template: {
    type: Object,
    required: true,
  },
  /** When false, hide duplicate (needs create_templates). */
  canDuplicate: {
    type: Boolean,
    default: true,
  },
  /** When false, hide push to screen (needs edit_templates). */
  canPush: {
    type: Boolean,
    default: true,
  },
  /** When false, hide delete (needs delete_templates). */
  canDelete: {
    type: Boolean,
    default: true,
  },
})

defineEmits(['edit', 'duplicate', 'push', 'delete'])

// Calculate aspect ratio
const getAspectRatio = (width, height) => {
  if (!width || !height) return 'N/A'
  const gcd = (a, b) => b === 0 ? a : gcd(b, a % b)
  const divisor = gcd(width, height)
  const ratioWidth = width / divisor
  const ratioHeight = height / divisor
  
  // Common ratios
  if (ratioWidth === 16 && ratioHeight === 9) return '16:9'
  if (ratioWidth === 9 && ratioHeight === 16) return '9:16'
  if (ratioWidth === 4 && ratioHeight === 3) return '4:3'
  if (ratioWidth === 3 && ratioHeight === 4) return '3:4'
  if (ratioWidth === 21 && ratioHeight === 9) return '21:9'
  if (ratioWidth === 1 && ratioHeight === 1) return '1:1'
  
  return `${ratioWidth}:${ratioHeight}`
}

// Format last modified time
const formatLastModified = (timestamp) => {
  if (!timestamp) return 'Never'
  const now = new Date()
  const lastModified = new Date(timestamp)
  const diffMs = now - lastModified
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return lastModified.toLocaleDateString()
}

// Get created by name
const getCreatedBy = (createdBy) => {
  if (!createdBy) return 'Unknown'
  if (typeof createdBy === 'string') return createdBy
  if (createdBy.username) return createdBy.username
  if (createdBy.email) return createdBy.email
  return 'Unknown'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
