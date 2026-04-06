<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="$emit('close')"
        role="dialog"
        aria-modal="true"
        aria-labelledby="push-to-screen-title"
      >
        <!-- Backdrop -->
        <div
          class="fixed inset-0 transition-opacity bg-black/50 dark:bg-black/70 backdrop-blur-sm"
          aria-hidden="true"
        ></div>
        
        <!-- Modal Container -->
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
          
          <div
            class="inline-block align-bottom bg-gray-800/95 backdrop-blur-lg rounded-2xl text-left overflow-hidden shadow-2xl border border-white/10 transform transition-all duration-300 sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full"
          >
            <!-- Header -->
            <div class="bg-gradient-to-r from-purple-600/20 to-indigo-600/20 border-b border-white/10 px-6 py-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-purple-600/20 flex items-center justify-center">
                    <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 id="push-to-screen-title" class="text-xl font-semibold text-white">
                      Push Template to Screen
                    </h3>
                    <p class="text-sm text-gray-400 mt-0.5">Select an online screen to push this template</p>
                  </div>
                </div>
                <button
                  @click="$emit('close')"
                  class="text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/10"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Content -->
            <div class="px-6 py-6">
              <!-- Template Info -->
              <div class="mb-6 p-4 bg-gray-900/50 rounded-lg border border-white/5">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-lg bg-indigo-600/20 flex items-center justify-center">
                    <svg class="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-medium text-white truncate">{{ template?.name || 'Template' }}</h4>
                    <p class="text-xs text-gray-400 mt-0.5">
                      {{ template?.width }}×{{ template?.height }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Search -->
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-300 mb-2">Search Screens</label>
                <div class="relative">
                  <svg
                    class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="Search by name, device ID, or location..."
                    class="w-full pl-10 pr-4 py-2.5 bg-gray-900/50 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all"
                  />
                </div>
              </div>

              <!-- Screen List -->
              <div class="max-h-96 overflow-y-auto custom-scrollbar space-y-2">
                <div v-if="filteredOnlineScreens.length === 0" class="text-center py-12">
                  <svg class="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <p class="text-gray-400">
                    {{ searchQuery ? 'No online screens match your search' : 'No online screens available' }}
                  </p>
                </div>
                
                <button
                  v-for="screen in filteredOnlineScreens"
                  :key="screen.id"
                  @click="handleSelectScreen(screen)"
                  :disabled="loading"
                  class="w-full p-4 bg-gray-900/50 hover:bg-gray-900 border border-white/5 hover:border-purple-500/50 rounded-lg transition-all duration-200 text-left group"
                  :class="{ 'opacity-50 cursor-not-allowed': loading }"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3 flex-1 min-w-0">
                      <!-- Online Indicator -->
                      <div class="flex-shrink-0">
                        <div class="w-3 h-3 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
                      </div>
                      
                      <!-- Screen Info -->
                      <div class="flex-1 min-w-0">
                        <h4 class="text-sm font-semibold text-white truncate group-hover:text-purple-400 transition-colors">
                          {{ screen.name || 'Unnamed Screen' }}
                        </h4>
                        <div class="flex items-center gap-3 mt-1">
                          <p class="text-xs text-gray-400 font-mono">{{ screen.device_id }}</p>
                          <span class="text-xs text-gray-500">•</span>
                          <p class="text-xs text-gray-400">
                            {{ screen.screen_width }}×{{ screen.screen_height }}
                          </p>
                        </div>
                        <p v-if="screen.location" class="text-xs text-gray-500 mt-1 truncate">
                          {{ screen.location }}
                        </p>
                      </div>
                    </div>
                    
                    <!-- Arrow Icon -->
                    <div class="flex-shrink-0 ml-4">
                      <svg
                        class="w-5 h-5 text-gray-400 group-hover:text-purple-400 group-hover:translate-x-1 transition-all"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <!-- Footer -->
            <div class="bg-gray-900/50 border-t border-white/10 px-6 py-4 flex items-center justify-between">
              <div v-if="loading" class="flex items-center gap-2 text-sm text-blue-400">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span>Pushing template to screen...</span>
              </div>
              <div v-else class="flex-1"></div>
              <button
                @click="$emit('close')"
                :disabled="loading"
                class="px-4 py-2 text-gray-300 hover:text-white transition-colors rounded-lg hover:bg-white/10 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  template: {
    type: Object,
    default: null,
  },
  onlineScreens: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'select'])

const searchQuery = ref('')

const filteredOnlineScreens = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.onlineScreens
  }
  
  const query = searchQuery.value.toLowerCase()
  return props.onlineScreens.filter(screen => {
    const name = (screen.name || '').toLowerCase()
    const deviceId = (screen.device_id || '').toLowerCase()
    const location = (screen.location || '').toLowerCase()
    
    return name.includes(query) || deviceId.includes(query) || location.includes(query)
  })
})

const handleSelectScreen = (screen) => {
  if (!props.loading) {
    emit('select', screen)
  }
}
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

