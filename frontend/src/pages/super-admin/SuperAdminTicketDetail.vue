<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-muted">Loading ticket…</div>

    <!-- Error -->
    <div v-else-if="error" class="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
      {{ error }}
    </div>

    <!-- Ticket loaded -->
    <template v-else-if="ticket">
      <!-- Header -->
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <router-link to="/super-admin/tickets" class="text-sm text-muted hover:text-primary transition-colors">&larr; Queue</router-link>
            <span class="text-muted">/</span>
            <span class="font-mono text-sm text-muted">#{{ ticket.ticket_number }}</span>
            <span v-if="ticket.tenant_name" class="text-xs px-2 py-0.5 rounded-full border border-border-color/70 text-muted">
              {{ ticket.tenant_name }}
            </span>
          </div>
          <h1 class="text-2xl font-bold text-primary mt-1">{{ ticket.subject }}</h1>
        </div>
        <div class="flex items-center gap-2 flex-wrap shrink-0">
          <span class="text-xs px-2.5 py-1 rounded-full border capitalize" :class="statusClass(ticket.status)">
            {{ formatStatus(ticket.status) }}
          </span>
          <span class="text-xs px-2.5 py-1 rounded-full border capitalize" :class="priorityClass(ticket.priority)">
            {{ formatPriority(ticket.priority) }}
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main column -->
        <div class="lg:col-span-2 space-y-6">
          <!-- SLA Timeline -->
          <Card v-if="ticket.first_response_due_at || ticket.resolution_due_at" title="SLA Timeline">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div v-if="ticket.first_response_due_at" class="rounded-lg bg-slate-800/30 p-3">
                <p class="text-muted text-xs uppercase tracking-wide">First Response Due</p>
                <p class="font-semibold text-primary mt-1">{{ formatDateTime(ticket.first_response_due_at) }}</p>
                <p class="text-xs mt-1" :class="slaCountdownClass(ticket.first_response_due_at)">
                  {{ slaCountdown(ticket.first_response_due_at) }}
                </p>
              </div>
              <div v-if="ticket.resolution_due_at" class="rounded-lg bg-slate-800/30 p-3">
                <p class="text-muted text-xs uppercase tracking-wide">Resolution Due</p>
                <p class="font-semibold text-primary mt-1">{{ formatDateTime(ticket.resolution_due_at) }}</p>
                <p class="text-xs mt-1" :class="slaCountdownClass(ticket.resolution_due_at)">
                  {{ slaCountdown(ticket.resolution_due_at) }}
                </p>
              </div>
            </div>
          </Card>

          <!-- Conversation -->
          <Card title="Conversation">
            <div v-if="!messages.length" class="text-center py-6 text-muted text-sm">No messages yet</div>
            <div v-else class="space-y-4">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="rounded-xl border p-4"
                :class="msg.is_internal
                  ? 'border-amber-500/30 bg-amber-500/5'
                  : 'border-border-color/70 bg-card/50'"
              >
                <div class="flex items-center justify-between gap-2 mb-2">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm text-primary">{{ msg.author_name || 'System' }}</span>
                    <span v-if="msg.is_internal" class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 uppercase tracking-wider">
                      Internal Note
                    </span>
                    <span v-if="msg.is_agent" class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 uppercase tracking-wider">
                      Agent
                    </span>
                  </div>
                  <span class="text-xs text-muted">{{ formatDateTime(msg.created_at) }}</span>
                </div>
                <div class="text-sm text-secondary whitespace-pre-wrap">{{ msg.body }}</div>
                <div v-if="msg.attachments?.length" class="mt-2 flex flex-wrap gap-2">
                  <a
                    v-for="att in msg.attachments"
                    :key="att.id"
                    :href="att.url"
                    target="_blank"
                    class="text-xs px-2 py-1 rounded border border-border-color/70 text-muted hover:text-primary transition-colors"
                  >
                    {{ att.filename }}
                  </a>
                </div>
              </div>
            </div>

            <!-- Reply form -->
            <div class="mt-6 space-y-3 border-t border-border-color/40 pt-4">
              <div class="flex items-center justify-between gap-2">
                <label class="label-base text-sm">Reply</label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <span class="text-xs text-muted">Internal note</span>
                  <button
                    type="button"
                    class="relative w-9 h-5 rounded-full transition-colors"
                    :class="replyInternal ? 'bg-amber-500' : 'bg-slate-600'"
                    @click="replyInternal = !replyInternal"
                  >
                    <span
                      class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform"
                      :class="replyInternal ? 'translate-x-4' : ''"
                    />
                  </button>
                </label>
              </div>
              <textarea
                v-model="replyBody"
                rows="4"
                class="input-base w-full px-3 py-2 rounded-lg resize-y"
                :placeholder="replyInternal ? 'Write an internal note…' : 'Type your reply…'"
              />
              <div class="flex items-center justify-between gap-2 flex-wrap">
                <div>
                  <label class="btn-outline px-3 py-1.5 rounded-lg text-xs cursor-pointer inline-flex items-center gap-1.5">
                    <PaperClipIcon class="w-3.5 h-3.5" />
                    Attach file
                    <input type="file" class="hidden" @change="handleFileUpload" />
                  </label>
                  <span v-if="uploadStatus" class="text-xs text-muted ml-2">{{ uploadStatus }}</span>
                </div>
                <button type="button" class="btn-primary px-4 py-2 rounded-lg text-sm" :disabled="sendingReply" @click="submitReply">
                  {{ sendingReply ? 'Sending…' : (replyInternal ? 'Add Note' : 'Send Reply') }}
                </button>
              </div>
            </div>
          </Card>
        </div>

        <!-- Sidebar -->
        <div class="space-y-4">
          <!-- Details -->
          <Card title="Details">
            <dl class="space-y-3 text-sm">
              <div>
                <dt class="text-muted text-xs uppercase tracking-wide">Tenant</dt>
                <dd class="text-primary mt-0.5">{{ ticket.tenant_name || '—' }}</dd>
              </div>
              <div>
                <dt class="text-muted text-xs uppercase tracking-wide">Requester</dt>
                <dd class="text-primary mt-0.5">{{ ticket.requester_name || '—' }}</dd>
              </div>
              <div>
                <dt class="text-muted text-xs uppercase tracking-wide">Assignee</dt>
                <dd class="text-primary mt-0.5">{{ ticket.assignee_name || 'Unassigned' }}</dd>
              </div>
              <div>
                <dt class="text-muted text-xs uppercase tracking-wide">Queue</dt>
                <dd class="text-primary mt-0.5">{{ ticket.queue_name || '—' }}</dd>
              </div>
              <div>
                <dt class="text-muted text-xs uppercase tracking-wide">Created</dt>
                <dd class="text-primary mt-0.5">{{ formatDateTime(ticket.created_at) }}</dd>
              </div>
              <div v-if="ticket.tags?.length">
                <dt class="text-muted text-xs uppercase tracking-wide">Tags</dt>
                <dd class="mt-1 flex flex-wrap gap-1">
                  <span
                    v-for="tag in ticket.tags"
                    :key="tag"
                    class="text-[11px] px-2 py-0.5 rounded-full border border-border-color/70 text-muted"
                  >
                    {{ tag }}
                  </span>
                </dd>
              </div>
            </dl>
          </Card>

          <!-- Assign -->
          <Card title="Assign">
            <div class="space-y-3">
              <div>
                <label class="label-base block text-sm mb-1">User ID</label>
                <input v-model="assignUserId" type="text" class="input-base w-full px-3 py-2 rounded-lg" placeholder="Enter user ID" />
              </div>
              <button type="button" class="btn-primary w-full px-4 py-2 rounded-lg text-sm" :disabled="assigning" @click="submitAssign">
                {{ assigning ? 'Assigning…' : 'Assign' }}
              </button>
            </div>
          </Card>

          <!-- Transitions -->
          <Card title="Actions">
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="action in transitionActions"
                :key="action.value"
                type="button"
                class="px-3 py-2 rounded-lg border text-xs font-medium transition-colors"
                :class="action.class"
                @click="handleTransition(action.value)"
              >
                {{ action.label }}
              </button>
            </div>
          </Card>

          <!-- Merge -->
          <Card title="Merge">
            <div class="space-y-3">
              <p class="text-xs text-muted">Merge this ticket into another ticket. Messages will be combined.</p>
              <div>
                <label class="label-base block text-sm mb-1">Target Ticket ID</label>
                <input v-model="mergeTargetId" type="text" class="input-base w-full px-3 py-2 rounded-lg" placeholder="Enter ticket ID" />
              </div>
              <button type="button" class="btn-outline w-full px-4 py-2 rounded-lg text-sm text-amber-300 border-amber-500/40 hover:bg-amber-500/10" :disabled="merging" @click="submitMerge">
                {{ merging ? 'Merging…' : 'Merge Ticket' }}
              </button>
            </div>
          </Card>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PaperClipIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/common/Card.vue'
import { platformTicketsAPI } from '@/services/api'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'

const route = useRoute()
const notify = useNotification()
const ticketId = () => route.params.id

const loading = ref(false)
const error = ref(null)
const ticket = ref(null)
const messages = ref([])

const replyBody = ref('')
const replyInternal = ref(false)
const sendingReply = ref(false)
const uploadStatus = ref('')

const assignUserId = ref('')
const assigning = ref(false)

const mergeTargetId = ref('')
const merging = ref(false)

const transitionActions = [
  { value: 'start_progress', label: 'Start Progress', class: 'border-violet-500/40 bg-violet-500/10 text-violet-300 hover:bg-violet-500/20' },
  { value: 'pend', label: 'Pend', class: 'border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20' },
  { value: 'resolve', label: 'Resolve', class: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20' },
  { value: 'close', label: 'Close', class: 'border-slate-500/40 bg-slate-500/10 text-slate-400 hover:bg-slate-500/20' },
  { value: 'reopen', label: 'Reopen', class: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20' },
  { value: 'escalate', label: 'Escalate', class: 'border-red-500/40 bg-red-500/10 text-red-300 hover:bg-red-500/20' },
]

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

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function slaCountdown(iso) {
  if (!iso) return ''
  const diff = new Date(iso) - Date.now()
  if (diff <= 0) return 'Overdue'
  const hours = Math.floor(diff / 3600000)
  const mins = Math.floor((diff % 3600000) / 60000)
  if (hours >= 24) return `${Math.floor(hours / 24)}d ${hours % 24}h remaining`
  return `${hours}h ${mins}m remaining`
}

function slaCountdownClass(iso) {
  if (!iso) return 'text-muted'
  const diff = new Date(iso) - Date.now()
  if (diff <= 0) return 'text-red-400 font-semibold'
  if (diff < 3600000) return 'text-orange-400'
  return 'text-emerald-400'
}

async function loadTicket() {
  loading.value = true
  error.value = null
  try {
    const { data } = await platformTicketsAPI.detail(ticketId())
    ticket.value = data
    messages.value = data.messages ?? []
    assignUserId.value = data.assignee_id ? String(data.assignee_id) : ''
  } catch (e) {
    error.value = normalizeApiError(e).userMessage || 'Failed to load ticket'
  } finally {
    loading.value = false
  }
}

async function submitReply() {
  if (!replyBody.value.trim()) {
    notify.error('Reply cannot be empty.')
    return
  }
  sendingReply.value = true
  try {
    await platformTicketsAPI.reply(ticketId(), { body: replyBody.value, is_internal: replyInternal.value })
    replyBody.value = ''
    notify.success(replyInternal.value ? 'Internal note added.' : 'Reply sent.')
    await loadTicket()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed to send reply')
  } finally {
    sendingReply.value = false
  }
}

async function handleFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploadStatus.value = 'Uploading…'
  try {
    const formData = new FormData()
    formData.append('file', file)
    await platformTicketsAPI.upload(ticketId(), formData)
    uploadStatus.value = ''
    notify.success('File uploaded.')
    await loadTicket()
  } catch (e) {
    uploadStatus.value = ''
    notify.error(normalizeApiError(e).userMessage || 'Upload failed')
  }
  event.target.value = ''
}

async function submitAssign() {
  if (!assignUserId.value.trim()) {
    notify.error('User ID is required.')
    return
  }
  assigning.value = true
  try {
    await platformTicketsAPI.assign(ticketId(), { assignee_id: assignUserId.value.trim() })
    notify.success('Ticket assigned.')
    await loadTicket()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Assign failed')
  } finally {
    assigning.value = false
  }
}

async function handleTransition(action) {
  try {
    await platformTicketsAPI.transition(ticketId(), { action })
    notify.success(`Ticket transitioned: ${action.replace(/_/g, ' ')}`)
    await loadTicket()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Transition failed')
  }
}

async function submitMerge() {
  if (!mergeTargetId.value.trim()) {
    notify.error('Target ticket ID is required.')
    return
  }
  const ok = window.confirm(`Merge this ticket into #${mergeTargetId.value}? This action cannot be undone.`)
  if (!ok) return
  merging.value = true
  try {
    await platformTicketsAPI.merge(ticketId(), { target_ticket_id: mergeTargetId.value.trim() })
    notify.success('Tickets merged.')
    await loadTicket()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Merge failed')
  } finally {
    merging.value = false
  }
}

onMounted(loadTicket)
</script>
