<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 class="text-2xl font-bold text-primary">Support Tickets</h1>
          <p class="text-sm text-muted mt-1">Track and manage your support requests</p>
        </div>
        <div class="flex gap-2 flex-wrap">
          <button type="button" class="btn-primary px-4 py-2 rounded-lg text-sm" @click="openCreateModal">
            New Ticket
          </button>
          <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" @click="load" :disabled="loading">
            Refresh
          </button>
        </div>
      </div>

      <Card>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <div>
            <label class="label-base block text-sm mb-1">Search</label>
            <input
              v-model="filters.search"
              type="text"
              class="input-base w-full px-3 py-2 rounded-lg"
              placeholder="Subject, ticket number…"
              @keyup.enter="load"
            />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Status</label>
            <select v-model="filters.status" class="select-base w-full px-3 py-2 rounded-lg" @change="load">
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="pending">Pending</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Priority</label>
            <select v-model="filters.priority" class="select-base w-full px-3 py-2 rounded-lg" @change="load">
              <option value="">All</option>
              <option value="low">Low</option>
              <option value="medium">Normal</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>

        <div v-if="loading" class="text-center py-8 text-muted">Loading…</div>
        <div v-else-if="error" class="text-center py-8 text-red-600">{{ error }}</div>
        <div v-else-if="!rows.length" class="text-center py-12 text-muted">
          <TicketIcon class="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p>No tickets found</p>
          <button type="button" class="btn-primary px-4 py-2 rounded-lg text-sm mt-4" @click="openCreateModal">
            Create your first ticket
          </button>
        </div>
        <div v-else class="space-y-4">
          <!-- Mobile cards -->
          <div class="grid gap-3 lg:hidden">
            <router-link
              v-for="row in rows"
              :key="`card-${row.id}`"
              :to="`/tickets/${row.id}`"
              class="block rounded-xl border border-border-color/70 bg-card/50 p-4 hover:border-cyan-500/30 transition-colors"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="text-[11px] text-muted font-mono">#{{ row.ticket_number }}</p>
                  <h3 class="font-semibold text-primary truncate">{{ row.subject }}</h3>
                </div>
                <span class="text-[11px] px-2 py-1 rounded-full border capitalize shrink-0" :class="statusClass(row.status)">
                  {{ formatStatus(row.status) }}
                </span>
              </div>
              <div class="mt-3 flex items-center justify-between text-xs">
                <span class="px-2 py-0.5 rounded-full border capitalize" :class="priorityClass(row.priority)">
                  {{ formatPriority(row.priority) }}
                </span>
                <span class="text-muted">{{ row.assignee_name || 'Unassigned' }}</span>
                <span class="text-muted">{{ formatDate(row.created_at) }}</span>
              </div>
            </router-link>
          </div>

          <!-- Desktop table -->
          <div class="hidden lg:block overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="border-b border-border-color text-left text-muted">
                  <th class="py-2 pr-4">Ticket</th>
                  <th class="py-2 pr-4">Subject</th>
                  <th class="py-2 pr-4">Status</th>
                  <th class="py-2 pr-4">Priority</th>
                  <th class="py-2 pr-4">Assignee</th>
                  <th class="py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in rows"
                  :key="row.id"
                  class="border-b border-border-color/60 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 cursor-pointer"
                  @click="$router.push(`/tickets/${row.id}`)"
                >
                  <td class="py-2 pr-4 font-mono text-muted text-xs">#{{ row.ticket_number }}</td>
                  <td class="py-2 pr-4 font-medium text-primary max-w-xs truncate">{{ row.subject }}</td>
                  <td class="py-2 pr-4">
                    <span class="text-[11px] px-2 py-1 rounded-full border capitalize" :class="statusClass(row.status)">
                      {{ formatStatus(row.status) }}
                    </span>
                  </td>
                  <td class="py-2 pr-4">
                    <span class="text-[11px] px-2 py-1 rounded-full border capitalize" :class="priorityClass(row.priority)">
                      {{ formatPriority(row.priority) }}
                    </span>
                  </td>
                  <td class="py-2 pr-4 text-secondary">{{ row.assignee_name || '—' }}</td>
                  <td class="py-2 text-muted text-xs">{{ formatDate(row.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>

    <!-- Create ticket modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 bg-black/55 backdrop-blur-sm p-4 flex items-center justify-center"
      @click.self="closeModal"
    >
      <div class="w-full max-w-lg rounded-2xl border border-border-color bg-card p-5 space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-primary">New Ticket</h2>
            <p class="text-xs text-muted mt-1">Describe your issue and we'll get back to you.</p>
          </div>
          <button type="button" class="btn-outline px-3 py-1 text-xs rounded-lg" @click="closeModal">Close</button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="label-base block text-sm mb-1">Subject *</label>
            <input v-model="form.subject" type="text" class="input-base w-full px-3 py-2 rounded-lg" placeholder="Brief description of the issue" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Description *</label>
            <textarea v-model="form.body" rows="5" class="input-base w-full px-3 py-2 rounded-lg resize-y" placeholder="Provide details about your issue…" />
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Priority</label>
            <select v-model="form.priority" class="select-base w-full px-3 py-2 rounded-lg">
              <option value="low">Low</option>
              <option value="medium">Normal</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2">
          <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" @click="closeModal">Cancel</button>
          <button type="button" class="btn-primary px-4 py-2 rounded-lg text-sm" :disabled="saving" @click="submitTicket">
            {{ saving ? 'Creating…' : 'Create Ticket' }}
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { TicketIcon } from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import { ticketsAPI } from '@/services/api'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'

const loading = ref(false)
const error = ref(null)
const rows = ref([])
const filters = ref({ search: '', status: '', priority: '' })
const notify = useNotification()
const showModal = ref(false)
const saving = ref(false)
const form = ref({ subject: '', body: '', priority: 'medium' })

function statusClass(status) {
  const map = {
    open: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300',
    assigned: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
    in_progress: 'border-violet-500/30 bg-violet-500/10 text-violet-300',
    pending: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
    resolved: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
    closed: 'border-slate-500/30 bg-slate-500/10 text-slate-400',
  }
  return map[status] || 'border-border-color/70 bg-card text-muted'
}

function priorityClass(priority) {
  const map = {
    low: 'border-slate-500/30 bg-slate-500/10 text-slate-400',
    medium: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
    high: 'border-orange-500/30 bg-orange-500/10 text-orange-300',
    critical: 'border-red-500/30 bg-red-500/10 text-red-300',
  }
  return map[priority] || 'border-border-color/70 bg-card text-muted'
}

function formatPriority(p) {
  const labels = { low: 'Low', medium: 'Normal', high: 'High', critical: 'Critical' }
  return labels[p] || p
}

function formatStatus(s) {
  return s?.replace(/_/g, ' ') || s
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function openCreateModal() {
  form.value = { subject: '', body: '', priority: 'medium' }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function submitTicket() {
  if (!form.value.subject?.trim()) {
    notify.error('Subject is required.')
    return
  }
  if (!form.value.body?.trim()) {
    notify.error('Description is required.')
    return
  }
  saving.value = true
  try {
    await ticketsAPI.create(form.value)
    notify.success('Ticket created.')
    closeModal()
    await load()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed to create ticket')
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.priority) params.priority = filters.value.priority
    const { data } = await ticketsAPI.list(params)
    rows.value = data.results ?? data
  } catch (e) {
    error.value = normalizeApiError(e).userMessage || 'Failed to load tickets'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
