<template>
  <Teleport to="body">
    <div
      :class="[
        'notification-container',
        `notification-container--${position}`,
        'fixed z-[9999] pointer-events-none',
        positionClasses,
      ]"
      aria-live="polite"
      aria-label="Notifications"
    >
      <TransitionGroup
        name="notification-list"
        tag="div"
        class="space-y-3"
      >
        <Notification
          v-for="notification in visibleNotifications"
          :key="notification.id"
          :id="notification.id"
          :message="notification.message"
          :type="notification.type"
          :duration="notification.duration"
          :title="notification.title"
          :action="notification.action"
          @close="handleClose(notification.id)"
          @action="handleAction(notification)"
        />
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useNotificationStore } from '@/stores/notification'
import Notification from './Notification.vue'

const notificationStore = useNotificationStore()

// Use storeToRefs to ensure reactivity
const { position, notifications, maxNotifications } = storeToRefs(notificationStore)

const visibleNotifications = computed(() => {
  // Access notifications directly from refs to ensure reactivity
  return notifications.value.slice(0, maxNotifications.value)
})

// Ensure container is always mounted for reactivity

const positionClasses = computed(() => {
  const classes = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
  }
  return classes[position.value] || classes['top-right']
})

const handleClose = (id) => {
  notificationStore.remove(id)
}

const handleAction = (notification) => {
  // Action is handled by Notification component
  // This is just for potential future use
}
</script>

<style scoped>
.notification-list-enter-active,
.notification-list-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-list-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.notification-list-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.notification-list-move {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .notification-container {
    left: 1rem !important;
    right: 1rem !important;
    width: auto;
  }
  
  .notification-container :deep(.notification) {
    max-width: 100%;
  }
}
</style>

