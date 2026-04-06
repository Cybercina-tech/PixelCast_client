<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 bg-slate-950 text-white">
    <div class="w-full max-w-md space-y-6">
      <h1 class="text-2xl font-bold">Forgot password</h1>
      <p class="text-slate-400 text-sm">Enter your email and we will send reset instructions if an account exists.</p>
      <form class="space-y-4" @submit.prevent="submit">
        <div>
          <label class="block text-sm mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
        >
          {{ loading ? 'Sending…' : 'Send reset link' }}
        </button>
      </form>
      <p v-if="message" class="text-emerald-400 text-sm">{{ message }}</p>
      <router-link to="/login" class="text-indigo-400 text-sm">Back to login</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authAPI } from '@/services/api'

const email = ref('')
const loading = ref(false)
const message = ref('')

async function submit() {
  loading.value = true
  message.value = ''
  try {
    const { data } = await authAPI.passwordResetRequest({ email: email.value.trim() })
    message.value = data.message || 'If an account exists, check your email.'
  } catch {
    message.value = 'If an account exists, check your email.'
  } finally {
    loading.value = false
  }
}
</script>
