<template>
  <AppLayout>
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
              <router-link to="/tickets" class="text-sm text-muted hover:text-primary transition-colors">&larr; Tickets</router-link>
              <span class="text-muted">/</span>
              <span class="font-mono text-sm text-muted">#{{ ticket.ticket_number }}</span>
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
                        Internal
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
                <label class="label-base block text-sm">Reply</label>
                <textarea
                  v-model="replyBody"
                  rows="4"
                  class="input-base w-full px-3 py-2 rounded-lg resize-y"
                  placeholder="Type your reply…"
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
                    {{ sendingReply ? 'Sending…' : 'Send Reply' }}
                  </button>
                </div>
              </div>
            </Card>

            <!-- CSAT -->
            <Card
              v-if="showCsatForm"
              title="How was your experience?"
              subtitle="Your feedback helps us improve."
            >
              <div class="space-y-4">
                <div>
                  <label class="label-base block text-sm mb-2">Rating</label>
                  <div class="flex gap-2">
                    <button
                      v-for="n in 5"
                      :key="n"
                      type="button"
                      class="w-10 h-10 rounded-lg border text-sm font-semibold transition-colors"
                      :class="csatForm.score === n
                        ? 'border-cyan-500 bg-cyan-500/20 text-cyan-300'
                        : 'border-border-color/70 text-muted hover:border-cyan-500/30'"
                      @click="csatForm.score = n"
                    >
                      {{ n }}
                    </button>
                  </div>
                </div>
                <div>
                  <label class="label-base block text-sm mb-1">Comment (optional)</label>
                  <textarea v-model="csatForm.comment" rows="2" class="input-base w-full px-3 py-2 rounded-lg resize-y" />
                </div>
                <button type="button" class="btn-primary px-4 py-2 rounded-lg text-sm" :disabled="submittingCsat || !csatForm.score" @click="submitCsat">
                  {{ submittingCsat ? 'Submitting…' : 'Submit Feedback' }}
                </button>
              </div>
            </Card>
          </div>

          <!-- Sidebar -->
          <div class="space-y-4">
            <Card title="Details">
              <dl class="space-y-3 text-sm">
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
                <div>
                  <dt class="text-muted text-xs uppercase tracking-wide">Last Updated</dt>
                  <dd class="text-primary mt-0.5">{{ formatDateTime(ticket.updated_at) }}</dd>
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
          </div>
        </div>
      </template>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PaperClipIcon } from '@heroicons/vue/24/outline'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'
import { ticketsAPI } from '@/services/api'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'

const route = useRoute()
const notify = useNotification()

const loading = ref(false)
const error = ref(null)
const ticket = ref(null)
const messages = ref([])
const replyBody = ref('')
const sendingReply = ref(false)
const uploadStatus = ref('')
const csatForm = ref({ score: null, comment: '' })
const submittingCsat = ref(false)

const showCsatForm = computed(() => {
  if (!ticket.value) return false
  const status = ticket.value.status
  return (status === 'resolved' || status === 'closed') && !ticket.value.csat
})

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
    const { data } = await ticketsAPI.detail(route.params.id)
    ticket.value = data
    messages.value = data.messages ?? []
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
    await ticketsAPI.reply(route.params.id, { body: replyBody.value })
    replyBody.value = ''
    notify.success('Reply sent.')
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
    await ticketsAPI.upload(route.params.id, formData)
    uploadStatus.value = ''
    notify.success('File uploaded.')
    await loadTicket()
  } catch (e) {
    uploadStatus.value = ''
    notify.error(normalizeApiError(e).userMessage || 'Upload failed')
  }
  event.target.value = ''
}

async function submitCsat() {
  if (!csatForm.value.score) return
  submittingCsat.value = true
  try {
    await ticketsAPI.csat(route.params.id, csatForm.value)
    notify.success('Thank you for your feedback!')
    await loadTicket()
  } catch (e) {
    notify.error(normalizeApiError(e).userMessage || 'Failed to submit feedback')
  } finally {
    submittingCsat.value = false
  }
}

onMounted(loadTicket)
</script>
