<template>
  <AppLayout>
    <div class="min-h-screen flex items-center justify-center px-4">
      <div class="text-center">
        <ExclamationTriangleIcon class="mx-auto h-24 w-24 text-yellow-400" />
        <h1 class="text-6xl font-bold text-gray-300 mt-4">401</h1>
        <h2 class="text-3xl font-bold text-gray-900 mt-4">Unauthorized</h2>
        <p class="text-gray-600 mt-4 mb-8">
          You need to be authenticated to access this page.
        </p>
        <router-link
          to="/login"
          class="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          Go to Login
        </router-link>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'
</script>
