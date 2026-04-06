<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap justify-between items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-primary">Ticket Queue</h1>
        <p class="text-sm text-muted mt-1">Create, assign, and manage support tickets for any customer</p>
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

    <!-- Filters -->
    <Card>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <div>
          <label class="label-base block text-sm mb-1">Search</label>
          <input
            v-model="filters.search"
            type="text"
            class="input-base w-full px-3 py-2 rounded-lg"
            placeholder="Subject, ticket #..."
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
        <div>
          <label class="label-base block text-sm mb-1">Tenant</label>
          <select v-model="filters.tenant_id" class="select-base w-full px-3 py-2 rounded-lg" @change="load">
            <option value="">All tenants</option>
            <option v-for="t in tenantOptions" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>
        <div>
          <label class="label-base block text-sm mb-1">Assignee</label>
          <select v-model="filters.assignee_id" class="select-base w-full px-3 py-2 rounded-lg" @change="load">
            <option value="">All</option>
            <option value="unassigned">Unassigned</option>
            <option v-for="u in agentOptions" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
        </div>
      </div>

      <!-- Loading / error / empty -->
      <div v-if="loading" class="text-center py-8 text-muted">Loading...</div>
      <div v-else-if="error" class="text-center py-8 text-red-400">{{ error }}</div>
      <div v-else-if="!rows.length" class="text-center py-12 text-muted">
        <p class="text-lg">No tickets match your filters</p>
        <p class="text-sm mt-1">Create a new ticket or adjust your filters</p>
      </div>

      <!-- Ticket list -->
      <div v-else class="space-y-4">
        <!-- Mobile cards -->
        <div class="grid gap-3 lg:hidden">
          <article
            v-for="row in rows"
            :key="`card-${row.id}`"
            class="rounded-xl border border-border-color/70 bg-card/50 p-4 cursor-pointer hover:border-accent-color/30 transition-colors"
            @click="$router.push(`/super-admin/tickets/${row.id}`)"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="text-[10px] text-muted uppercase tracking-wider">{{ row.tenant_name }}</p>
                <h3 class="font-semibold text-primary truncate mt-0.5">
                  <span class="font-mono text-muted text-xs">#{{ row.number }}</span>
                  {{ row.subject }}
                </h3>
                <p class="text-xs text-muted mt-1">{{ row.requester_name || 'Unknown' }}</p>
              </div>
              <span class="text-[11px] px-2 py-1 rounded-full border capitalize shrink-0" :class="statusClass(row.status)">
                {{ formatStatus(row.status) }}
              </span>
            </div>
            <div class="mt-3 flex items-center justify-between text-xs flex-wrap gap-2">
              <span class="px-2 py-0.5 rounded-full border capitalize" :class="priorityClass(row.priority)">{{ formatPriority(row.priority) }}</span>
              <span class="text-muted">{{ row.assignee_name || 'Unassigned' }}</span>
              <span :class="slaStatusClass(row)">{{ slaStatusLabel(row) }}</span>
            </div>
            <div class="mt-2 flex items-center justify-between text-xs text-muted">
              <span>{{ formatDate(row.created_at) }}</span>
              <button
                type="button"
                class="px-2 py-1 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 text-xs hover:bg-cyan-500/20"
                @click.stop="openQuickReply(row)"
              >
                Reply
              </button>
            </div>
          </article>
        </div>

        <!-- Desktop table -->
        <div class="hidden lg:block overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="border-b border-border-color text-left text-muted">
                <th class="py-2 pr-4">Tenant</th>
                <th class="py-2 pr-4">Ticket</th>
                <th class="py-2 pr-4">Subject</th>
                <th class="py-2 pr-4">Requester</th>
                <th class="py-2 pr-4">Status</th>
                <th class="py-2 pr-4">Priority</th>
                <th class="py-2 pr-4">Assignee</th>
                <th class="py-2 pr-4">SLA</th>
                <th class="py-2 pr-4">Created</th>
                <th class="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in rows"
                :key="row.id"
                class="border-b border-border-color/60 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 cursor-pointer"
                @click="$router.push(`/super-admin/tickets/${row.id}`)"
              >
                <td class="py-2.5 pr-4 text-secondary text-xs">{{ row.tenant_name }}</td>
                <td class="py-2.5 pr-4 font-mono text-muted text-xs">#{{ row.number }}</td>
                <td class="py-2.5 pr-4 font-medium text-primary max-w-xs truncate">{{ row.subject }}</td>
                <td class="py-2.5 pr-4 text-secondary text-xs">{{ row.requester_name || '—' }}</td>
                <td class="py-2.5 pr-4">
                  <span class="text-[11px] px-2 py-1 rounded-full border capitalize" :class="statusClass(row.status)">
                    {{ formatStatus(row.status) }}
                  </span>
                </td>
                <td class="py-2.5 pr-4">
                  <span class="text-[11px] px-2 py-1 rounded-full border capitalize" :class="priorityClass(row.priority)">
                    {{ formatPriority(row.priority) }}
                  </span>
                </td>
                <td class="py-2.5 pr-4 text-secondary text-xs">{{ row.assignee_name || '—' }}</td>
                <td class="py-2.5 pr-4">
                  <span class="text-xs" :class="slaStatusClass(row)">{{ slaStatusLabel(row) }}</span>
                </td>
                <td class="py-2.5 pr-4 text-muted text-xs whitespace-nowrap">{{ formatDate(row.created_at) }}</td>
                <td class="py-2.5" @click.stop>
                  <div class="flex items-center gap-1.5">
                    <button
                      type="button"
                      class="inline-flex items-center rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 px-2 py-1 text-xs hover:bg-cyan-500/20 transition-colors"
                      @click="openQuickReply(row)"
                    >
                      Reply
                    </button>
                    <button
                      type="button"
                      class="inline-flex items-center rounded-lg border border-violet-500/40 bg-violet-500/10 text-violet-300 px-2 py-1 text-xs hover:bg-violet-500/20 transition-colors"
                      @click="openAssignModal(row)"
                    >
                      Assign
                    </button>
                    <select
                      class="select-base px-2 py-1 rounded-lg text-xs"
                      @change="handleTransition(row, $event.target.value); $event.target.value = ''"
                    >
                      <option value="">Action...</option>
                      <option value="start_progress">Start Progress</option>
                      <option value="pend">Pend</option>
                      <option value="resolve">Resolve</option>
                      <option value="close">Close</option>
                      <option value="reopen">Reopen</option>
                      <option value="escalate">Escalate</option>
                    </select>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Card>

    <!-- ==================== Create Ticket Modal ==================== -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 bg-black/55 backdrop-blur-sm p-4 flex items-center justify-center"
      @click.self="showCreateModal = false"
    >
      <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border-color bg-card p-5 space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-primary">Create Ticket</h2>
            <p class="text-xs text-muted mt-1">Open a ticket on behalf of any customer</p>
          </div>
          <button type="button" class="btn-outline px-3 py-1 text-xs rounded-lg" @click="showCreateModal = false">Close</button>
        </div>

        <!-- Tenant selection -->
        <div>
          <label class="label-base block text-sm mb-1">Tenant *</label>
          <select v-model="createForm.tenant_id" class="select-base w-full px-3 py-2 rounded-lg" @change="onTenantChange">
            <option value="">Select tenant...</option>
            <option v-for="t in tenantOptions" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>

        <!-- User selection -->
        <div>
          <label class="label-base block text-sm mb-1">Requester (customer) *</label>
          <div class="relative">
            <input
              v-model="userSearch"
              type="text"
              class="input-base w-full px-3 py-2 rounded-lg"
              placeholder="Search by email or name..."
              @input="searchUsers"
              @focus="showUserDropdown = true"
            />
            <div
              v-if="showUserDropdown && userResults.length"
              class="absolute z-10 mt-1 w-full rounded-xl border border-border-color bg-card shadow-lg max-h-48 overflow-y-auto"
            >
              <button
                v-for="u in userResults"
                :key="u.id"
                type="button"
                class="w-full text-left px-3 py-2 hover:bg-slate-800/40 text-sm flex items-center justify-between gap-2 border-b border-border-color/40 last:border-0"
                @click="selectUser(u)"
              >
                <div class="min-w-0">
                  <p class="font-medium text-primary truncate">{{ u.name }}</p>
                  <p class="text-xs text-muted truncate">{{ u.email }}</p>
                </div>
                <span class="text-[10px] px-1.5 py-0.5 rounded border border-border-color/60 text-muted shrink-0">{{ u.role }}</span>
              </button>
            </div>
          </div>
          <p v-if="selectedUser" class="mt-1.5 text-xs text-emerald-400">
            Selected: {{ selectedUser.name }} ({{ selectedUser.email }})
          </p>
        </div>

        <!-- Subject -->
        <div>
          <label class="label-base block text-sm mb-1">Subject *</label>
          <input v-model="createForm.subject" type="text" class="input-base w-full px-3 py-2 rounded-lg" placeholder="Brief summary of the issue" />
        </div>

        <!-- Message body -->
        <div>
          <label class="label-base block text-sm mb-1">Message *</label>
          <textarea
            v-model="createForm.body"
            class="input-base w-full px-3 py-2 rounded-lg min-h-[120px] resize-y"
            placeholder="Describe the issue or provide information to the customer..."
          />
        </div>

        <!-- Priority & Category -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="label-base block text-sm mb-1">Priority</label>
            <select v-model="createForm.priority" class="select-base w-full px-3 py-2 rounded-lg">
              <option value="low">Low</option>
              <option value="medium">Normal</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label class="label-base block text-sm mb-1">Category</label>
            <input v-model="createForm.category" type="text" class="input-base w-full px-3 py-2 rounded-lg" placeholder="e.g. billing, technical..." />
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" @click="showCreateModal = false">Cancel</button>
          <button
            type="button"
            class="btn-primary px-4 py-2 rounded-lg text-sm"
            :disabled="creating || !createForm.tenant_id || !createForm.requester_id || !createForm.subject.trim() || !createForm.body.trim()"
            @click="submitCreate"
          >
            {{ creating ? 'Creating...' : 'Create Ticket' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ==================== Quick Reply Modal ==================== -->
    <div
      v-if="showReplyModal"
      class="fixed inset-0 z-50 bg-black/55 backdrop-blur-sm p-4 flex items-center justify-center"
      @click.self="showReplyModal = false"
    >
      <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border-color bg-card p-5 space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-primary">
              <span class="font-mono text-muted">#{{ replyTarget?.number }}</span>
              {{ replyTarget?.subject }}
            </h2>
            <p class="text-xs text-muted mt-1">{{ replyTarget?.requester_name }} &middot; {{ replyTarget?.tenant_name }}</p>
          </div>
          <button type="button" class="btn-outline px-3 py-1 text-xs rounded-lg" @click="showReplyModal = false">Close</button>
        </div>

        <!-- Recent messages preview -->
        <div v-if="replyMessages.length" class="space-y-2 max-h-60 overflow-y-auto border border-border-color/60 rounded-xl p-3">
          <div
            v-for="msg in replyMessages"
            :key="msg.id"
            class="rounded-lg px-3 py-2 text-sm"
            :class="msg.is_internal
              ? 'border border-amber-500/30 bg-amber-500/5'
              : 'border border-border-color/40 bg-card/50'"
          >
            <div class="flex items-center justify-between gap-2 mb-1">
              <span class="font-medium text-xs" :class="msg.is_internal ? 'text-amber-300' : 'text-secondary'">
                {{ msg.author_name || 'System' }}
                <span v-if="msg.is_internal" class="text-amber-400/70 text-[10px] ml-1">[internal]</span>
              </span>
              <span class="text-[10px] text-muted">{{ formatDate(msg.created_at) }}</span>
            </div>
            <p class="text-secondary whitespace-pre-wrap text-xs">{{ msg.body }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-muted">Loading messages...</p>

        <!-- Reply form -->
        <div>
          <div class="flex items-center gap-3 mb-2">
            <label class="label-base text-sm">Your reply</label>
            <label class="inline-flex items-center gap-1.5 text-xs cursor-pointer">
              <input v-model="replyForm.is_internal" type="checkbox" class="rounded border-border-color" />
              <span class="text-amber-300">Internal note</span>
            </label>
          </div>
          <textarea
            v-model="replyForm.body"
            class="input-base w-full px-3 py-2 rounded-lg min-h-[80px] resize-y"
            placeholder="Type your message..."
          />
        </div>

        <div class="flex items-center justify-end gap-2">
          <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" @click="showReplyModal = false">Cancel</button>
          <button
            type="button"
            class="btn-primary px-4 py-2 rounded-lg text-sm"
            :disabled="replying || !replyForm.body.trim()"
            @click="submitReply"
          >
            {{ replying ? 'Sending...' : (replyForm.is_internal ? 'Add Note' : 'Send Reply') }}
          </button>
        </div>
      </div>
    </div>

    <!-- ==================== Assign Modal ==================== -->
    <div
      v-if="showAssignModal"
      class="fixed inset-0 z-50 bg-black/55 backdrop-blur-sm p-4 flex items-center justify-center"
      @click.self="showAssignModal = false"
    >
      <div class="w-full max-w-md rounded-2xl border border-border-color bg-card p-5 space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-primary">Assign Ticket</h2>
            <p class="text-xs text-muted mt-1">
              <span class="font-mono">#{{ assignTarget?.number }}</span> &mdash; {{ assignTarget?.subject }}
            </p>
          </div>
          <button type="button" class="btn-outline px-3 py-1 text-xs rounded-lg" @click="showAssignModal = false">Close</button>
        </div>
        <div>
          <label class="label-base block text-sm mb-1">Select agent</label>
          <div class="relative">
            <input
              v-model="assignSearch"
              type="text"
              class="input-base w-full px-3 py-2 rounded-lg"
              placeholder="Search by name or email..."
              @input="searchAgents"
              @focus="showAgentDropdown = true"
            />
            <div
              v-if="showAgentDropdown && assignResults.length"
              class="absolute z-10 mt-1 w-full rounded-xl border border-border-color bg-card shadow-lg max-h-48 overflow-y-auto"
            >
              <button
                v-for="u in assignResults"
                :key="u.id"
                type="button"
                class="w-full text-left px-3 py-2 hover:bg-slate-800/40 text-sm flex items-center justify-between gap-2 border-b border-border-color/40 last:border-0"
                @click="selectAgent(u)"
              >
                <div class="min-w-0">
                  <p class="font-medium text-primary truncate">{{ u.name }}</p>
                  <p class="text-xs text-muted truncate">{{ u.email }}</p>
                </div>
                <span class="text-[10px] px-1.5 py-0.5 rounded border border-border-color/60 text-muted shrink-0">{{ u.role }}</span>
              </button>
            </div>
          </div>
          <p v-if="selectedAgent" class="mt-1.5 text-xs text-emerald-400">
            Selected: {{ selectedAgent.name }} ({{ selectedAgent.email }})
          </p>
        </div>
        <div class="flex items-center justify-end gap-2">
          <button type="button" class="btn-outline px-4 py-2 rounded-lg text-sm" @click="showAssignModal = false">Cancel</button>
          <button
            type="button"
            class="btn-primary px-4 py-2 rounded-lg text-sm"
            :disabled="assigning || !selectedAgent"
            @click="submitAssign"
          >
            {{ assigning ? 'Assigning...' : 'Assign' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/common/Card.vue'
import { platformTicketsAPI, usersAPI } from '@/services/api'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'

const notify = useNotification()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref(null)
const rows = ref([])
const filters = ref({ search: '', status: '', priority: '', tenant_id: '', assignee_id: '' })

const tenantOptions = ref([])
const agentOptions = ref([])

// -- Create modal --
const showCreateModal = ref(false)
const creating = ref(false)
const createForm = ref({ tenant_id: '', requester_id: '', subject: '', body: '', priority: 'medium', category: '' })
const userSearch = ref('')
const userResults = ref([])
const showUserDropdown = ref(false)
const selectedUser = ref(null)
let userSearchTimeout = null

// -- Reply modal --
const showReplyModal = ref(false)
const replying = ref(false)
const replyTarget = ref(null)
const replyMessages = ref([])
const replyForm = ref({ body: '', is_internal: false })

// -- Assign modal --
const showAssignModal = ref(false)
const assigning = ref(false)
const assignTarget = ref(null)
const assignSearch = ref('')
const assignResults = ref([])
const showAgentDropdown = ref(false)
const selectedAgent = ref(null)
let agentSearchTimeout = null

// ========== Helpers ==========

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

function formatDate(d) {
  if (!d) return '—'
  const dt = new Date(d)
  const now = new Date()
  const diffMs = now - dt
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`
  if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`
  return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function slaStatusLabel(row) {
  if (!row.resolution_due_at) return '—'
  const diff = new Date(row.resolution_due_at) - Date.now()
  if (diff <= 0) return 'Breached'
  if (diff < 3600000) return 'At risk'
  return 'On track'
}

function slaStatusClass(row) {
  if (!row.resolution_due_at) return 'text-muted'
  const diff = new Date(row.resolution_due_at) - Date.now()
  if (diff <= 0) return 'text-red-400 font-semibold'
  if (diff < 3600000) return 'text-orange-400'
  return 'text-emerald-400'
}

// ========== Load ==========

async function load() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.priority) params.priority = filters.value.priority
    if (filters.value.tenant_id) params.tenant_id = filters.value.tenant_id
    if (filters.value.assignee_id && filters.value.assignee_id !== 'unassigned') params.assignee_id = filters.value.assignee_id
    const { data } = await platformTicketsAPI.list(params)
    rows.value = data.results ?? data
  } catch (e) {
    error.value = normalizeApiError(e).userMessage || 'Failed to load ticket queue'
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  try {
    const [tRes, uRes] = await Promise.all([
      platformTicketsAPI.tenants(),
      platformTicketsAPI.users(),
    ])
    tenantOptions.value = tRes.data
    agentOptions.value = uRes.data
  } catch {
    // meta load failure is non-critical
  }
}

// ========== Create ==========

function openCreateModal() {
  createForm.value = { tenant_id: '', requester_id: '', subject: '', body: '', priority: 'medium', category: '' }
  selectedUser.value = null
  userSearch.value = ''
  userResults.value = []
  showCreateModal.value = true
}

async function applyCreatePrefillFromQuery() {
  const q = route.query
  if (q.new !== '1') return
  const rid = q.requester_id
  const tid = q.tenant_id
  if (!rid && !tid) return
  openCreateModal()
  if (tid) createForm.value.tenant_id = String(tid)
  if (rid) {
    createForm.value.requester_id = String(rid)
    try {
      const { data } = await usersAPI.detail(rid)
      selectedUser.value = {
        id: data.id,
        name: data.full_name || data.username,
        email: data.email,
        tenant_id: data.tenant_id,
      }
      userSearch.value = selectedUser.value.name
      if (!createForm.value.tenant_id && data.tenant_id) {
        createForm.value.tenant_id = String(data.tenant_id)
      }
    } catch {
      userSearch.value = `User #${rid}`
    }
  }
  router.replace({ path: route.path, query: {} })
}

function onTenantChange() {
  selectedUser.value = null
  createForm.value.requester_id = ''
  userSearch.value = ''
  userResults.value = []
}

function searchUsers() {
  clearTimeout(userSearchTimeout)
  userSearchTimeout = setTimeout(async () => {
    if (!userSearch.value.trim()) { userResults.value = []; return }
    try {
      const params = { search: userSearch.value.trim() }
      if (createForm.value.tenant_id) params.tenant_id = createForm.value.tenant_id
      const { data } = await platformTicketsAPI.users(params)
      userResults.value = data
      showUserDropdown.value = true
    } catch { /* ignore */ }
  }, 300)
}

function selectUser(u) {
  selectedUser.value = u
  createForm.value.requester_id = u.id
  userSearch.value = u.name
  showUserDropdown.value = false
  if (!createForm.value.tenant_id && u.tenant_id) {
    createForm.value.tenant_id = u.tenant_id
  }
}

async function submitCreate() {
  creating.value = true
  try {
    await platformTicketsAPI.create(createForm.value)
    notify.success('Ticket created successfully')
    showCreateModal.value = false
    await load()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed to create ticket')
  } finally {
    creating.value = false
  }
}

// ========== Quick Reply ==========

async function openQuickReply(row) {
  replyTarget.value = row
  replyForm.value = { body: '', is_internal: false }
  replyMessages.value = []
  showReplyModal.value = true
  try {
    const { data } = await platformTicketsAPI.detail(row.id)
    replyMessages.value = data.messages || []
  } catch { /* ignore */ }
}

async function submitReply() {
  replying.value = true
  try {
    await platformTicketsAPI.reply(replyTarget.value.id, replyForm.value)
    notify.success(replyForm.value.is_internal ? 'Internal note added' : 'Reply sent')
    // Refresh the messages
    try {
      const { data } = await platformTicketsAPI.detail(replyTarget.value.id)
      replyMessages.value = data.messages || []
    } catch { /* ignore */ }
    replyForm.value.body = ''
    replyForm.value.is_internal = false
    await load()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed to send reply')
  } finally {
    replying.value = false
  }
}

// ========== Assign ==========

function openAssignModal(row) {
  assignTarget.value = row
  assignSearch.value = ''
  assignResults.value = []
  selectedAgent.value = null
  showAssignModal.value = true
}

function searchAgents() {
  clearTimeout(agentSearchTimeout)
  agentSearchTimeout = setTimeout(async () => {
    if (!assignSearch.value.trim()) { assignResults.value = []; return }
    try {
      const { data } = await platformTicketsAPI.users({ search: assignSearch.value.trim() })
      assignResults.value = data
      showAgentDropdown.value = true
    } catch { /* ignore */ }
  }, 300)
}

function selectAgent(u) {
  selectedAgent.value = u
  assignSearch.value = u.name
  showAgentDropdown.value = false
}

async function submitAssign() {
  if (!selectedAgent.value) return
  assigning.value = true
  try {
    await platformTicketsAPI.assign(assignTarget.value.id, { assignee_id: selectedAgent.value.id })
    notify.success('Ticket assigned')
    showAssignModal.value = false
    await load()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Assign failed')
  } finally {
    assigning.value = false
  }
}

// ========== Transition ==========

async function handleTransition(row, action) {
  if (!action) return
  try {
    await platformTicketsAPI.transition(row.id, { action })
    notify.success(`Ticket: ${action.replace(/_/g, ' ')}`)
    await load()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Transition failed')
  }
}

// ========== Init ==========

onMounted(async () => {
  await load()
  await loadMeta()
  await applyCreatePrefillFromQuery()
})
</script>
