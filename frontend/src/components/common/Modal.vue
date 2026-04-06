<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto" @click.self="$emit('close')">
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
          <div class="fixed inset-0 transition-opacity bg-black/40 backdrop-blur-md" aria-hidden="true"></div>
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
          <div
            :class="[
              'inline-block align-bottom bg-card backdrop-blur-lg rounded-2xl text-left overflow-hidden shadow-2xl border border-border-color transform transition-all duration-300 sm:my-8 sm:align-middle',
              size === 'large' ? 'sm:max-w-4xl sm:w-full' : 'sm:max-w-lg sm:w-full'
            ]"
            style="animation: modalFadeUp 0.3s ease-out;"
          >
            <div class="bg-card px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-primary">{{ title }}</h3>
                <button
                  @click="$emit('close')"
                  class="text-muted hover:text-primary transition-colors duration-200 p-1 rounded-lg hover:bg-card"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <slot></slot>
            </div>
            <div v-if="showFooter" class="bg-card px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse border-t border-border-color">
              <slot name="footer">
                <Button
                  variant="primary"
                  @click="$emit('confirm')"
                  class="w-full sm:w-auto sm:ml-3"
                >
                  Confirm
                </Button>
                <Button
                  variant="secondary"
                  @click="$emit('close')"
                  class="mt-3 w-full sm:mt-0 sm:w-auto sm:ml-3"
                >
                  Cancel
                </Button>
              </slot>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import Button from './Button.vue'

defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'Modal',
  },
  showFooter: {
    type: Boolean,
    default: true,
  },
  size: {
    type: String,
    default: 'normal',
    validator: (value) => ['normal', 'large'].includes(value),
  },
})

defineEmits(['close', 'confirm'])
</script>

<style scoped>
.modal-enter-active {
  transition: opacity 0.3s ease-out;
}

.modal-leave-active {
  transition: opacity 0.2s ease-in;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .inline-block {
  animation: modalFadeUp 0.3s ease-out;
}

@keyframes modalFadeUp {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
