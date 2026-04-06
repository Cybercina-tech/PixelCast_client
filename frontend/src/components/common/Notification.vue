<template>
  <Transition
    name="notification"
    appear
    @enter="onEnter"
    @leave="onLeave"
  >
    <div
      v-if="visible"
      :class="[
        'notification',
        `notification--${type}`,
        'max-w-sm w-full shadow-lg rounded-2xl pointer-events-auto',
        'border',
        typeClasses.background,
        typeClasses.border,
        'overflow-hidden',
      ]"
      role="alert"
      :aria-live="type === 'error' ? 'assertive' : 'polite'"
      :aria-atomic="true"
    >
      <div class="p-4">
        <div class="flex items-start">
          <!-- Icon -->
          <div class="flex-shrink-0">
            <component
              :is="iconComponent"
              :class="[
                'h-6 w-6',
                typeClasses.icon,
              ]"
            />
          </div>

          <!-- Content -->
          <div class="ml-3 flex-1 min-w-0">
            <!-- Title (optional) -->
            <h4
              v-if="title"
              :class="[
                'text-sm font-semibold',
                typeClasses.title,
              ]"
            >
              {{ title }}
            </h4>

            <!-- Message -->
            <p
              :class="[
                title ? 'mt-1' : '',
                'text-sm font-medium',
                typeClasses.message,
              ]"
            >
              {{ message }}
            </p>

            <!-- Action Button (optional) -->
            <div
              v-if="action"
              class="mt-3"
            >
              <button
                @click="handleAction"
                :class="[
                  'text-sm font-medium underline',
                  typeClasses.action,
                  'hover:opacity-80 transition-opacity',
                  'focus:outline-none focus:ring-2 focus:ring-offset-2 rounded',
                  typeClasses.actionFocus,
                ]"
              >
                {{ action.label }}
              </button>
            </div>
          </div>

          <!-- Close Button -->
          <div class="ml-4 flex-shrink-0">
            <button
              @click="handleClose"
              :class="[
                'inline-flex rounded-md p-1.5',
                'text-slate-400 hover:text-slate-600 dark:text-slate-400 dark:hover:text-slate-200',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800',
                'focus:ring-slate-500 dark:focus:ring-slate-400',
                'transition-colors',
              ]"
              aria-label="Close notification"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Progress Bar (if auto-dismiss) -->
      <div
        v-if="duration > 0 && showProgress"
        class="h-1 bg-slate-200/50 dark:bg-slate-700"
      >
        <div
          :class="[
            'h-full transition-all ease-linear',
            typeClasses.progress,
          ]"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value),
  },
  duration: {
    type: Number,
    default: 5000,
  },
  title: {
    type: String,
    default: null,
  },
  action: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'action'])

const visible = ref(true)
const showProgress = ref(false)
const progressPercent = ref(100)
let timeoutId = null
let progressInterval = null
const startTime = ref(Date.now())

const typeClasses = computed(() => {
  const classes = {
    success: {
      background: 'bg-emerald-50/95 dark:bg-slate-800/95',
      border: 'border-emerald-200/80 dark:border-emerald-500/30',
      icon: 'text-emerald-600 dark:text-emerald-400',
      title: 'text-emerald-800 dark:text-emerald-200',
      message: 'text-slate-600 dark:text-slate-200',
      action: 'text-emerald-700 dark:text-emerald-300',
      actionFocus: 'focus:ring-emerald-400 dark:focus:ring-emerald-500',
      progress: 'bg-emerald-400 dark:bg-emerald-500',
    },
    error: {
      background: 'bg-rose-50/95 dark:bg-slate-800/95',
      border: 'border-rose-200/80 dark:border-rose-500/25',
      icon: 'text-rose-500 dark:text-rose-400',
      title: 'text-rose-800 dark:text-rose-100',
      message: 'text-slate-600 dark:text-slate-200',
      action: 'text-rose-700 dark:text-rose-300',
      actionFocus: 'focus:ring-rose-300 dark:focus:ring-rose-500',
      progress: 'bg-rose-400 dark:bg-rose-500',
    },
    warning: {
      background: 'bg-amber-50/95 dark:bg-slate-800/95',
      border: 'border-amber-200/80 dark:border-amber-500/30',
      icon: 'text-amber-600 dark:text-amber-400',
      title: 'text-amber-900 dark:text-amber-100',
      message: 'text-slate-600 dark:text-slate-200',
      action: 'text-amber-800 dark:text-amber-300',
      actionFocus: 'focus:ring-amber-300 dark:focus:ring-amber-500',
      progress: 'bg-amber-400 dark:bg-amber-500',
    },
    info: {
      background: 'bg-slate-50/95 dark:bg-slate-800/95',
      border: 'border-slate-200/90 dark:border-slate-600/50',
      icon: 'text-slate-500 dark:text-slate-400',
      title: 'text-slate-800 dark:text-slate-100',
      message: 'text-slate-600 dark:text-slate-300',
      action: 'text-slate-700 dark:text-slate-300',
      actionFocus: 'focus:ring-slate-400 dark:focus:ring-slate-500',
      progress: 'bg-slate-400 dark:bg-slate-500',
    },
  }
  return classes[props.type] || classes.info
})

const iconComponent = computed(() => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }
  return icons[props.type] || InformationCircleIcon
})

const handleClose = () => {
  if (timeoutId) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  visible.value = false
  setTimeout(() => {
    emit('close')
  }, 300) // Wait for animation to complete
}

const handleAction = () => {
  if (props.action?.handler) {
    props.action.handler()
  }
  emit('action', props.action)
  handleClose()
}

const onEnter = (el) => {
  // Trigger animation
  requestAnimationFrame(() => {
    el.style.transform = 'translateX(0)'
    el.style.opacity = '1'
  })
}

const onLeave = (el, done) => {
  // Animation handled by CSS
  setTimeout(done, 300)
}

onMounted(() => {
  if (props.duration > 0) {
    showProgress.value = true
    
    // Update progress bar
    progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime.value
      const remaining = Math.max(0, props.duration - elapsed)
      progressPercent.value = (remaining / props.duration) * 100
      
      if (remaining <= 0) {
        clearInterval(progressInterval)
        handleClose()
      }
    }, 50) // Update every 50ms for smooth animation

    // Auto-dismiss
    timeoutId = setTimeout(() => {
      handleClose()
    }, props.duration)
  }
})

onUnmounted(() => {
  if (timeoutId) {
    clearTimeout(timeoutId)
  }
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})
</script>

<style scoped>
.notification {
  /* Initial state handled by Vue transitions */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-enter-from {
  transform: translateX(400px);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(400px);
  opacity: 0;
}

/* Position-specific animations */
.notification--top-left.notification-enter-from,
.notification--bottom-left.notification-enter-from {
  transform: translateX(-400px);
}

.notification--top-left.notification-leave-to,
.notification--bottom-left.notification-leave-to {
  transform: translateX(-400px);
}

.notification--bottom-right.notification-enter-from,
.notification--bottom-left.notification-enter-from {
  transform: translateY(400px);
}

.notification--bottom-right.notification-leave-to,
.notification--bottom-left.notification-leave-to {
  transform: translateY(400px);
}
</style>

