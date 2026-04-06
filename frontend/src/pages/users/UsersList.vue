<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-primary">Team management</h1>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          Create User
        </button>
      </div>
      
      <Card>
        <div v-if="usersStore.loading" class="text-center py-8">Loading...</div>
        <div v-else-if="usersStore.error" class="text-center py-8 text-red-600">
          {{ usersStore.error }}
        </div>
        <Table
          v-else
          :columns="columns"
          :data="usersStore.users"
          :actions="['view', 'edit', 'delete']"
          @view="handleView"
          @edit="handleEdit"
          @delete="handleDelete"
        >
          <template #cell-role="{ value }">
            <span class="badge-primary px-2 py-1 rounded text-xs capitalize">{{ value }}</span>
          </template>
          <template #actions="{ row }">
            <div class="flex items-center justify-end gap-1">
              <router-link
                :to="`/users/${row.id}`"
                class="action-btn-view"
                title="View"
              >
                <EyeIcon class="w-4 h-4" />
              </router-link>
              <button
                @click="handleEdit(row)"
                class="action-btn-edit"
                title="Edit"
              >
                <PencilIcon class="w-4 h-4" />
              </button>
              <button
                v-if="isDeveloper"
                @click="handleChangeRole(row)"
                class="action-btn-role"
                title="Change Role"
              >
                <ShieldCheckIcon class="w-4 h-4" />
              </button>
              <button
                v-if="isDeveloper"
                @click="openPasswordModal(row)"
                class="action-btn-role"
                title="Set Password"
              >
                <KeyIcon class="w-4 h-4" />
              </button>
              <button
                @click="handleDelete(row)"
                class="action-btn-delete"
                title="Delete"
              >
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </template>
        </Table>
      </Card>
      
      <!-- Create/Edit Modal -->
      <Modal
        :show="showCreateModal || showEditModal"
        :title="showEditModal ? 'Edit User' : 'Create User'"
        @close="closeModal"
      >
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">Username</label>
            <input v-model="form.username" type="text" required class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Email</label>
            <input v-model="form.email" type="email" required class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Full Name</label>
            <input v-model="form.full_name" type="text" class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div v-if="!showEditModal">
            <label class="label-base block text-sm mb-1">Password</label>
            <input v-model="form.password" type="password" required class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Role</label>
            <select v-model="form.role" class="select-base w-full px-3 py-2 rounded-lg">
              <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Organization</label>
            <input v-model="form.organization_name" type="text" class="input-base w-full px-3 py-2 rounded-lg" />
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleSubmit" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            {{ showEditModal ? 'Update' : 'Create' }}
          </button>
          <button type="button" @click="closeModal" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
      
      <!-- Change Role Modal -->
      <Modal :show="showRoleModal" title="Change Role" @close="showRoleModal = false">
        <div class="space-y-4">
          <div>
            <label class="label-base block text-sm mb-1">New Role</label>
            <select v-model="roleForm.role" required class="select-base w-full px-3 py-2 rounded-lg">
              <option v-for="opt in changeRoleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
        </div>
        <template #footer>
          <button type="button" @click="handleRoleSubmit" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            Change Role
          </button>
          <button type="button" @click="showRoleModal = false" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>

      <Modal :show="showPasswordModal" title="Set User Password" @close="closePasswordModal">
        <div class="space-y-4">
          <p class="text-xs text-muted">
            {{ passwordTargetUser ? `User: ${passwordTargetUser.username} (${passwordTargetUser.email})` : '' }}
          </p>
          <div>
            <label class="label-base block text-sm mb-1">New Password</label>
            <input
              v-model="passwordForm.new_password"
              :type="passwordForm.showPlain ? 'text' : 'password'"
              required
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Confirm Password</label>
            <input
              v-model="passwordForm.confirm_password"
              :type="passwordForm.showPlain ? 'text' : 'password'"
              required
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="btn-outline px-3 py-1.5 rounded-lg text-xs" @click="passwordForm.showPlain = !passwordForm.showPlain">
              {{ passwordForm.showPlain ? 'Hide' : 'Show' }}
            </button>
            <button type="button" class="btn-outline px-3 py-1.5 rounded-lg text-xs" @click="generateStrongPassword">
              Generate strong
            </button>
          </div>
          <p class="text-xs text-muted">
            Current password cannot be viewed because it is stored hashed on the server. Use this form to set any new password.
          </p>
        </div>
        <template #footer>
          <button type="button" @click="submitPasswordReset" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700" :disabled="savingPassword">
            {{ savingPassword ? 'Saving...' : 'Save Password' }}
          </button>
          <button type="button" @click="closePasswordModal" class="btn-outline px-4 py-2 rounded-lg">
            Cancel
          </button>
        </template>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { EyeIcon, PencilIcon, TrashIcon, ShieldCheckIcon, KeyIcon } from '@heroicons/vue/24/outline'
import { useUsersStore } from '@/stores/users'
import { useNotification } from '@/composables/useNotification'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import Table from '@/components/common/Table.vue'
import Modal from '@/components/common/Modal.vue'
import { isDeveloperOrSuperuser } from '@/utils/permissions'
import { usersAPI } from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const usersStore = useUsersStore()
const notify = useNotification()

const isDeveloper = computed(() => isDeveloperOrSuperuser(authStore.user))

const roleOptions = computed(() => {
  if (isDeveloperOrSuperuser(authStore.user)) {
    return [
      { value: 'Developer', label: 'Developer' },
      { value: 'Manager', label: 'Manager' },
      { value: 'Employee', label: 'Employee' },
      { value: 'Visitor', label: 'Visitor' },
    ]
  }
  return [
    { value: 'Employee', label: 'Employee' },
    { value: 'Visitor', label: 'Visitor' },
  ]
})

const changeRoleOptions = [
  { value: 'Developer', label: 'Developer' },
  { value: 'Manager', label: 'Manager' },
  { value: 'Employee', label: 'Employee' },
  { value: 'Visitor', label: 'Visitor' },
]

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showRoleModal = ref(false)
const showPasswordModal = ref(false)
const editingUser = ref(null)
const roleChangingUser = ref(null)
const passwordTargetUser = ref(null)
const savingPassword = ref(false)

const form = ref({
  username: '',
  email: '',
  full_name: '',
  password: '',
  role: 'Employee',
  organization_name: '',
})

const roleForm = ref({
  role: 'Employee',
})

const passwordForm = ref({
  new_password: '',
  confirm_password: '',
  showPlain: false,
})

const columns = [
  { key: 'username', label: 'Username' },
  { key: 'email', label: 'Email' },
  { key: 'full_name', label: 'Full Name' },
  { key: 'role', label: 'Role' },
  { key: 'organization_name', label: 'Organization' },
]

const handleView = (row) => {
  router.push(`/users/${row.id}`)
}

const handleEdit = (row) => {
  editingUser.value = row
  form.value = {
    username: row.username || '',
    email: row.email || '',
    full_name: row.full_name || '',
    password: '',
    role: row.role || 'Employee',
    organization_name: row.organization_name || '',
  }
  showEditModal.value = true
}

const handleChangeRole = (row) => {
  roleChangingUser.value = row
  roleForm.value.role = row.role || 'Employee'
  showRoleModal.value = true
}

const openPasswordModal = (row) => {
  passwordTargetUser.value = row
  passwordForm.value = {
    new_password: '',
    confirm_password: '',
    showPlain: false,
  }
  showPasswordModal.value = true
}

const closePasswordModal = () => {
  showPasswordModal.value = false
  passwordTargetUser.value = null
  savingPassword.value = false
}

const generateStrongPassword = () => {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*'
  const length = 16
  let generated = ''
  for (let i = 0; i < length; i += 1) {
    generated += alphabet[Math.floor(Math.random() * alphabet.length)]
  }
  passwordForm.value.new_password = generated
  passwordForm.value.confirm_password = generated
  passwordForm.value.showPlain = true
}

const submitPasswordReset = async () => {
  if (!passwordTargetUser.value?.id) return
  const pwd = (passwordForm.value.new_password || '').trim()
  const confirm = passwordForm.value.confirm_password || ''
  if (!pwd) {
    notify.error('New password is required')
    return
  }
  if (pwd !== confirm) {
    notify.error('Password confirmation does not match')
    return
  }

  savingPassword.value = true
  try {
    await usersAPI.adminSetPassword(passwordTargetUser.value.id, { new_password: pwd })
    notify.success('Password updated and sessions revoked')
    closePasswordModal()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Password update failed'
    notify.error(errorMsg)
  } finally {
    savingPassword.value = false
  }
}

const handleDelete = async (row) => {
  try {
    const { confirmDelete } = useDeleteConfirmation()
    await confirmDelete(
      row.id,
      async () => {
        await usersStore.deleteUser(row.id)
      },
      {
        title: 'Delete User?',
        message: 'This will permanently delete the user account and all associated data. This action cannot be undone.',
        itemName: row.username,
        confirmText: 'Yes, Delete User',
        cancelText: 'Cancel'
      }
    )
    notify.success('User deleted successfully')
  } catch (error) {
    if (error.message !== 'Delete cancelled') {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to delete user'
      notify.error(errorMsg)
    }
  }
}

const handleSubmit = async () => {
  try {
    if (showEditModal.value) {
      const updateData = { ...form.value }
      delete updateData.password // Don't send password if empty
      if (!updateData.password) {
        delete updateData.password
      }
      await usersStore.updateUser(editingUser.value.id, updateData)
      notify.success('User updated')
    } else {
      await usersStore.createUser(form.value)
      notify.success('User created')
    }
    closeModal()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Operation failed'
    notify.error(errorMsg)
  }
}

const handleRoleSubmit = async () => {
  try {
    await usersStore.changeRole(roleChangingUser.value.id, roleForm.value.role)
    notify.success('Role changed')
    showRoleModal.value = false
    roleChangingUser.value = null
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to change role'
    notify.error(errorMsg)
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingUser.value = null
  form.value = {
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'Employee',
    organization_name: '',
  }
}

onMounted(async () => {
  await usersStore.fetchUsers()
})
</script>
