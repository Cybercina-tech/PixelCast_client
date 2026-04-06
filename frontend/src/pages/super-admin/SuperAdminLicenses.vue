<template>
  <div class="space-y-6">
    <div class="flex flex-wrap justify-between items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-primary">Self-hosted licenses</h1>
        <p class="text-sm text-muted mt-1">
          Envato-backed installations that activated against this SaaS license registry
        </p>
      </div>
      <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" :disabled="loading" @click="load">
        Refresh
      </button>
    </div>

    <div
      v-if="loadError"
      class="rounded-2xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-900 dark:text-amber-100"
    >
      {{ loadError }}
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <label class="text-sm text-muted">Status</label>
      <select v-model="statusFilter" class="select-base px-3 py-2 rounded-lg text-sm max-w-xs">
        <option value="">All</option>
        <option value="pending">Pending</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
        <option value="suspended">Suspended</option>
        <option value="suspicious">Suspicious</option>
      </select>
      <label class="text-sm text-muted">Plan</label>
      <select v-model="planFilter" class="select-base px-3 py-2 rounded-lg text-sm max-w-xs">
        <option value="">All</option>
        <option value="basic">Basic</option>
        <option value="saas">SaaS</option>
      </select>
      <span class="text-xs text-muted">{{ totalCount }} total · page {{ page }} / {{ totalPages || 1 }}</span>
    </div>

    <div v-if="loading" class="card-base rounded-2xl p-8 animate-pulse h-32" />
    <Card v-else title="Installations">
      <div v-if="!rows.length" class="text-center py-10 text-muted text-sm">No installations yet</div>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="border-b border-border-color text-left text-muted">
              <th class="py-2 pr-4">Domain</th>
              <th class="py-2 pr-4">Buyer</th>
              <th class="py-2 pr-4">Sold</th>
              <th class="py-2 pr-4">Status</th>
              <th class="py-2 pr-4">Plan</th>
              <th class="py-2 pr-4">Override</th>
              <th class="py-2 pr-4">Version</th>
              <th class="py-2 pr-4">Screens</th>
              <th class="py-2 pr-4">Users</th>
              <th class="py-2 pr-4">TZ</th>
              <th class="py-2 pr-4">CC</th>
              <th class="py-2 pr-4">Last heartbeat</th>
              <th class="py-2 pr-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.id"
              class="border-b border-border-color/60 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 align-top"
            >
              <td class="py-2 pr-4 font-mono text-xs text-primary">{{ row.domain }}</td>
              <td class="py-2 pr-4 text-xs">{{ row.purchase?.buyer_username || '—' }}</td>
              <td class="py-2 pr-4 text-xs text-muted">{{ formatDate(row.purchase?.sold_at) }}</td>
              <td class="py-2 pr-4">
                <span class="text-[11px] px-2 py-0.5 rounded-full border" :class="badgeClass(row.display_status)">
                  {{ row.display_status }}
                </span>
                <span v-if="row.suspicious" class="ml-1 text-[10px] text-amber-600">flagged</span>
              </td>
              <td class="py-2 pr-4 text-xs font-mono">{{ row.plan_type || '—' }}</td>
              <td class="py-2 pr-4 text-xs">
                <select
                  class="select-base px-2 py-1 rounded text-[11px] max-w-[9rem]"
                  :value="row.plan_type_override || ''"
                  :disabled="actionId === row.id"
                  @change="setPlanOverride(row, $event.target.value)"
                >
                  <option value="">Auto</option>
                  <option value="basic">basic</option>
                  <option value="saas">saas</option>
                </select>
              </td>
              <td class="py-2 pr-4 text-xs">{{ row.app_version || '—' }}</td>
              <td class="py-2 pr-4 text-xs tabular-nums">{{ row.last_screen_count ?? '—' }}</td>
              <td class="py-2 pr-4 text-xs tabular-nums">{{ row.last_user_count ?? '—' }}</td>
              <td class="py-2 pr-4 text-[10px] font-mono text-muted max-w-[7rem] truncate" :title="row.last_timezone">
                {{ row.last_timezone || '—' }}
              </td>
              <td class="py-2 pr-4 text-xs font-mono">{{ row.last_reported_country || '—' }}</td>
              <td class="py-2 pr-4 text-xs text-muted">{{ formatDate(row.last_heartbeat_at) }}</td>
              <td class="py-2 pl-4 text-right whitespace-nowrap">
                <button
                  type="button"
                  class="btn-outline px-2 py-1 rounded text-xs mr-1"
                  :disabled="actionId === row.id"
                  @click="openHeartbeats(row)"
                >
                  Heartbeats
                </button>
                <button
                  v-if="!row.suspended"
                  type="button"
                  class="btn-outline px-2 py-1 rounded text-xs mr-1"
                  :disabled="actionId === row.id"
                  @click="suspend(row)"
                >
                  Suspend
                </button>
                <button
                  v-else
                  type="button"
                  class="btn-outline px-2 py-1 rounded text-xs mr-1"
                  :disabled="actionId === row.id"
                  @click="reactivate(row)"
                >
                  Reactivate
                </button>
                <button
                  type="button"
                  class="btn-outline px-2 py-1 rounded text-xs"
                  :disabled="actionId === row.id"
                  @click="toggleSuspicious(row)"
                >
                  {{ row.suspicious ? 'Clear flag' : 'Flag' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="rows.length" class="flex flex-wrap items-center justify-between gap-3 mt-4 pt-4 border-t border-border-color/60">
        <button
          type="button"
          class="btn-outline px-3 py-1.5 rounded-lg text-xs"
          :disabled="page <= 1 || loading"
          @click="prevPage"
        >
          Previous
        </button>
        <button
          type="button"
          class="btn-outline px-3 py-1.5 rounded-lg text-xs"
          :disabled="page >= totalPages || loading"
          @click="nextPage"
        >
          Next
        </button>
      </div>
    </Card>

    <div
      v-if="heartbeatPanel"
      class="card-base rounded-2xl border border-border-color p-4 space-y-2"
    >
      <div class="flex justify-between items-center">
        <h2 class="text-sm font-semibold text-primary">Recent heartbeats — {{ heartbeatPanel.domain }}</h2>
        <button type="button" class="text-xs text-muted hover:text-primary" @click="heartbeatPanel = null">Close</button>
      </div>
      <p v-if="heartbeatLoading" class="text-sm text-muted">Loading…</p>
      <p v-else-if="heartbeatError" class="text-sm text-amber-600">{{ heartbeatError }}</p>
      <ul v-else class="text-xs space-y-1 font-mono text-muted max-h-48 overflow-y-auto">
        <li v-for="h in heartbeats" :key="h.id">
          {{ formatDate(h.received_at) }} · {{ h.app_version || '—' }} · {{ h.ip_address || '—' }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import Card from '@/components/common/Card.vue'
import { platformAPI } from '@/services/api'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'

const notify = useNotification()
const loading = ref(false)
const loadError = ref('')
const rows = ref([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = ref(50)
const statusFilter = ref('')
const planFilter = ref('')
const actionId = ref(null)
const heartbeatPanel = ref(null)
const heartbeats = ref([])
const heartbeatLoading = ref(false)
const heartbeatError = ref('')

const totalPages = computed(() =>
  totalCount.value ? Math.ceil(totalCount.value / pageSize.value) : 0,
)

watch(statusFilter, () => {
  page.value = 1
  load()
})

watch(planFilter, () => {
  page.value = 1
  load()
})

function formatDate(v) {
  if (!v) return '—'
  try {
    return new Date(v).toLocaleString()
  } catch {
    return String(v)
  }
}

function badgeClass(st) {
  switch (st) {
    case 'active':
      return 'border-emerald-500/40 text-emerald-600 dark:text-emerald-400'
    case 'inactive':
      return 'border-slate-500/40 text-slate-500'
    case 'suspended':
      return 'border-red-500/40 text-red-600 dark:text-red-400'
    case 'suspicious':
      return 'border-amber-500/40 text-amber-600 dark:text-amber-400'
    case 'pending':
      return 'border-indigo-500/40 text-indigo-600 dark:text-indigo-400'
    default:
      return 'border-border-color text-muted'
  }
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    if (planFilter.value) params.plan = planFilter.value
    const { data } = await platformAPI.selfHostedLicenses.list(params)
    rows.value = data?.results || []
    totalCount.value = typeof data?.count === 'number' ? data.count : rows.value.length
  } catch (e) {
    loadError.value = normalizeApiError(e).userMessage || 'Failed to load licenses'
  } finally {
    loading.value = false
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value -= 1
    load()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value += 1
    load()
  }
}

async function setPlanOverride(row, value) {
  actionId.value = row.id
  try {
    const { data } = await platformAPI.selfHostedLicenses.patch(row.id, {
      plan_type_override: value,
    })
    replaceRow(data)
    notify.success('Plan override updated')
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed to update plan')
  } finally {
    actionId.value = null
  }
}

async function suspend(row) {
  actionId.value = row.id
  try {
    const { data } = await platformAPI.selfHostedLicenses.suspend(row.id, { reason: 'Suspended from super admin' })
    replaceRow(data)
    notify.success('Suspended')
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed')
  } finally {
    actionId.value = null
  }
}

async function reactivate(row) {
  actionId.value = row.id
  try {
    const { data } = await platformAPI.selfHostedLicenses.reactivate(row.id)
    replaceRow(data)
    notify.success('Reactivated')
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed')
  } finally {
    actionId.value = null
  }
}

async function toggleSuspicious(row) {
  actionId.value = row.id
  try {
    const { data } = await platformAPI.selfHostedLicenses.setSuspicious(row.id, { suspicious: !row.suspicious })
    replaceRow(data)
    notify.success('Updated')
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed')
  } finally {
    actionId.value = null
  }
}

function replaceRow(data) {
  const i = rows.value.findIndex((r) => r.id === data.id)
  if (i >= 0) rows.value[i] = data
}

async function openHeartbeats(row) {
  heartbeatPanel.value = { id: row.id, domain: row.domain }
  heartbeats.value = []
  heartbeatError.value = ''
  heartbeatLoading.value = true
  try {
    const { data } = await platformAPI.selfHostedLicenses.heartbeats(row.id)
    heartbeats.value = data?.results || []
  } catch (e) {
    heartbeatError.value = normalizeApiError(e).userMessage || 'Failed to load heartbeats'
  } finally {
    heartbeatLoading.value = false
  }
}

onMounted(load)
</script>
