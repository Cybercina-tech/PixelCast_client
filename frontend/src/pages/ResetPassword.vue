<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 bg-slate-950 text-white">
    <div class="w-full max-w-md space-y-6">
      <h1 class="text-2xl font-bold">Set new password</h1>
      <form class="space-y-4" @submit.prevent="submit">
        <div>
          <label class="block text-sm mb-1">New password</label>
          <input
            v-model="pw"
            type="password"
            required
            minlength="8"
            class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700"
          />
        </div>
        <div>
          <label class="block text-sm mb-1">Confirm</label>
          <input
            v-model="pw2"
            type="password"
            required
            class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700"
          />
        </div>
        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
        >
          {{ loading ? 'Saving…' : 'Update password' }}
        </button>
      </form>
      <router-link to="/login" class="text-indigo-400 text-sm">Back to login</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI } from '@/services/api'

const route = useRoute()
const router = useRouter()
const uid = ref('')
const token = ref('')
const pw = ref('')
const pw2 = ref('')
const loading = ref(false)
const error = ref('')

onMounted(() => {
  uid.value = route.query.uid || ''
  token.value = route.query.token || ''
})

async function submit() {
  error.value = ''
  if (pw.value !== pw2.value) {
    error.value = 'Passwords do not match'
    return
  }
  loading.value = true
  try {
    await authAPI.passwordResetConfirm({
      uid: uid.value,
      token: token.value,
      new_password: pw.value,
      new_password_confirm: pw2.value,
    })
    router.push('/login')
  } catch (e) {
    error.value = e.response?.data?.error || 'Reset failed'
  } finally {
    loading.value = false
  }
}
</script>
