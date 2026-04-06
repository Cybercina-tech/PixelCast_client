<template>
  <AppLayout>
    <div v-if="schedulesStore.loading" class="text-center py-8">Loading...</div>
    <div v-else-if="schedule" class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-primary">{{ schedule.name }}</h1>
          <p class="text-secondary">{{ schedule.description || 'No description' }}</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="handleExecute"
            class="btn-success px-4 py-2 rounded-lg"
          >
            Execute Now
          </button>
          <button
            @click="handleToggleActive"
            :class="[
              'px-4 py-2 rounded-lg',
              schedule.is_active
                ? 'btn-danger'
                : 'btn-success',
            ]"
          >
            {{ schedule.is_active ? 'Deactivate' : 'Activate' }}
          </button>
        </div>
      </div>
      
      <!-- Timeline View -->
      <Card title="Timeline View">
        <div class="timeline-container">
          <!-- Timeline Grid -->
          <div class="timeline-grid">
            <!-- Hour Labels -->
            <div class="timeline-hours">
              <div
                v-for="hour in 24"
                :key="hour"
                class="timeline-hour-label"
              >
                {{ String(hour - 1).padStart(2, '0') }}:00
              </div>
            </div>
            
            <!-- Timeline Canvas -->
            <div class="timeline-canvas">
              <!-- Grid Lines -->
              <div class="timeline-grid-lines">
                <div
                  v-for="hour in 24"
                  :key="hour"
                  class="timeline-grid-line"
                ></div>
              </div>
              
              <!-- Current Time Indicator -->
              <div
                class="timeline-current-time"
                :style="{ left: `${getCurrentTimePosition()}%` }"
              >
                <div class="timeline-current-time-line"></div>
                <div class="timeline-current-time-label">
                  Now
                </div>
              </div>
              
              <!-- Event Blocks -->
              <div class="timeline-events">
                <div
                  v-for="(event, index) in timelineEvents"
                  :key="event.id || index"
                  class="timeline-event-block"
                  :class="`event-color-${index % 3}`"
                  :style="getEventBlockStyle(event)"
                  :draggable="true"
                  @dragstart="handleDragStart($event, event)"
                  @dragend="handleDragEnd"
                >
                  <div class="event-block-content">
                    <div class="event-block-title">{{ event.name || 'Scheduled Event' }}</div>
                    <div class="event-block-time">{{ formatEventTime(event.start_time) }} - {{ formatEventTime(event.end_time) }}</div>
                  </div>
                </div>
              </div>
              
              <!-- Drop Zones -->
              <div
                v-for="hour in 24"
                :key="`drop-${hour}`"
                class="timeline-drop-zone"
                :class="{ 'drop-zone-active': isDragging && activeDropZone === hour - 1 }"
                :style="{ left: `${((hour - 1) / 24) * 100}%` }"
                @dragover.prevent="handleDragOver($event, hour - 1)"
                @dragleave="handleDragLeave"
                @drop.prevent="handleDrop($event, hour - 1)"
              ></div>
            </div>
          </div>
        </div>
      </Card>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Schedule Information">
          <dl class="space-y-3">
            <div>
              <dt class="text-sm font-medium text-muted">Template</dt>
              <dd class="mt-1 text-sm text-primary">{{ schedule.template?.name || 'N/A' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Start Time</dt>
              <dd class="mt-1 text-sm text-primary">{{ formatDate(schedule.start_time) }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">End Time</dt>
              <dd class="mt-1 text-sm text-primary">{{ formatDate(schedule.end_time) }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Repeat</dt>
              <dd class="mt-1 text-sm text-primary capitalize">{{ schedule.repeat_type || 'none' }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-muted">Status</dt>
              <dd class="mt-1">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    schedule.is_active ? 'badge-success' : 'badge-info',
                  ]"
                >
                  {{ schedule.is_active ? 'Active' : 'Inactive' }}
                </span>
              </dd>
            </div>
          </dl>
        </Card>
        
        <Card title="Assigned Screens">
          <div v-if="schedule.screens && schedule.screens.length > 0" class="space-y-2">
            <div
              v-for="screen in schedule.screens"
              :key="screen.id"
              class="p-2 bg-card rounded"
            >
              {{ screen.name }} ({{ screen.device_id }})
            </div>
          </div>
          <div v-else class="text-center text-muted py-4">
            No screens assigned
          </div>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSchedulesStore } from '@/stores/schedules'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/common/Card.vue'

const route = useRoute()
const schedulesStore = useSchedulesStore()
const notify = useNotification()

const schedule = computed(() => schedulesStore.currentSchedule)

// Timeline state
const isDragging = ref(false)
const draggedEvent = ref(null)
const activeDropZone = ref(null)
const currentTime = ref(new Date())

// Update current time every minute
let timeInterval = null
onMounted(() => {
  const updateTime = () => {
    currentTime.value = new Date()
  }
  updateTime()
  timeInterval = setInterval(updateTime, 60000) // Update every minute
})

// Cleanup interval on unmount
onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})

// Timeline events (convert schedule to timeline events)
const timelineEvents = computed(() => {
  if (!schedule.value) return []
  
  return [{
    id: schedule.value.id,
    name: schedule.value.name,
    start_time: schedule.value.start_time,
    end_time: schedule.value.end_time,
    template: schedule.value.template,
  }]
})

// Get current time position in timeline (0-100%)
const getCurrentTimePosition = () => {
  const now = currentTime.value
  const hours = now.getHours()
  const minutes = now.getMinutes()
  return ((hours + minutes / 60) / 24) * 100
}

// Get event block style (position and width)
const getEventBlockStyle = (event) => {
  if (!event.start_time || !event.end_time) return {}
  
  const start = new Date(event.start_time)
  const end = new Date(event.end_time)
  
  const startHours = start.getHours() + start.getMinutes() / 60
  const endHours = end.getHours() + end.getMinutes() / 60
  
  const left = (startHours / 24) * 100
  const width = ((endHours - startHours) / 24) * 100
  
  return {
    left: `${left}%`,
    width: `${width}%`,
  }
}

// Format event time
const formatEventTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

// Drag and drop handlers
const handleDragStart = (event, scheduleEvent) => {
  isDragging.value = true
  draggedEvent.value = scheduleEvent
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', '')
  
  // Add ghost shadow class
  event.target.classList.add('dragging')
}

const handleDragEnd = (event) => {
  isDragging.value = false
  activeDropZone.value = null
  draggedEvent.value = null
  event.target.classList.remove('dragging')
}

const handleDragOver = (event, hour) => {
  event.preventDefault()
  activeDropZone.value = hour
  event.dataTransfer.dropEffect = 'move'
}

const handleDragLeave = () => {
  activeDropZone.value = null
}

const handleDrop = async (event, hour) => {
  event.preventDefault()
  activeDropZone.value = null
  
  if (!draggedEvent.value) return
  
  // Calculate new start time based on drop position
  const newStartTime = new Date(schedule.value.start_time)
  newStartTime.setHours(hour, 0, 0, 0)
  
  // Calculate duration
  const start = new Date(schedule.value.start_time)
  const end = new Date(schedule.value.end_time)
  const duration = end - start
  
  const newEndTime = new Date(newStartTime.getTime() + duration)
  
  try {
    await schedulesStore.updateSchedule(schedule.value.id, {
      start_time: newStartTime.toISOString(),
      end_time: newEndTime.toISOString(),
    })
    notify.success('Schedule updated')
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to update schedule')
  }
  
  isDragging.value = false
  draggedEvent.value = null
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const handleExecute = async () => {
  try {
    await schedulesStore.executeSchedule(schedule.value.id)
    notify.success('Schedule executed successfully')
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to execute schedule')
  }
}

const handleToggleActive = async () => {
  try {
    await schedulesStore.updateSchedule(schedule.value.id, {
      is_active: !schedule.value.is_active,
    })
    notify.success(`Schedule ${schedule.value.is_active ? 'deactivated' : 'activated'}`)
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to update schedule')
  }
}

onMounted(async () => {
  const scheduleId = route.params.id
  await schedulesStore.fetchSchedule(scheduleId)
})
</script>

<style scoped>
/* Timeline Container */
.timeline-container {
  @apply w-full;
}

.timeline-grid {
  @apply relative;
  min-height: 400px;
}

/* Timeline Hours Labels */
.timeline-hours {
  @apply flex justify-between mb-2;
  padding-left: 60px; /* Space for hour labels */
}

.timeline-hour-label {
  font-size: 0.75rem; /* text-xs equivalent */
  color: var(--text-muted);
  flex: 1;
  text-align: center;
}

/* Timeline Canvas */
.timeline-canvas {
  @apply relative;
  height: 300px;
  margin-left: 60px; /* Space for hour labels */
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

/* Timeline Grid Lines - Very Thin Light Grey */
.timeline-grid-lines {
  @apply absolute inset-0;
  background-image: 
    repeating-linear-gradient(
      to right,
      transparent,
      transparent calc(100% / 24 - 1px),
      var(--grid-color) calc(100% / 24 - 1px),
      var(--grid-color) calc(100% / 24)
    );
}

.dark .timeline-grid-lines {
  background-image: 
    repeating-linear-gradient(
      to right,
      transparent,
      transparent calc(100% / 24 - 1px),
      rgba(255, 255, 255, 0.1) calc(100% / 24 - 1px),
      rgba(255, 255, 255, 0.1) calc(100% / 24)
    );
}

.timeline-grid-line {
  @apply absolute top-0 bottom-0;
  width: 1px;
  background: var(--grid-color);
}

.dark .timeline-grid-line {
  background: rgba(255, 255, 255, 0.1);
}

/* Current Time Indicator - Using accent color */
.timeline-current-time {
  @apply absolute top-0 bottom-0 pointer-events-none;
  width: 2px;
  z-index: 10;
}

.timeline-current-time-line {
  @apply absolute top-0 bottom-0 w-full;
  background: var(--accent-color);
  box-shadow: 0 0 4px rgba(9, 132, 227, 0.4);
}

.timeline-current-time-label {
  @apply absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full;
  @apply px-2 py-1 rounded text-xs font-medium;
  background: var(--accent-color);
  color: var(--button-text);
  white-space: nowrap;
  margin-bottom: 4px;
}

.dark .timeline-current-time-line {
  box-shadow: 0 0 6px rgba(9, 132, 227, 0.6);
}

.dark .timeline-current-time-label {
  /* Same accent color works in both themes */
}

/* Event Blocks - Pastel Palette with 2px Rounded Corners */
.timeline-events {
  @apply absolute inset-0;
  padding: 8px;
}

.timeline-event-block {
  @apply absolute top-2 bottom-2 rounded cursor-move;
  border-radius: 2px;
  padding: 8px 12px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.timeline-event-block:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

/* Pastel Color Palette - Using theme-aware colors */
.event-color-0 {
  background: var(--card-bg);
  border-left: 3px solid var(--accent-color);
  opacity: 0.9;
}

.event-color-1 {
  background: var(--card-bg);
  border-left: 3px solid var(--accent-color);
  opacity: 0.85;
}

.event-color-2 {
  background: var(--card-bg);
  border-left: 3px solid var(--accent-color);
  opacity: 0.8;
}

.dark .event-color-0 {
  background: rgba(9, 132, 227, 0.2);
  border-left-color: var(--accent-color);
}

.dark .event-color-1 {
  background: rgba(9, 132, 227, 0.15);
  border-left-color: var(--accent-color);
}

.dark .event-color-2 {
  background: rgba(9, 132, 227, 0.1);
  border-left-color: var(--accent-color);
}

/* Event Block Content - Using theme text colors */
.event-block-content {
  @apply h-full flex flex-col justify-center;
}

.event-block-title {
  @apply text-sm font-semibold;
  color: var(--text-main);
  margin-bottom: 4px;
}

.event-block-time {
  @apply text-xs;
  color: var(--text-muted);
}

.dark .event-block-title {
  color: var(--text-main);
}

.dark .event-block-time {
  color: var(--text-muted);
}

/* Drag and Drop - Ghost Shadow */
.timeline-event-block.dragging {
  opacity: 0.5;
  transform: scale(0.95);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.2),
    0 0 0 2px rgba(9, 132, 227, 0.3);
  z-index: 100;
}

/* Drop Zones - Soft Amber Glow */
.timeline-drop-zone {
  @apply absolute top-0 bottom-0 pointer-events-none;
  width: calc(100% / 24);
  transition: all 0.3s ease;
  border: 2px dashed transparent;
}

.timeline-drop-zone.drop-zone-active {
  background: rgba(245, 158, 11, 0.1); /* Soft Amber */
  border-color: rgba(245, 158, 11, 0.4);
  box-shadow: 
    inset 0 0 20px rgba(245, 158, 11, 0.2),
    0 0 20px rgba(245, 158, 11, 0.3);
  pointer-events: all;
}

.dark .timeline-drop-zone.drop-zone-active {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.5);
  box-shadow: 
    inset 0 0 30px rgba(245, 158, 11, 0.3),
    0 0 30px rgba(245, 158, 11, 0.4);
}
</style>
