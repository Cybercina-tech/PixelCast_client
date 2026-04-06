<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="state.show"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="onCancel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-confirmation-title"
        aria-describedby="delete-confirmation-description"
      >
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
          <!-- Backdrop -->
          <div
            class="fixed inset-0 transition-opacity bg-black/50 dark:bg-black/70 backdrop-blur-sm"
            aria-hidden="true"
          ></div>
          
          <!-- Spacer for vertical centering -->
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
          
          <!-- Modal Container -->
          <div
            class="inline-block align-bottom bg-card backdrop-blur-lg rounded-2xl text-left overflow-hidden shadow-2xl border border-border-color transform transition-all duration-300 sm:my-8 sm:align-middle animate-fade-in sm:max-w-md sm:w-full"
          >
            <!-- Modal Content -->
            <div class="bg-card px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <!-- Icon and Title -->
              <div class="flex items-start">
                <div class="flex-shrink-0 mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/30 sm:mx-0 sm:h-10 sm:w-10">
                  <svg
                    class="h-6 w-6 text-red-600 dark:text-red-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                  <h3
                    id="delete-confirmation-title"
                    class="text-lg font-semibold text-primary"
                  >
                    {{ state.title }}
                  </h3>
                  <div class="mt-2">
                    <p
                      id="delete-confirmation-description"
                      class="text-sm text-secondary"
                    >
                      {{ state.message }}
                    </p>
                    <p
                      v-if="state.itemName"
                      class="mt-2 text-sm font-medium text-primary"
                    >
                      <span class="text-error">{{ state.itemName }}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Footer Actions -->
            <div class="bg-card px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse border-t border-border-color">
              <button
                type="button"
                @click="onConfirm"
                :disabled="state.loading"
                class="btn-danger w-full sm:w-auto sm:ml-3 px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span v-if="state.loading" class="flex items-center justify-center">
                  <svg
                    class="animate-spin -ml-1 mr-2 h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {{ state.loadingText || 'Deleting...' }}
                </span>
                <span v-else class="flex items-center justify-center gap-2">
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                  {{ state.confirmText }}
                </span>
              </button>
              <button
                type="button"
                @click="onCancel"
                :disabled="state.loading"
                class="btn-outline mt-3 w-full sm:mt-0 sm:w-auto sm:ml-3 px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ state.cancelText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, nextTick, onMounted, onUnmounted } from 'vue'
import { deleteConfirmationState, handleConfirm, handleCancel } from '@/composables/useDeleteConfirmation'

// Use reactive state from composable
const state = deleteConfirmationState

// Handle keyboard events for accessibility
let previousActiveElement = null

watch(() => state.show, (newValue) => {
  if (newValue) {
    // Store the previously focused element
    previousActiveElement = document.activeElement
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden'
    
    // Focus the confirm button after modal is rendered
    nextTick(() => {
      const confirmButton = document.querySelector('[aria-modal="true"] button.btn-danger')
      if (confirmButton) {
        confirmButton.focus()
      }
    })
  } else {
    // Restore body scroll
    document.body.style.overflow = ''
    // Restore focus to previous element
    if (previousActiveElement) {
      previousActiveElement.focus()
    }
  }
})

const onConfirm = () => {
  if (!state.loading) {
    handleConfirm()
  }
}

const onCancel = () => {
  if (!state.loading) {
    handleCancel()
  }
}

// Handle Escape key
const handleEscape = (event) => {
  if (event.key === 'Escape' && state.show && !state.loading) {
    onCancel()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  // Clean up body overflow
  document.body.style.overflow = ''
})
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
  animation: fade-in 0.3s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>

