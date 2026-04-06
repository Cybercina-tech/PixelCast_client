<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h1 class="text-2xl font-bold text-primary">Profile</h1>
        <p class="text-muted mt-1">Manage your account information and preferences</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-error/10 border border-error/20 rounded-lg p-4">
        <p class="text-error text-sm break-words">{{ error }}</p>
      </div>

      <!-- Profile Content -->
      <div v-else class="space-y-6">
        <!-- Profile Information Section -->
        <Card title="Profile Information">
          <form @submit.prevent="handleUpdateProfile" class="space-y-4">
            <div class="grid md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-secondary mb-1">Username</label>
                <input
                  v-model="profileForm.username"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-border-color rounded-lg bg-card text-primary placeholder:text-muted"
                  placeholder="Username"
                />
                <p class="mt-1 text-xs text-muted">Your unique username</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-secondary mb-1">Email</label>
                <input
                  v-model="profileForm.email"
                  type="email"
                  required
                  class="w-full px-3 py-2 border border-border-color rounded-lg bg-card text-primary placeholder:text-muted"
                  placeholder="email@example.com"
                />
                <div class="mt-1 flex items-center gap-2">
                  <p class="text-xs text-muted">Your email address</p>
                  <span v-if="!userData.is_email_verified" class="badge-error px-2 py-0.5 rounded text-xs font-medium">
                    Email not verified
                  </span>
                  <span v-else class="badge-success px-2 py-0.5 rounded text-xs font-medium">
                    Verified
                  </span>
                </div>
              </div>
            </div>

            <div class="grid md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-secondary mb-1">Full Name</label>
                <input
                  v-model="profileForm.full_name"
                  type="text"
                  class="w-full px-3 py-2 border border-border-color rounded-lg bg-card text-primary placeholder:text-muted"
                  placeholder="Your full name"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-secondary mb-1">Phone Number</label>
                <input
                  v-model="profileForm.phone_number"
                  type="tel"
                  class="w-full px-3 py-2 border border-border-color rounded-lg bg-card text-primary placeholder:text-muted"
                  placeholder="+1234567890"
                />
              </div>
            </div>

            <!-- Email Verification Section -->
            <div v-if="!userData.is_email_verified" class="p-4 bg-warning/10 border border-warning/20 rounded-lg">
              <p class="text-sm text-primary mb-3">Your email address is not verified.</p>
              
              <div v-if="!showCodeInput" class="flex items-center gap-3">
                <button
                  @click="sendVerificationCode"
                  :disabled="loadingSend"
                  class="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <span v-if="loadingSend" class="flex items-center gap-2">
                    <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Sending...
                  </span>
                  <span v-else>Send Verification Code</span>
                </button>
              </div>
              
              <div v-else class="space-y-3">
                <div class="flex flex-col sm:flex-row gap-2">
                  <input
                    ref="codeInputRef"
                    v-model="verificationCode"
                    type="text"
                    inputmode="numeric"
                    maxlength="6"
                    placeholder="Enter 6-digit code"
                    aria-label="Verification code"
                    class="flex-1 px-3 py-2 border border-border-color rounded-lg bg-card text-primary placeholder:text-muted"
                    @keyup.enter="verifyEmail"
                  />
                  <button
                    @click="verifyEmail"
                    :disabled="!verificationCode || verificationCode.length !== 6 || loadingVerify"
                    class="px-4 py-2 bg-success text-white rounded-lg hover:bg-success/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <span v-if="loadingVerify" class="flex items-center gap-2">
                      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Verifying...
                    </span>
                    <span v-else>Verify</span>
                  </button>
                </div>
                
                <div class="flex items-center gap-3">
                  <button
                    @click="sendVerificationCode"
                    :disabled="loadingSend || canResend === false"
                    class="text-sm text-primary hover:text-brand-hover hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
                  >
                    {{ canResend === false ? `Resend code in ${resendCountdown}s` : 'Resend Code' }}
                  </button>
                </div>
                
                <p v-if="verificationError" class="text-error text-sm whitespace-pre-line break-words">{{ verificationError }}</p>
                <p v-if="verificationSuccess" class="text-success text-sm">{{ verificationSuccess }}</p>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-secondary mb-1">Organization</label>
              <input
                v-model="profileForm.organization_name"
                type="text"
                disabled
                class="w-full px-3 py-2 border border-border-color rounded-lg bg-card text-muted cursor-not-allowed"
              />
              <p class="mt-1 text-xs text-muted">Organization cannot be changed</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-secondary mb-1">Role</label>
              <input
                :value="profileForm.role_display || profileForm.role"
                type="text"
                disabled
                class="w-full px-3 py-2 border border-border-color rounded-lg bg-card text-muted cursor-not-allowed"
              />
              <p class="mt-1 text-xs text-muted">Role cannot be changed</p>
            </div>

            <div class="flex justify-end gap-3 pt-4">
              <button
                type="button"
                @click="resetProfileForm"
                class="px-4 py-2 border border-border-color rounded-lg text-secondary hover:bg-card transition-colors"
                :disabled="saving"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors"
                :disabled="saving"
              >
                <span v-if="saving">Saving...</span>
                <span v-else>Save Changes</span>
              </button>
            </div>
          </form>
        </Card>

        <!-- Account Statistics -->
        <Card title="Account Statistics">
          <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-card border border-border-color rounded-lg p-4">
              <p class="text-sm text-muted">Total Screens</p>
              <p class="text-2xl font-bold text-primary mt-1">{{ userData.total_screens_count || 0 }}</p>
            </div>
            <div class="bg-card border border-border-color rounded-lg p-4">
              <p class="text-sm text-muted">Active Screens</p>
              <p class="text-2xl font-bold text-primary mt-1">{{ userData.active_screens_count || 0 }}</p>
            </div>
            <div class="bg-card border border-border-color rounded-lg p-4">
              <p class="text-sm text-muted">Total Templates</p>
              <p class="text-2xl font-bold text-primary mt-1">{{ userData.total_templates_count || 0 }}</p>
            </div>
            <div class="bg-card border border-border-color rounded-lg p-4">
              <p class="text-sm text-muted">Active Templates</p>
              <p class="text-2xl font-bold text-primary mt-1">{{ userData.active_templates_count || 0 }}</p>
            </div>
          </div>
        </Card>

        <!-- Account Information -->
        <Card title="Account Information">
          <div class="space-y-3">
            <div class="flex justify-between items-center py-2 border-b border-border-color">
              <span class="text-secondary">Account Created</span>
              <span class="text-primary font-medium">{{ formatDate(userData.date_joined) }}</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-border-color">
              <span class="text-secondary">Last Seen</span>
              <span class="text-primary font-medium">{{ formatDate(userData.last_seen) }}</span>
            </div>
            <div class="flex justify-between items-center py-2">
              <span class="text-secondary">Account Status</span>
              <span class="px-2 py-1 rounded text-xs font-medium" :class="userData.is_active ? 'bg-success/20 text-success' : 'bg-error/20 text-error'">
                {{ userData.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
          </div>
        </Card>

        <!-- Activity Logs -->
        <Card title="Recent Activity">
          <div v-if="loadingLogs" class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
          </div>
          <div v-else-if="logsError" class="bg-error/10 border border-error/20 rounded-lg p-4">
            <p class="text-error text-sm whitespace-pre-line break-words">{{ logsError }}</p>
          </div>
          <div v-else-if="activityLogs.length === 0" class="text-center py-8 text-muted">
            <p>No activity logs found</p>
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="log in activityLogs"
              :key="log.id"
              class="flex items-start gap-3 p-3 bg-card border border-border-color rounded-lg"
            >
              <div class="flex-shrink-0 w-2 h-2 rounded-full mt-2" :class="{
                'bg-success': log.severity === 'low',
                'bg-warning': log.severity === 'medium',
                'bg-error': log.severity === 'high' || log.severity === 'critical',
              }"></div>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-primary font-medium">{{ log.description }}</p>
                <div class="flex items-center gap-3 mt-1">
                  <span class="text-xs text-muted">{{ formatDate(log.timestamp) }}</span>
                  <span v-if="log.ip_address" class="text-xs text-muted">IP: {{ log.ip_address }}</span>
                </div>
              </div>
            </div>
            <div v-if="hasMoreLogs" class="text-center pt-4">
              <button
                @click="loadMoreLogs"
                class="px-4 py-2 text-sm text-primary hover:bg-card rounded-lg transition-colors"
                :disabled="loadingMoreLogs"
              >
                <span v-if="loadingMoreLogs">Loading...</span>
                <span v-else>Load More</span>
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotification } from '@/composables/useNotification'
import { usersAPI } from '@/services/api'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'

const router = useRouter()
const authStore = useAuthStore()
const notify = useNotification()

const loading = ref(true)
const saving = ref(false)
const error = ref(null)
const loadingLogs = ref(false)
const loadingMoreLogs = ref(false)
const logsError = ref(null)
const userData = ref({})
const activityLogs = ref([])
const currentLogPage = ref(1)
const hasMoreLogs = ref(false)
const verificationCode = ref('')
const showCodeInput = ref(false)
const loadingSend = ref(false)
const loadingVerify = ref(false)
const verificationError = ref(null)
const verificationSuccess = ref(null)
const codeInputRef = ref(null)
const resendCountdown = ref(0)
const resendTimer = ref(null)
const profileForm = ref({
  username: '',
  email: '',
  full_name: '',
  phone_number: '',
  organization_name: '',
  role: '',
  role_display: '',
})

const loadProfile = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await usersAPI.me()
    userData.value = response.data
    profileForm.value = {
      username: response.data.username || '',
      email: response.data.email || '',
      full_name: response.data.full_name || '',
      phone_number: response.data.phone_number || '',
      organization_name: response.data.organization_name || '',
      role: response.data.role || '',
      role_display: response.data.role_display || '',
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.response?.data?.error || 'Failed to load profile'
    console.error('Failed to load profile:', err)
  } finally {
    loading.value = false
  }
}

const handleUpdateProfile = async () => {
  saving.value = true
  error.value = null
  try {
    const updateData = {
      username: profileForm.value.username,
      email: profileForm.value.email,
      full_name: profileForm.value.full_name,
      phone_number: profileForm.value.phone_number,
    }
    
    const response = await usersAPI.updateMe(updateData)
    userData.value = response.data
    
    // Update auth store
    if (authStore.user) {
      authStore.user = { ...authStore.user, ...response.data }
    }
    
    notify.success('Profile updated successfully')
  } catch (err) {
    const errorData = err.response?.data
    if (errorData) {
      // Handle field-specific errors
      const errorMessages = []
      for (const [field, messages] of Object.entries(errorData)) {
        if (Array.isArray(messages)) {
          errorMessages.push(`${field}: ${messages.join(', ')}`)
        } else {
          errorMessages.push(`${field}: ${messages}`)
        }
      }
      error.value = errorMessages.join('; ') || 'Failed to update profile'
    } else {
      error.value = err.message || 'Failed to update profile'
    }
    notify.error(error.value)
  } finally {
    saving.value = false
  }
}

const resetProfileForm = () => {
  profileForm.value = {
    username: userData.value.username || '',
    email: userData.value.email || '',
    full_name: userData.value.full_name || '',
    phone_number: userData.value.phone_number || '',
    organization_name: userData.value.organization_name || '',
    role: userData.value.role || '',
    role_display: userData.value.role_display || '',
  }
}

const loadActivityLogs = async (page = 1) => {
  if (page === 1) {
    loadingLogs.value = true
  } else {
    loadingMoreLogs.value = true
  }
  logsError.value = null
  try {
    const response = await usersAPI.activityLogs({ page, page_size: 10 })
    if (page === 1) {
      activityLogs.value = response.data.results || []
    } else {
      activityLogs.value.push(...(response.data.results || []))
    }
    currentLogPage.value = page
    hasMoreLogs.value = page < response.data.pages
  } catch (err) {
    logsError.value = err.response?.data?.detail || err.response?.data?.error || 'Failed to load activity logs'
    console.error('Failed to load activity logs:', err)
  } finally {
    loadingLogs.value = false
    loadingMoreLogs.value = false
  }
}

const loadMoreLogs = () => {
  loadActivityLogs(currentLogPage.value + 1)
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

const canResend = computed(() => resendCountdown.value === 0)

const sendVerificationCode = async () => {
  loadingSend.value = true
  verificationError.value = null
  verificationSuccess.value = null
  
  try {
    await usersAPI.sendVerificationEmail()
    notify.success('Code sent to your email!')
    showCodeInput.value = true
    verificationCode.value = ''
    
    // Start resend countdown (60 seconds)
    resendCountdown.value = 60
    if (resendTimer.value) {
      clearInterval(resendTimer.value)
    }
    resendTimer.value = setInterval(() => {
      resendCountdown.value--
      if (resendCountdown.value <= 0) {
        clearInterval(resendTimer.value)
        resendTimer.value = null
      }
    }, 1000)
    
    // Focus input field after sending
    await nextTick()
    if (codeInputRef.value) {
      codeInputRef.value.focus()
    }
  } catch (err) {
    const errorMessage = err.response?.data?.message || err.response?.data?.error || 'Failed to send verification code'
    verificationError.value = errorMessage
    notify.error(errorMessage)
  } finally {
    loadingSend.value = false
  }
}

const verifyEmail = async () => {
  if (!verificationCode.value || verificationCode.value.length !== 6) {
    verificationError.value = 'Please enter a valid 6-digit code'
    return
  }
  
  loadingVerify.value = true
  verificationError.value = null
  verificationSuccess.value = null
  
  try {
    await usersAPI.verifyEmail({ code: verificationCode.value })
    notify.success('Email verified successfully!')
    
    // Clear verification state
    verificationCode.value = ''
    showCodeInput.value = false
    if (resendTimer.value) {
      clearInterval(resendTimer.value)
      resendTimer.value = null
    }
    resendCountdown.value = 0
    
    // Refresh user data to update verification status
    await loadProfile()
    
    // Update auth store
    await authStore.fetchMe()
  } catch (err) {
    const errorMessage = err.response?.data?.message || err.response?.data?.error || 'Invalid or expired code'
    verificationError.value = errorMessage
    notify.error(errorMessage || 'Invalid or expired code')
  } finally {
    loadingVerify.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadActivityLogs()
})

// Cleanup timer on unmount
onUnmounted(() => {
  if (resendTimer.value) {
    clearInterval(resendTimer.value)
  }
})
</script>
