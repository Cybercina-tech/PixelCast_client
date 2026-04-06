<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h1 class="text-2xl font-bold text-primary">Active Sessions</h1>
        <p class="text-muted mt-1">View and manage your active login sessions</p>
      </div>

      <Card :title="`Active Sessions (${sessions.length})`">
        <div v-if="loading" class="flex items-center justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
        </div>
        <div v-else-if="error" class="bg-error/10 border border-error/20 rounded-lg p-4">
          <p class="text-error text-sm break-words">{{ error }}</p>
        </div>
        <div v-else-if="sessions.length === 0" class="text-center py-8 text-muted">
          <p>No active sessions found</p>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="flex items-center justify-between p-4 bg-card border border-border-color rounded-lg"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <p class="font-medium text-primary">{{ session.device || 'Unknown Device' }}</p>
                <span v-if="session.current" class="px-2 py-0.5 bg-brand/20 text-brand text-xs rounded">Current</span>
              </div>
              <p class="text-sm text-secondary">IP Address: {{ session.ip_address }}</p>
              <p class="text-xs text-muted mt-1">Last activity: {{ formatDate(session.last_activity) }}</p>
            </div>
            <button
              v-if="!session.current"
              @click="handleTerminateSession(session.id)"
              class="px-3 py-1.5 text-sm text-error hover:bg-error/10 rounded transition-colors"
              :disabled="terminatingSession === session.id"
            >
              <span v-if="terminatingSession === session.id">Terminating...</span>
              <span v-else>Terminate</span>
            </button>
          </div>
        </div>
        
        <div v-if="sessions.length > 0" class="mt-6 pt-6 border-t border-border-color">
          <div class="bg-card border border-border-color rounded-lg p-4">
            <h3 class="font-medium text-primary mb-2">Danger Zone</h3>
            <p class="text-sm text-secondary mb-4">Log out from all devices. You'll need to log in again on all devices.</p>
            <button
              @click="showLogoutAllModal = true"
              class="px-4 py-2 bg-error text-white rounded-lg hover:bg-error/90 transition-colors"
              :disabled="loggingOutAll"
            >
              <span v-if="loggingOutAll">Logging out...</span>
              <span v-else>Logout from All Sessions</span>
            </button>
          </div>
        </div>
      </Card>

      <!-- Logout All Confirmation Modal -->
      <Modal
        :show="showLogoutAllModal"
        title="Logout from All Sessions"
        @close="showLogoutAllModal = false"
        @confirm="handleLogoutAll"
      >
        <p class="text-secondary">
          Are you sure you want to log out from all sessions? You will need to log in again on all devices.
        </p>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotification } from '@/composables/useNotification'
import { authAPI } from '@/services/api'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'

const router = useRouter()
const authStore = useAuthStore()
const notify = useNotification()

const loading = ref(true)
const error = ref(null)
const loggingOutAll = ref(false)
const terminatingSession = ref(null)
const sessions = ref([])
const showLogoutAllModal = ref(false)

const loadSessions = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await authAPI.sessions()
    sessions.value = response.data.sessions || []
  } catch (err) {
    error.value = err.response?.data?.detail || err.response?.data?.error || 'Failed to load sessions'
    console.error('Failed to load sessions:', err)
  } finally {
    loading.value = false
  }
}

const handleTerminateSession = async (sessionId) => {
  terminatingSession.value = sessionId
  try {
    const oid = parseInt(sessionId, 10)
    await authAPI.revokeSession(Number.isFinite(oid) ? oid : sessionId)
    notify.success('Session revoked')
    await loadSessions()
  } catch (err) {
    notify.error(err.response?.data?.error || err.response?.data?.detail || 'Could not revoke session')
  } finally {
    terminatingSession.value = null
  }
}

const handleLogoutAll = async () => {
  loggingOutAll.value = true
  try {
    await authAPI.logoutAll()
    notify.success('Logged out from all sessions')
    
    // Clear auth state and redirect to login
    authStore.logout()
    router.push('/login')
  } catch (err) {
    const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Failed to logout from all sessions'
    notify.error(errorMessage)
  } finally {
    loggingOutAll.value = false
    showLogoutAllModal.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Never'
  try {
    const date = new Date(dateString)
    return date.toLocaleString()
  } catch {
    return dateString
  }
}

onMounted(() => {
  loadSessions()
})
</script>
