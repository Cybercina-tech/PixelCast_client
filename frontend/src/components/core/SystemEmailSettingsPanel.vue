<template>
  <div class="space-y-6 max-w-3xl">
    <div v-if="showTitle">
      <h1 class="text-2xl font-bold text-primary">Email / SMTP</h1>
      <p class="text-sm text-secondary mt-1">
        System-wide settings for transactional email (verification codes, etc.). Developer only.
      </p>
    </div>

    <!-- Last test status -->
    <div
      v-if="!loading && (lastTestAt || lastTestOk !== null)"
      class="card-base rounded-2xl p-4 text-sm border border-border-color"
    >
      <p class="font-medium text-primary mb-1">Last test send</p>
      <p v-if="lastTestAt" class="text-muted">
        {{ formatTs(lastTestAt) }}
        —
        <span :class="lastTestOk ? 'text-emerald-600' : 'text-red-500'">
          {{ lastTestOk ? 'Success' : 'Failed' }}
        </span>
        <span v-if="lastTestCode" class="text-muted"> ({{ lastTestCode }})</span>
      </p>
      <p v-if="lastTestDetail && !lastTestOk" class="text-red-600/90 mt-2 break-words">{{ lastTestDetail }}</p>
    </div>

    <div v-if="loading" class="card-base rounded-2xl p-8 text-center text-muted">Loading…</div>

    <form v-else class="card-base rounded-2xl p-6 space-y-5" @submit.prevent="save">
      <div>
        <label class="label-base block text-sm mb-1">Delivery mode</label>
        <select v-model="form.delivery_mode" class="select-base w-full max-w-md px-3 py-2 rounded-lg">
          <option value="console">Console (log only — development)</option>
          <option value="smtp">SMTP</option>
        </select>
      </div>

      <p v-if="clientError" class="text-sm text-red-500">{{ clientError }}</p>

      <template v-if="form.delivery_mode === 'smtp'">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="label-base block text-sm mb-1">SMTP host</label>
            <input
              v-model="form.smtp_host"
              type="text"
              class="input-base w-full px-3 py-2 rounded-lg"
              placeholder="smtp.example.com"
              autocomplete="off"
            />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Port</label>
            <input
              v-model.number="form.smtp_port"
              type="number"
              min="1"
              max="65535"
              class="input-base w-full px-3 py-2 rounded-lg"
            />
          </div>
          <div class="flex flex-col gap-3 justify-end pb-1">
            <label class="inline-flex items-center gap-2 text-sm">
              <input v-model="form.use_tls" type="checkbox" class="rounded" @change="onTlsSslChange('tls')" />
              Use TLS (STARTTLS)
            </label>
            <label class="inline-flex items-center gap-2 text-sm">
              <input v-model="form.use_ssl" type="checkbox" class="rounded" @change="onTlsSslChange('ssl')" />
              Use SSL (implicit TLS, usually port 465)
            </label>
          </div>
          <div class="md:col-span-2">
            <label class="label-base block text-sm mb-1">SMTP username (optional)</label>
            <input
              v-model="form.smtp_username"
              type="text"
              class="input-base w-full px-3 py-2 rounded-lg"
              autocomplete="username"
            />
          </div>
          <div class="md:col-span-2">
            <label class="label-base block text-sm mb-1">SMTP password</label>
            <input
              v-model="form.smtp_password"
              type="password"
              class="input-base w-full px-3 py-2 rounded-lg"
              :placeholder="passwordPlaceholder"
              autocomplete="new-password"
            />
            <p class="text-xs text-muted mt-1">
              Leave blank to keep the current password
              <span v-if="smtpPasswordConfigured"> (password is configured)</span>
            </p>
          </div>
        </div>
      </template>

      <div>
        <label class="label-base block text-sm mb-1">Default “From” address</label>
        <input
          v-model="form.default_from_email"
          type="email"
          class="input-base w-full px-3 py-2 rounded-lg"
          placeholder="no-reply@yourdomain.com"
        />
      </div>

      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
      <p v-if="successMsg" class="text-sm text-emerald-600">{{ successMsg }}</p>

      <div class="flex flex-wrap gap-3">
        <button type="submit" class="btn-primary px-4 py-2 rounded-lg" :disabled="saving">
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
        <button
          type="button"
          class="btn-outline px-4 py-2 rounded-lg"
          :disabled="testing"
          @click="sendTest"
        >
          {{ testing ? 'Sending…' : 'Send test email' }}
        </button>
      </div>
      <p v-if="form.delivery_mode === 'console'" class="text-xs text-muted">
        Test send uses the console backend (output in server logs), not real email delivery.
      </p>
    </form>

    <div class="text-xs text-muted space-y-1">
      <p>
        If SMTP is not configured here, the server can fall back to <code class="text-xs">EMAIL_*</code>
        environment variables when set.
      </p>
      <p>
        Notification channels can set <code class="text-xs">use_system_smtp</code> in their config to use
        these settings.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { coreAPI } from '@/services/api'
import { normalizeApiError } from '@/utils/apiError'

defineProps({
  showTitle: { type: Boolean, default: true },
})

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const error = ref('')
const clientError = ref('')
const successMsg = ref('')
const smtpPasswordConfigured = ref(false)

const lastTestAt = ref(null)
const lastTestOk = ref(null)
const lastTestCode = ref('')
const lastTestDetail = ref('')

const form = ref({
  delivery_mode: 'console',
  smtp_host: '',
  smtp_port: 587,
  use_tls: true,
  use_ssl: false,
  smtp_username: '',
  smtp_password: '',
  default_from_email: '',
})

const passwordPlaceholder = computed(() =>
  smtpPasswordConfigured.value ? '•••••••• (unchanged if empty)' : 'Optional'
)

function formatTs(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function applyLastTestFromApi(data) {
  lastTestAt.value = data.last_smtp_test_at || null
  lastTestOk.value = typeof data.last_smtp_test_ok === 'boolean' ? data.last_smtp_test_ok : null
  lastTestCode.value = data.last_smtp_test_error_code || ''
  lastTestDetail.value = data.last_smtp_test_detail || ''
}

function onTlsSslChange(which) {
  if (which === 'tls' && form.value.use_tls && form.value.use_ssl) {
    form.value.use_ssl = false
  }
  if (which === 'ssl' && form.value.use_ssl && form.value.use_tls) {
    form.value.use_tls = false
  }
}

function validateClient() {
  clientError.value = ''
  if (form.value.delivery_mode !== 'smtp') return true
  if (!(form.value.smtp_host || '').trim()) {
    clientError.value = 'SMTP host is required.'
    return false
  }
  const p = Number(form.value.smtp_port)
  if (!Number.isFinite(p) || p < 1 || p > 65535) {
    clientError.value = 'Port must be between 1 and 65535.'
    return false
  }
  if (form.value.use_tls && form.value.use_ssl) {
    clientError.value = 'Enable only one of TLS (STARTTLS) or SSL (implicit TLS).'
    return false
  }
  return true
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await coreAPI.systemEmail.get()
    smtpPasswordConfigured.value = !!data.smtp_password_configured
    applyLastTestFromApi(data)
    form.value = {
      delivery_mode: data.delivery_mode || 'console',
      smtp_host: data.smtp_host || '',
      smtp_port: data.smtp_port ?? 587,
      use_tls: data.use_tls !== false,
      use_ssl: !!data.use_ssl,
      smtp_username: data.smtp_username || '',
      smtp_password: '',
      default_from_email: data.default_from_email || '',
    }
  } catch (e) {
    error.value = normalizeApiError(e).userMessage || 'Failed to load settings'
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!validateClient()) return
  saving.value = true
  error.value = ''
  successMsg.value = ''
  try {
    const payload = {
      delivery_mode: form.value.delivery_mode,
      smtp_host: form.value.smtp_host,
      smtp_port: form.value.smtp_port,
      use_tls: form.value.use_tls,
      use_ssl: form.value.use_ssl,
      smtp_username: form.value.smtp_username,
      default_from_email: form.value.default_from_email,
    }
    if (form.value.smtp_password && form.value.smtp_password.length) {
      payload.smtp_password = form.value.smtp_password
    }
    const { data } = await coreAPI.systemEmail.patch(payload)
    smtpPasswordConfigured.value = !!data.smtp_password_configured
    applyLastTestFromApi(data)
    form.value.smtp_password = ''
    successMsg.value = 'Settings saved.'
  } catch (e) {
    error.value = normalizeApiError(e).userMessage || 'Save failed'
  } finally {
    saving.value = false
  }
}

async function sendTest() {
  const addr = window.prompt('Send test email to:', '')
  if (!addr || !addr.trim()) return
  if (!validateClient()) return
  testing.value = true
  error.value = ''
  successMsg.value = ''
  try {
    const { data } = await coreAPI.systemEmail.test(addr.trim())
    successMsg.value = data?.message || `Test email sent to ${addr.trim()}.`
    await load()
  } catch (e) {
    const norm = normalizeApiError(e)
    error.value = norm.userMessage || norm.detail || 'Test send failed'
    await load()
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>
