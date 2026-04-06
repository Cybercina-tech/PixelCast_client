<template>
  <AppLayout>
    <div class="min-h-screen flex items-center justify-center px-4">
      <div class="text-center max-w-2xl">
        <XCircleIcon class="mx-auto h-24 w-24 text-red-400" />
        <h1 class="text-6xl font-bold text-gray-300 mt-4">500</h1>
        <h2 class="text-3xl font-bold text-gray-900 mt-4">Internal Server Error</h2>
        <p class="text-gray-600 mt-4 mb-8">
          Something went wrong on our end. Please try again later or contact support if the problem persists.
        </p>
        <div class="space-x-4">
          <button
            @click="retry"
            class="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Retry
          </button>
          <router-link
            to="/dashboard"
            class="inline-block px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
          >
            Go to Dashboard
          </router-link>
        </div>
        <div v-if="error" class="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg text-left">
          <p class="text-sm font-medium text-red-800">Error Details:</p>
          <p class="text-sm text-red-600 mt-1 break-words">{{ error }}</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { XCircleIcon } from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()
const error = ref(route.query.error || null)

const retry = () => {
  window.location.reload()
}
</script>
