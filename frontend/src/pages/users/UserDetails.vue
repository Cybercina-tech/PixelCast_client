<template>
  <AppLayout>
    <div class="space-y-6">
      <router-link
        :to="{ name: 'users' }"
        class="btn-outline inline-flex w-fit items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:-translate-x-0.5"
        title="Back to Team management"
      >
        <ArrowLeftIcon class="w-5 h-5 shrink-0" aria-hidden="true" />
        Back to Team management
      </router-link>

      <div v-if="usersStore.loading" class="text-center py-8">Loading...</div>
      <div v-else-if="user" class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-primary">{{ user.full_name || user.username }}</h1>
          <p class="text-secondary">{{ user.email }}</p>
        </div>
        <button
          @click="showPasswordModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Change Password
        </button>
      </div>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Profile Information">
          <dl class="space-y-3">
            <div>
              <dt class="text-sm font-medium text-muted">Username</dt>
              <dd class="mt-1 text-sm text-primary">{{ user.username }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Email</dt>
              <dd class="mt-1 text-sm text-primary">{{ user.email }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Full Name</dt>
              <dd class="mt-1 text-sm text-primary">{{ user.full_name || 'N/A' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Role</dt>
              <dd class="mt-1">
                <span class="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded text-xs capitalize">
                  {{ user.role }}
                </span>
              </dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Organization</dt>
              <dd class="mt-1 text-sm text-primary">{{ user.organization_name || 'N/A' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Last Login</dt>
              <dd class="mt-1 text-sm text-primary">{{ formatDate(user.last_login) }}</dd>
            </div>
          </dl>
        </Card>
        
        <Card title="Access & Permissions">
          <div class="space-y-2">
            <div v-if="user.role === 'Developer'" class="p-2 bg-green-50 dark:bg-green-900/20 rounded text-primary">
              Full system access (settings, logs, team, content)
            </div>
            <div v-else-if="user.role === 'Manager'" class="p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-primary">
              Manage Employees, screens, and content; no system settings
            </div>
            <div v-else-if="user.role === 'Employee'" class="p-2 bg-gray-50 dark:bg-gray-800 rounded text-primary">
              Screens, playlists, and media library
            </div>
            <div v-else-if="user.role === 'Visitor'" class="p-2 bg-slate-50 dark:bg-slate-900/40 rounded text-primary">
              Dashboard and template exploration only; changes are not saved
            </div>
            <div v-else class="p-2 bg-gray-50 dark:bg-gray-800 rounded text-primary">
              {{ user.role }}
            </div>
          </div>
        </Card>
      </div>
      
      <Card title="Recent Activities">
        <div class="space-y-2">
          <div
            v-for="activity in recentActivities"
            :key="activity.id"
            class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <p class="text-sm text-primary">{{ activity.message || activity.type }}</p>
            <p class="text-xs text-muted mt-1">{{ formatDate(activity.timestamp || activity.created_at) }}</p>
          </div>
          <div v-if="!recentActivities || recentActivities.length === 0" class="text-center text-muted py-4">
            No recent activities
          </div>
        </div>
      </Card>
      
      <Modal :show="showPasswordModal" title="Change Password" @close="showPasswordModal = false">
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">Old Password</label>
            <input v-model="passwordForm.old_password" type="password" required class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">New Password</label>
            <input v-model="passwordForm.new_password" type="password" required class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Confirm New Password</label>
            <input v-model="passwordForm.new_password_confirm" type="password" required class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handlePasswordChange" class="btn-primary px-4 py-2 rounded-lg">
            Change Password
          </button>
          <button type="button" @click="showPasswordModal = false" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUsersStore } from '@/stores/users'
import { useNotification } from '@/composables/useNotification'
import { ArrowLeftIcon } from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Modal from '@/components/common/Modal.vue'

const route = useRoute()
const usersStore = useUsersStore()
const notify = useNotification()

const user = computed(() => usersStore.currentUser)
const recentActivities = ref([])
const showPasswordModal = ref(false)

const passwordForm = ref({
  old_password: '',
  new_password: '',
  new_password_confirm: '',
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const handlePasswordChange = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.new_password_confirm) {
    notify.error('New passwords do not match')
    return
  }
  
  if (!passwordForm.value.old_password) {
    notify.error('Old password is required')
    return
  }
  
  if (!passwordForm.value.new_password) {
    notify.error('New password is required')
    return
  }
  
  try {
    await usersStore.changePassword(user.value.id, {
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
      new_password_confirm: passwordForm.value.new_password_confirm,
    })
    notify.success('Password changed successfully')
    showPasswordModal.value = false
    passwordForm.value = { old_password: '', new_password: '', new_password_confirm: '' }
  } catch (error) {
    notify.error(error.response?.data?.detail || error.response?.data?.message || 'Failed to change password')
  }
}

onMounted(async () => {
  const userId = route.params.id
  await usersStore.fetchUser(userId)
  // In a real app, you'd fetch recent activities from logs or a separate endpoint
})
</script>
