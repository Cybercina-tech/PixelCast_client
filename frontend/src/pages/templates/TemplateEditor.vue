<template>
  <AppLayout>
    <div v-if="loading" class="template-editor h-full min-h-0 w-full flex items-center justify-center bg-editor-workspace dark:bg-gray-900 text-primary dark:text-white overflow-hidden">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-color mx-auto mb-4"></div>
        <p class="text-muted">Loading template...</p>
      </div>
    </div>
    <div v-else class="template-editor h-full min-h-0 w-full flex flex-col bg-editor-workspace dark:bg-gray-900 text-primary dark:text-white overflow-hidden">
      <div
        v-if="!canEditTemplates"
        class="px-4 py-2.5 bg-amber-500/10 border-b border-amber-500/35 text-amber-100 text-sm text-center shrink-0"
        role="status"
      >
        Read-only: you can explore the canvas; changes are not saved to the server.
      </div>
      <!-- Top Toolbar -->
      <div class="shrink-0 flex flex-col gap-2 px-3 py-2.5 sm:px-4 sm:py-3 bg-card border-b border-border-color">
        <div class="flex items-center gap-2 min-w-0">
          <button
            @click="goBack"
            class="btn-outline px-2.5 sm:px-3 py-2 active:scale-95 rounded-lg text-sm font-medium transition-all duration-400 flex items-center gap-2 shrink-0"
            title="Back to Templates List"
          >
            <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span class="hidden sm:inline">Back to List</span>
          </button>
          <h1 class="text-base sm:text-xl font-semibold text-primary truncate min-w-0 flex-1">{{ templateName || 'Untitled Template' }}</h1>
          <button
            @click="saveTemplate"
            :disabled="saving || !canEditTemplates"
            :title="!canEditTemplates ? 'Your account cannot save templates' : ''"
            class="btn-primary px-3 sm:px-4 py-2 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-xs sm:text-sm font-medium transition-all duration-400 shrink-0"
          >
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
          <div class="hidden lg:flex items-center gap-2 flex-wrap">
            <button
              @click="exportJSON"
              class="btn-outline px-3 sm:px-4 py-2 active:scale-95 rounded-lg text-sm font-medium transition-all duration-400"
            >
              Export JSON
            </button>
            <button
              @click="deleteSelectedWidget"
              :disabled="!selectedWidgetId"
              class="px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all duration-400 border border-red-200 dark:border-red-500/60 text-red-600 dark:text-red-300 hover:bg-red-500/10 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Delete selected object"
            >
              Delete
            </button>
            <button
              v-if="templateId && canEditTemplates"
              @click="handlePushToScreen"
              :disabled="saving || pushing"
              class="btn-secondary px-3 sm:px-4 py-2 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-all duration-400 flex items-center gap-2"
            >
              <svg v-if="!pushing" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <div v-else class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              {{ pushing ? 'Pushing...' : 'Push to Screen' }}
            </button>
          </div>
          <button
            type="button"
            class="lg:hidden btn-outline p-2 rounded-lg shrink-0"
            aria-label="More actions"
            @click="showMobileToolbarMore = !showMobileToolbarMore"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
            </svg>
          </button>
          <div class="hidden lg:flex items-center gap-2 text-sm text-muted ml-auto">
            <button
              type="button"
              @click="rightPanelCollapsed = !rightPanelCollapsed"
              class="btn-outline px-2 py-1 rounded text-xs"
              :title="rightPanelCollapsed ? 'Expand inspector panel' : 'Collapse inspector panel'"
            >
              {{ rightPanelCollapsed ? 'Show Inspector' : 'Hide Inspector' }}
            </button>
          </div>
        </div>
        <div
          v-if="showMobileToolbarMore"
          class="lg:hidden flex flex-wrap gap-2 pt-2 border-t border-border-color/70"
        >
          <button
            type="button"
            @click="showMobileToolbarMore = false; exportJSON()"
            class="btn-outline px-3 py-2 rounded-lg text-sm font-medium"
          >
            Export JSON
          </button>
          <button
            type="button"
            @click="showMobileToolbarMore = false; deleteSelectedWidget()"
            :disabled="!selectedWidgetId"
            class="px-3 py-2 rounded-lg text-sm font-medium border border-red-200 dark:border-red-500/60 text-red-600 dark:text-red-300 disabled:opacity-40"
          >
            Delete
          </button>
          <button
            v-if="templateId && canEditTemplates"
            type="button"
            @click="showMobileToolbarMore = false; handlePushToScreen()"
            :disabled="saving || pushing"
            class="btn-secondary px-3 py-2 rounded-lg text-sm font-medium"
          >
            Push to Screen
          </button>
        </div>
      </div>

      <!-- Main Editor Area -->
      <div class="flex-1 flex overflow-hidden min-h-0">
        <!-- Left: Widget Library (desktop) -->
        <div class="hidden lg:flex lg:flex-col h-full w-56 shrink-0 border-r border-border-color">
          <WidgetLibraryPanel
            :sections="widgetLibrarySections"
            :widget-section-card-style="widgetSectionCardStyle"
            :widget-section-header-style="widgetSectionHeaderStyle"
            :is-widget-section-open="isWidgetSectionOpen"
            :toggle-widget-section="toggleWidgetSection"
            @add-widget="addWidget"
          />
        </div>

        <Teleport to="body">
          <div
            v-if="!isDesktopLayout && mobileLibraryOpen"
            class="fixed inset-0 z-[56] lg:hidden"
          >
            <div
              class="absolute inset-0 bg-black/50 backdrop-blur-sm"
              aria-hidden="true"
              @click="mobileLibraryOpen = false"
            />
            <aside
              class="absolute left-0 top-0 bottom-0 w-[min(100%,20rem)] max-w-[100vw] flex flex-col shadow-2xl border-r border-border-color bg-card"
              style="padding-top: max(0.5rem, env(safe-area-inset-top))"
              role="dialog"
              aria-modal="true"
              aria-label="Widget library"
            >
              <WidgetLibraryPanel
                :sections="widgetLibrarySections"
                :widget-section-card-style="widgetSectionCardStyle"
                :widget-section-header-style="widgetSectionHeaderStyle"
                :is-widget-section-open="isWidgetSectionOpen"
                :toggle-widget-section="toggleWidgetSection"
                @add-widget="(t) => { addWidget(t); mobileLibraryOpen = false }"
              >
                <template #headerEnd>
                  <button
                    type="button"
                    class="btn-outline px-2 py-1 rounded text-xs shrink-0"
                    @click="mobileLibraryOpen = false"
                  >
                    Close
                  </button>
                </template>
              </WidgetLibraryPanel>
            </aside>
          </div>
        </Teleport>

        <!-- Center: Canvas Area -->
        <div class="flex-1 flex flex-col bg-editor-workspace dark:bg-gray-900 overflow-hidden">
          <div
            ref="canvasContainer"
            class="relative flex-1 overflow-hidden bg-editor-matte dark:bg-gray-700 flex items-center justify-center touch-manipulation"
            @wheel.prevent="handleWheel"
          >
            <!-- Monitor Frame (Wall-Mounted Display) -->
            <div
              ref="canvasWrapper"
              class="relative monitor-frame"
              :style="{
                padding: '12px',
                width: `${canvasWidth + 24}px`,
                height: `${canvasHeight + 24}px`,
                transform: `scale(${scale})`,
                transformOrigin: 'center center',
                flexShrink: 0
              }"
            >
              <!-- Power Indicator Light -->
              <div class="power-indicator absolute bottom-3 right-5 w-2 h-2 bg-green-400 rounded-full"></div>
              
              <!-- Canvas Background -->
              <div
                ref="canvasArea"
                class="relative canvas-area rounded overflow-hidden"
                :style="{
                  width: `${canvasWidth}px`,
                  height: `${canvasHeight}px`,
                  backgroundImage: canvasBackgroundImage
                        ? `url(${canvasBackgroundImage})`
                        : undefined,
                  backgroundSize: canvasBackgroundImage ? 'cover' : undefined,
                  backgroundColor: canvasBackgroundImage ? canvasBackgroundColor : undefined
                }"
              >
                <!-- Empty State Watermark -->
                <div
                  v-if="widgets.length === 0"
                  class="absolute inset-0 flex items-center justify-center pointer-events-none"
                >
                  <span class="text-muted text-lg font-light opacity-50 select-none">
                    Drag widgets here to start
                  </span>
                </div>
                <!-- Render Widgets -->
                <div
                  v-for="widget in sortedWidgetsByZIndex"
                  :key="widget.id"
                  :ref="el => setWidgetRef(el, widget.id)"
                  :data-widget-id="widget.id"
                  class="widget-element absolute cursor-move"
                  :class="{ 'widget-selected': selectedWidgetId === widget.id }"
                  :style="getWidgetStyle(widget)"
                  @click.stop="selectWidget(widget.id)"
                >
                  <!-- Widget Content Preview -->
                  <WidgetPreview :widget="widget" />
                </div>

                <!-- Moveable Component -->
                <Moveable
                  v-if="selectedWidget"
                  ref="moveableRef"
                  :target="selectedWidgetElement"
                  :draggable="true"
                  :resizable="true"
                  :rotatable="true"
                  :scalable="false"
                  :snappable="true"
                  :snapThreshold="5"
                  :snapGap="false"
                  :snapElement="true"
                  :snapVertical="true"
                  :snapHorizontal="true"
                  :snapCenter="true"
                  :elementGuidelines="widgetElements"
                  :bounds="canvasBounds"
                  :zoom="1 / scale"
                  :persistRect="true"
                  :keepRatio="false"
                  :edge="false"
                  :throttleDrag="0"
                  :throttleResize="1"
                  :throttleRotate="0"
                  @dragStart="handleDragMoveableStart"
                  @drag="handleDrag"
                  @dragEnd="handleDragEnd"
                  @resizeStart="handleResizeStart"
                  @resize="handleResize"
                  @resizeEnd="handleResizeEnd"
                  @rotate="handleRotate"
                  @rotateEnd="handleRotateEnd"
                />
              </div>
            </div>
            <div class="absolute bottom-4 right-4 z-20 flex items-center gap-2 rounded-lg border border-border-color bg-card/95 px-3 py-2 text-xs text-muted max-w-[calc(100vw-1rem)] flex-wrap justify-end" style="bottom: max(1rem, env(safe-area-inset-bottom)); right: max(1rem, env(safe-area-inset-right))">
              <span>{{ canvasWidth }}×{{ canvasHeight }}</span>
              <span>|</span>
              <button class="btn-outline px-2 py-1 rounded" @click="zoomOut">-</button>
              <span class="w-10 text-center">{{ Math.round(scale * 100) }}%</span>
              <button class="btn-outline px-2 py-1 rounded" @click="zoomIn">+</button>
              <button class="btn-outline px-2 py-1 rounded" @click="calculateScale">Fit</button>
            </div>
          </div>

        <!-- Mobile: quick access dock -->
        <div
          class="lg:hidden shrink-0 flex border-t border-border-color bg-card/95 backdrop-blur-md z-[40]"
          style="padding-bottom: max(0.5rem, env(safe-area-inset-bottom))"
        >
          <button
            type="button"
            class="flex-1 py-3 text-xs font-medium text-primary border-r border-border-color/80 active:bg-surface-inset"
            @click="openMobileLibrary"
          >
            Widgets
          </button>
          <button
            type="button"
            class="flex-1 py-3 text-xs font-medium text-primary active:bg-surface-inset"
            @click="openMobileInspector"
          >
            Inspector
          </button>
        </div>

        </div>

        <!-- Right: Inspector (desktop) -->
        <div
          class="hidden lg:flex lg:flex-col h-full bg-card border-l border-border-color transition-all duration-200 shrink-0"
          :class="rightPanelCollapsed ? 'w-14' : 'w-80'"
        >
          <div class="bg-card border-b border-border-color px-4 py-3 shrink-0">
            <h2 v-if="!rightPanelCollapsed" class="text-lg font-semibold text-primary">Inspector</h2>
            <h2 v-else class="text-xs font-semibold text-primary uppercase tracking-wide">Panel</h2>
          </div>
          <TemplateInspectorPanel />
        </div>

        <Teleport to="body">
          <div
            v-if="!isDesktopLayout && mobileInspectorOpen"
            class="fixed inset-0 z-[56] lg:hidden flex justify-end"
          >
            <div
              class="absolute inset-0 bg-black/50 backdrop-blur-sm"
              aria-hidden="true"
              @click="mobileInspectorOpen = false"
            />
            <aside
              class="relative w-[min(100%,22rem)] max-w-[100vw] h-full flex flex-col bg-card border-l border-border-color shadow-2xl"
              style="padding-top: max(0.5rem, env(safe-area-inset-top))"
              role="dialog"
              aria-modal="true"
              aria-label="Inspector"
            >
              <div class="flex items-center justify-between gap-2 px-4 py-3 border-b border-border-color shrink-0">
                <h2 class="text-lg font-semibold text-primary">Inspector</h2>
                <button
                  type="button"
                  class="btn-outline px-3 py-1.5 rounded-lg text-sm"
                  @click="mobileInspectorOpen = false"
                >
                  Close
                </button>
              </div>
              <div class="flex-1 min-h-0 flex flex-col overflow-hidden">
                <TemplateInspectorPanel />
              </div>
            </aside>
          </div>
        </Teleport>

      </div>

    <!-- Media Library Modal -->
    <MediaLibraryModal
      :show="showMediaLibrary"
      :filter-by-type="mediaLibraryFilterType"
      :widget-id="selectedWidget?.id"
      @close="showMediaLibrary = false"
      @select="handleMediaSelect"
    />

    <!-- Push to Screen Modal -->
    <PushToScreenModal
      :show="showPushModal"
      :template="currentTemplate"
      :online-screens="onlineScreens"
      :loading="pushing"
      @close="showPushModal = false"
      @select="handlePushToScreenSelect"
    />
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch, provide, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTemplatesStore } from '@/stores/templates'
import { useNotification } from '@/composables/useNotification'
import { normalizeApiError } from '@/utils/apiError'
import Moveable from 'vue3-moveable'
import AppLayout from '@/components/layout/AppLayout.vue'
import WidgetPreview from './components/WidgetPreview.vue'
import WidgetLibraryPanel from './components/WidgetLibraryPanel.vue'
import TemplateInspectorPanel from './components/TemplateInspectorPanel.vue'
import { TEMPLATE_EDITOR_INJECTION_KEY } from './templateEditorInjectionKey'
import MediaLibraryModal from '@/components/common/MediaLibraryModal.vue'
import PushToScreenModal from '@/components/templates/PushToScreenModal.vue'
import { useScreensStore } from '@/stores/screens'
import { useAuthStore } from '@/stores/auth'
import { hasPermission } from '@/utils/permissions'
import { resolveWidgetBackgroundColor } from '@/utils/widgetBackground'
import { WIDGET_FONT_OPTIONS } from '@/constants/widgetFonts'
import {
  COUNTDOWN_THEMES,
  getCountdownThemePreset,
  COUNTDOWN_THEME_DEFAULT_ID,
} from '@/constants/countdownThemes'

const route = useRoute()
const router = useRouter()
const templatesStore = useTemplatesStore()
const screensStore = useScreensStore()
const authStore = useAuthStore()
const notify = useNotification()

const canEditTemplates = computed(() => hasPermission(authStore.user, 'edit_templates'))

// Expose Math for template usage
const Math = window.Math

// Template ID from route params (if editing existing template)
const templateId = computed(() => route.params.id)

// Template state - Initialize from query params if available
const templateName = ref(route.query.name || 'New Template')
const canvasWidth = ref(parseInt(route.query.width) || 1920)
const canvasHeight = ref(parseInt(route.query.height) || 1080)
const canvasBackgroundColor = ref('#ffffff')
const canvasBackgroundImage = ref('')
const targetScreenId = ref(route.query.screen_id || null)
const saving = ref(false)
const loading = ref(false)
const pushing = ref(false)
const showPushModal = ref(false)
const currentTemplate = ref(null)

// Widgets array
const widgets = ref([])

// Selected widget
const selectedWidgetId = ref(null)
const selectedWidget = computed(() => {
  return widgets.value.find(w => w.id === selectedWidgetId.value)
})

const webviewUrlDraft = ref('')
watch(
  () => [selectedWidgetId.value, selectedWidget.value?.type, selectedWidget.value?.content],
  () => {
    const w = selectedWidget.value
    if (w?.type === 'webview') {
      webviewUrlDraft.value = typeof w.content === 'string' ? w.content : ''
    } else {
      webviewUrlDraft.value = ''
    }
  },
  { immediate: true }
)

const albumQueueItems = computed(() => {
  const widget = selectedWidget.value
  if (!widget || widget.type !== 'album') return []
  const playlist = Array.isArray(widget.style?.playlist) ? widget.style.playlist : []
  return playlist
})

const toDatetimeLocalValue = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const fromDatetimeLocalToIso = (local) => {
  if (!local) return ''
  const d = new Date(local)
  return Number.isNaN(d.getTime()) ? '' : d.toISOString()
}

const countdownTargetLocal = computed(() => {
  const w = selectedWidget.value
  if (!w || w.type !== 'countdown') return ''
  return toDatetimeLocalValue(w.style?.targetAt)
})

const countdownStartLocal = computed(() => {
  const w = selectedWidget.value
  if (!w || w.type !== 'countdown') return ''
  return toDatetimeLocalValue(w.style?.startAt)
})

const onCountdownTargetAtInput = (local) => {
  updateWidgetStyle('targetAt', fromDatetimeLocalToIso(local))
}

const onCountdownStartAtInput = (local) => {
  updateWidgetStyle('startAt', local ? fromDatetimeLocalToIso(local) : '')
}

const updateCountdownLabel = (key, value) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'countdown') return
  if (!selectedWidget.value.style) selectedWidget.value.style = {}
  if (!selectedWidget.value.style.labels) selectedWidget.value.style.labels = {}
  selectedWidget.value.style.labels[key] = value
}

const countdownIsCustomTheme = computed(() => {
  const w = selectedWidget.value
  if (!w || w.type !== 'countdown') return false
  return (w.style?.theme || COUNTDOWN_THEME_DEFAULT_ID) === 'custom'
})

const countdownThemeHint = computed(() => {
  const w = selectedWidget.value
  if (!w || w.type !== 'countdown') return ''
  const id = w.style?.theme || COUNTDOWN_THEME_DEFAULT_ID
  const entry = COUNTDOWN_THEMES.find((t) => t.id === id)
  return entry?.hint || ''
})

const applyCountdownTheme = (themeId) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'countdown') return
  if (!selectedWidget.value.style) selectedWidget.value.style = {}
  if (themeId === 'custom') {
    selectedWidget.value.style = {
      ...selectedWidget.value.style,
      theme: 'custom',
    }
    return
  }
  const entry = COUNTDOWN_THEMES.find((t) => t.id === themeId)
  selectedWidget.value.style = {
    ...selectedWidget.value.style,
    theme: themeId,
    ...(entry?.preset || {}),
  }
}

// Widget visibility state (default to visible)
const widgetVisibility = ref({})

// Drag and drop state
const draggingWidgetId = ref(null)
const dragOverWidgetId = ref(null)

// Widget name editing state
const editingWidgetId = ref(null)
const editingWidgetName = ref('')
const widgetNameInput = ref(null)

// Media Library Modal state
const showMediaLibrary = ref(false)
const mediaLibraryFilterType = ref(null)
const rightPanelCollapsed = ref(false)
const rightPanelTab = ref('properties')
const isDesktopLayout = ref(
  typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)').matches : true
)
const mobileLibraryOpen = ref(false)
const mobileInspectorOpen = ref(false)
const showMobileToolbarMore = ref(false)
let desktopLayoutMql = null

function openMobileLibrary() {
  mobileInspectorOpen.value = false
  rightPanelCollapsed.value = false
  mobileLibraryOpen.value = true
}

function openMobileInspector() {
  mobileLibraryOpen.value = false
  rightPanelCollapsed.value = false
  mobileInspectorOpen.value = true
}

/** Pinch-zoom state (touch handlers attached in onMounted) */
const pinchZoomState = { startDist: 0, startScale: 1, active: false }

function canvasTouchDistance(touchList) {
  if (touchList.length < 2) return 0
  const a = touchList[0]
  const b = touchList[1]
  return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
}
const defaultTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
const widgetLibrarySections = [
  {
    id: 'date-time',
    label: 'Date & Time',
    items: [
      { type: 'clock', label: 'Add Clock', iconPath: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
      { type: 'date', label: 'Add Date', iconPath: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
      { type: 'weekday', label: 'Add Weekday', iconPath: 'M8 7V3m8 4V3m-9 9h10m-8 5h6M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
      { type: 'countdown', label: 'Add Countdown', iconPath: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41' },
    ]
  },
  {
    id: 'text-live',
    label: 'Text & Live Info',
    items: [
      { type: 'text', label: 'Add Text', iconPath: 'M4 6h16M4 12h16M4 18h7' },
      { type: 'marquee', label: 'Add Marquee', iconPath: 'M4 12h16M4 7h7m6 0h3M4 17h5m8 0h3' },
      { type: 'weather', label: 'Add Weather', iconPath: 'M3 15a4 4 0 014-4h.26A6 6 0 0119 13h1a3 3 0 010 6H7a4 4 0 01-4-4z' },
      { type: 'qr_action', label: 'Add QR Action', iconPath: 'M4 4h5v5H4V4zm11 0h5v5h-5V4zM4 15h5v5H4v-5zm2-9h1v1H6V6zm10 0h1v1h-1V6zm-1 10h5v1h-5v-1zm-1-5h1v3h-1v-3zm-3 0h2v1h-2v-1zm-1 2h1v1h-1v-1zm2 2h1v1h-1v-1zm-2 2h2v1h-2v-1z' },
    ]
  },
  {
    id: 'media',
    label: 'Media',
    items: [
      { type: 'image', label: 'Add Image', iconPath: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
      { type: 'video', label: 'Add Video', iconPath: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' },
      { type: 'album', label: 'Add Album Playlist', iconPath: 'M4 7h16M4 12h16M4 17h10m4 0h2M8 7v10M16 7v10' },
    ]
  },
  {
    id: 'web-data',
    label: 'Web & Data',
    items: [
      { type: 'webview', label: 'Add Webview', iconPath: 'M21 12H3m0 0l4-4m-4 4l4 4m14-4l-4-4m4 4l-4 4' },
      { type: 'chart', label: 'Add Chart', iconPath: 'M3 3v18h18M8 13l3-3 3 2 4-5' },
    ]
  },
]
const widgetSectionOpenState = ref({
  'date-time': true,
  'text-live': true,
  media: true,
  'web-data': false,
})
const isWidgetSectionOpen = (sectionId) => widgetSectionOpenState.value[sectionId] !== false
const toggleWidgetSection = (sectionId) => {
  widgetSectionOpenState.value = {
    ...widgetSectionOpenState.value,
    [sectionId]: !isWidgetSectionOpen(sectionId),
  }
}

/** Antler widget library — category border + header tint (CSS variables in style.css) */
const WIDGET_SECTION_ACCENT = {
  'date-time': { accent: '--widget-section-date-time', tint: '--widget-section-date-time-bg' },
  'text-live': { accent: '--widget-section-text-live', tint: '--widget-section-text-live-bg' },
  media: { accent: '--widget-section-media', tint: '--widget-section-media-bg' },
  'web-data': { accent: '--widget-section-web-data', tint: '--widget-section-web-data-bg' },
}
const widgetSectionCardStyle = (sectionId) => {
  const t = WIDGET_SECTION_ACCENT[sectionId]
  if (!t) return {}
  return {
    borderLeftWidth: '4px',
    borderLeftStyle: 'solid',
    borderLeftColor: `var(${t.accent})`,
  }
}
const widgetSectionHeaderStyle = (sectionId) => {
  const t = WIDGET_SECTION_ACCENT[sectionId]
  if (!t) return {}
  return { backgroundColor: `var(${t.tint})` }
}

const worldTimeZones = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
  { value: 'Asia/Tehran', label: 'Tehran (Asia/Tehran)' },
  { value: 'Asia/Dubai', label: 'Dubai (Asia/Dubai)' },
  { value: 'Europe/London', label: 'London (Europe/London)' },
  { value: 'Europe/Paris', label: 'Paris (Europe/Paris)' },
  { value: 'Europe/Berlin', label: 'Berlin (Europe/Berlin)' },
  { value: 'America/New_York', label: 'New York (America/New_York)' },
  { value: 'America/Chicago', label: 'Chicago (America/Chicago)' },
  { value: 'America/Los_Angeles', label: 'Los Angeles (America/Los_Angeles)' },
  { value: 'America/Toronto', label: 'Toronto (America/Toronto)' },
  { value: 'America/Sao_Paulo', label: 'Sao Paulo (America/Sao_Paulo)' },
  { value: 'Africa/Johannesburg', label: 'Johannesburg (Africa/Johannesburg)' },
  { value: 'Asia/Kolkata', label: 'India (Asia/Kolkata)' },
  { value: 'Asia/Bangkok', label: 'Bangkok (Asia/Bangkok)' },
  { value: 'Asia/Singapore', label: 'Singapore (Asia/Singapore)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (Asia/Shanghai)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (Asia/Tokyo)' },
  { value: 'Australia/Sydney', label: 'Sydney (Australia/Sydney)' },
]

const marqueePresets = [
  { id: 'breakingNews', label: 'Breaking News', style: { color: '#ffffff', backgroundColor: '#b91c1c', fontSize: '42px', fontWeight: '800', fadeEdge: true, mode: 'continuous', direction: 'left' } },
  { id: 'stockTape', label: 'Stock Tape', style: { color: '#22c55e', backgroundColor: '#0f172a', fontSize: '32px', fontWeight: '700', separator: '  ▲  ', mode: 'continuous', direction: 'left' } },
  { id: 'sports', label: 'Sports Bar', style: { color: '#fde047', backgroundColor: '#1f2937', fontSize: '36px', fontWeight: '700', separator: '  |  ', mode: 'continuous', direction: 'left' } },
  { id: 'gold', label: 'Golden Luxury', style: { color: '#fbbf24', backgroundColor: '#111827', fontSize: '40px', fontWeight: '700', textShadow: '0 0 16px rgba(251,191,36,0.45)', mode: 'continuous', direction: 'left' } },
  { id: 'neon', label: 'Neon Glow', style: { color: '#22d3ee', backgroundColor: '#020617', fontSize: '40px', fontWeight: '700', textShadow: '0 0 12px rgba(34,211,238,0.9)', mode: 'continuous', direction: 'left' } },
  { id: 'minimalLight', label: 'Minimal Light', style: { color: '#111827', backgroundColor: '#f8fafc', fontSize: '34px', fontWeight: '600', mode: 'continuous', direction: 'left' } },
  { id: 'alerts', label: 'Alert Banner', style: { color: '#ffffff', backgroundColor: '#dc2626', fontSize: '38px', fontWeight: '800', uppercase: true, mode: 'continuous', direction: 'left' } },
  {
    id: 'calmBlue',
    label: 'Calm Blue',
    style: {
      color: '#e8f4fc',
      backgroundColor: '#0c1b2e',
      fontSize: '34px',
      fontWeight: '600',
      letterSpacing: '0.02em',
      textShadow: '0 1px 2px rgba(0,0,0,0.45)',
      fadeEdge: true,
      separator: '  ·  ',
      mode: 'continuous',
      direction: 'left',
    },
  },
  { id: 'matrix', label: 'Matrix', style: { color: '#4ade80', backgroundColor: '#052e16', fontSize: '30px', fontWeight: '600', letterSpacing: '0.08em', mode: 'continuous', direction: 'left' } },
  { id: 'darkGlass', label: 'Dark Glass', style: { color: '#e5e7eb', backgroundColor: 'rgba(15,23,42,0.85)', fontSize: '36px', fontWeight: '700', mode: 'continuous', direction: 'left' } },
]

const supportedLocales = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'fa-IR', label: 'Persian (Iran)' },
  { value: 'ar-SA', label: 'Arabic (Saudi Arabia)' },
  { value: 'tr-TR', label: 'Turkish (Turkey)' },
  { value: 'fr-FR', label: 'French (France)' },
]

const qrWeekdayOptions = [
  { value: 0, label: 'Mon' },
  { value: 1, label: 'Tue' },
  { value: 2, label: 'Wed' },
  { value: 3, label: 'Thu' },
  { value: 4, label: 'Fri' },
  { value: 5, label: 'Sat' },
  { value: 6, label: 'Sun' },
]

const qrHourOptions = Array.from({ length: 24 }, (_, hour) => ({
  value: hour,
  label: `${String(hour).padStart(2, '0')}:00`,
}))

const clockStylePresets = [
  { id: 'digitalBoard', label: 'Digital Board', style: { preset: 'digitalBoard', color: '#e2e8f0', backgroundColor: '#0f172a', fontSize: '56px', fontWeight: '800', fontFamily: "'Segoe UI', sans-serif", textAlign: 'center', locale: 'en-US', displayMode: 'timeOnly', showWeekday: false, timeZone: defaultTimeZone } },
  { id: 'glassBlue', label: 'Glass Blue', style: { preset: 'glassBlue', color: '#dbeafe', backgroundColor: 'rgba(30,64,175,0.65)', fontSize: '54px', fontWeight: '700', textShadow: '0 0 12px rgba(30,64,175,0.6)', fontFamily: "Roboto, sans-serif", locale: 'en-US', displayMode: 'timePlusWeekday', showWeekday: true, weekdayStyle: 'short', timeZone: defaultTimeZone } },
  { id: 'minimalDark', label: 'Minimal Dark', style: { preset: 'minimalDark', color: '#f8fafc', backgroundColor: '#111827', fontSize: '52px', fontWeight: '600', fontFamily: "Arial, sans-serif", locale: 'en-US', displayMode: 'stacked', showWeekday: true, weekdayStyle: 'long', timeZone: defaultTimeZone } },
]

const dateStylePresets = [
  { id: 'calendarCard', label: 'Calendar Card', style: { preset: 'calendarCard', color: '#f8fafc', backgroundColor: '#1e293b', fontSize: '40px', fontWeight: '700', textAlign: 'center', fontFamily: "'Segoe UI', sans-serif", locale: 'en-US', displayMode: 'datePlusWeekday', showWeekday: true, weekdayStyle: 'long', dateStyle: 'medium', timeZone: defaultTimeZone } },
  { id: 'minimalLight', label: 'Minimal Light', style: { preset: 'minimalLight', color: '#0f172a', backgroundColor: '#f8fafc', fontSize: '38px', fontWeight: '600', textAlign: 'center', fontFamily: "Roboto, sans-serif", locale: 'en-US', displayMode: 'stacked', showWeekday: true, weekdayStyle: 'short', dateStyle: 'short', timeZone: defaultTimeZone } },
  { id: 'boldBanner', label: 'Bold Banner', style: { preset: 'boldBanner', color: '#fde68a', backgroundColor: '#7c2d12', fontSize: '42px', fontWeight: '800', textAlign: 'center', fontFamily: "Verdana, sans-serif", locale: 'en-US', displayMode: 'dateOnly', showWeekday: false, dateStyle: 'full', timeZone: defaultTimeZone } },
]

const weekdayStylePresets = [
  { id: 'weekdayBold', label: 'Weekday Bold', style: { preset: 'weekdayBold', color: '#ffffff', backgroundColor: '#0f172a', fontSize: '44px', fontWeight: '800', textAlign: 'center', fontFamily: "'Segoe UI', sans-serif", locale: 'en-US', weekdayStyle: 'long', timeZone: defaultTimeZone } },
  { id: 'weekdayCalm', label: 'Weekday Calm', style: { preset: 'weekdayCalm', color: '#dbeafe', backgroundColor: '#1d4ed8', fontSize: '40px', fontWeight: '700', textAlign: 'center', fontFamily: "Roboto, sans-serif", locale: 'en-US', weekdayStyle: 'short', timeZone: defaultTimeZone } },
  { id: 'weekdayLight', label: 'Weekday Light', style: { preset: 'weekdayLight', color: '#0f172a', backgroundColor: '#f8fafc', fontSize: '38px', fontWeight: '700', textAlign: 'center', fontFamily: "Arial, sans-serif", locale: 'en-US', weekdayStyle: 'narrow', timeZone: defaultTimeZone } },
]

const getMarqueeDefaultStyle = () => ({
  preset: 'breakingNews',
  mode: 'continuous',
  direction: 'left',
  speed: 120,
  gap: 80,
  stepHold: 1.5,
  bounceHold: 0.8,
  loop: true,
  reverse: false,
  fadeEdge: true,
  separator: ' • ',
  uppercase: false,
  fontFamily: "'Segoe UI', Arial, sans-serif",
  fontSize: '42px',
  fontWeight: '700',
  color: '#ffffff',
  backgroundColor: '#b91c1c',
  lineHeight: 1.2,
  letterSpacing: '0.01em',
})

const getWeatherDefaultStyle = () => ({
  location: 'Tehran,IR',
  units: 'celsius',
  layout: 'compact',
  forecastDays: 3,
  hideAfterHours: 6,
  color: '#ffffff',
  backgroundColor: '#0f172a',
})

const getAlbumDefaultStyle = () => ({
  transition: 'fade',
  transitionDurationMs: 450,
  defaultDurationSec: 10,
  gifMode: 'autoEnd',
  objectFit: 'contain',
  muted: true,
  loopPlaylist: true,
  playlist: [],
})

const getCountdownDefaultStyle = () => {
  const target = new Date()
  target.setDate(target.getDate() + 7)
  target.setHours(18, 0, 0, 0)
  const start = new Date()
  return {
    targetAt: target.toISOString(),
    startAt: start.toISOString(),
    zeroStateMode: 'showMessage',
    zeroStateMessage: 'The event has started!',
    showProgress: true,
    labels: {
      days: 'Days',
      hours: 'Hours',
      minutes: 'Minutes',
      seconds: 'Seconds',
    },
    fontSize: '36px',
    fontFamily: "'Inter', system-ui, sans-serif",
    textAlign: 'center',
    ...getCountdownThemePreset(COUNTDOWN_THEME_DEFAULT_ID),
  }
}

const getQrActionDefaultStyle = () => ({
  ctaText: 'Scan to continue',
  campaignId: '',
  defaultUrl: 'https://example.com/menu',
  redirectPath: '',
  displayUrl: '',
  logoUrl: '',
  foregroundColor: '#000000',
  backgroundColor: '#ffffff',
  textColor: '#0f172a',
  errorCorrectionLevel: 'H',
  quietZone: 4,
  rules: [
    {
      name: 'Morning Menu',
      priority: 1,
      startHour: 8,
      endHour: 12,
      daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
      targetUrl: 'https://example.com/menu-breakfast',
      isActive: true,
    },
    {
      name: 'Evening Menu',
      priority: 2,
      startHour: 12,
      endHour: 23,
      daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
      targetUrl: 'https://example.com/menu-dinner',
      isActive: true,
    },
  ],
})

const getTemporalDefaultStyle = (type) => {
  if (type === 'clock') return { ...clockStylePresets[0].style }
  if (type === 'date') return { ...dateStylePresets[0].style, format: 'YYYY-MM-DD' }
  if (type === 'weekday') return { ...weekdayStylePresets[0].style, showWeekday: true, format: 'dddd' }
  return {}
}

const applyTemporalPreset = (type, presetId) => {
  if (!selectedWidget.value || selectedWidget.value.type !== type) return
  const source = type === 'clock' ? clockStylePresets : type === 'date' ? dateStylePresets : weekdayStylePresets
  const preset = source.find((entry) => entry.id === presetId) || source[0]
  if (!preset) return
  selectedWidget.value.style = {
    ...(selectedWidget.value.style || {}),
    ...preset.style,
  }
}

// Sort widgets by z-index for display
const sortedWidgetsByZIndex = computed(() => {
  return [...widgets.value].sort((a, b) => {
    // First sort by z-index
    if (a.zIndex !== b.zIndex) {
      return a.zIndex - b.zIndex
    }
    // If z-index is same, maintain original order
    return widgets.value.indexOf(a) - widgets.value.indexOf(b)
  })
})

// Canvas scaling
const canvasContainer = ref(null)
const canvasWrapper = ref(null)
const canvasArea = ref(null)
const scale = ref(0.5)
let canvasResizeObserver = null

// Moveable references
const moveableRef = ref(null)
const selectedWidgetElement = ref(null)
const widgetRefs = ref({})
const dragStartState = ref(null)
const resizeStartState = ref(null)

// Generate unique ID
const generateId = () => {
  return `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// Set widget ref
const setWidgetRef = (el, widgetId) => {
  if (el) {
    widgetRefs.value[widgetId] = el
  }
}

// Get widget elements for snapping
const widgetElements = computed(() => {
  return widgets.value
    .filter(w => w.id !== selectedWidgetId.value)
    .map(w => widgetRefs.value[w.id])
    .filter(Boolean)
})

// Canvas bounds for Moveable (in internal/canvas coordinates)
// Using internal bounds instead of viewport bounds works better with zoom transform
// Moveable with zoom prop can handle internal coordinate bounds
const canvasBounds = computed(() => {
  return {
    left: 0,
    top: 0,
    right: canvasWidth.value,
    bottom: canvasHeight.value
  }
})

// Calculate scale to fit viewport - Auto-scale to fill available space
const calculateScale = () => {
  if (!canvasContainer.value) return

  const container = canvasContainer.value
  const margin = 32
  const containerWidth = Math.max(1, container.clientWidth - margin * 2)
  const containerHeight = Math.max(1, container.clientHeight - margin * 2)

  // Canvas width + bezel padding (12px * 2 = 24px)
  const totalCanvasWidth = canvasWidth.value + 24
  const totalCanvasHeight = canvasHeight.value + 24

  const scaleX = containerWidth / totalCanvasWidth
  const scaleY = containerHeight / totalCanvasHeight

  // Contain: fit full canvas in the workspace; allow scale > 1 so the preview can fill large panels
  scale.value = Math.min(Math.min(scaleX, scaleY), 2)
}

// Handle wheel for zoom
const handleWheel = (e) => {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.1 : 0.1
    scale.value = Math.max(0.1, Math.min(2, scale.value + delta))
  }
}

const zoomIn = () => {
  scale.value = Math.min(2, scale.value + 0.1)
}

const zoomOut = () => {
  scale.value = Math.max(0.1, scale.value - 0.1)
}

// Add widget
const addWidget = (type) => {
  const defaultWidth =
    type === 'text'
      ? 300
      : type === 'marquee'
        ? Math.min(720, Math.max(320, canvasWidth.value * 0.6))
        : type === 'weather'
          ? 420
        : type === 'qr_action'
          ? 360
        : type === 'countdown'
          ? 520
        : type === 'image' || type === 'video' || type === 'album' || type === 'webview'
          ? 400
          : type === 'chart'
            ? 500
            : type === 'weekday'
              ? 280
            : 200
  const defaultHeight = type === 'text' ? 100 : type === 'marquee' ? 110 : type === 'weather' ? 180 : type === 'qr_action' ? 420 : type === 'countdown' ? 200 : type === 'image' || type === 'video' || type === 'album' || type === 'webview' ? 300 : type === 'chart' ? 300 : type === 'weekday' ? 120 : 100

  const widget = {
    id: generateId(),
    type,
    name: `${type.charAt(0).toUpperCase() + type.slice(1)} Widget ${widgets.value.length + 1}`,
    x: (canvasWidth.value - defaultWidth) / 2,
    y: (canvasHeight.value - defaultHeight) / 2,
    width: defaultWidth,
    height: defaultHeight,
    rotation: 0,
    zIndex: widgets.value.length,
    visible: true, // Default to visible
    content:
      type === 'text'
        ? 'Sample Text'
        : type === 'marquee'
        ? 'Breaking News: New promotions are now live • Visit the help desk for details • Stay tuned for more updates'
        : type === 'weather'
        ? 'Tehran,IR'
        : type === 'qr_action'
        ? 'https://example.com/menu'
        : type === 'clock'
        ? 'HH:mm:ss'
        : type === 'date'
        ? 'YYYY-MM-DD'
        : type === 'weekday'
        ? 'dddd'
        : type === 'webview'
        ? 'https://example.com'
        : type === 'chart'
        ? '{"type":"bar","data":{"labels":["A","B","C"],"datasets":[{"label":"Series","data":[12,19,7]}]}}'
        : type === 'countdown'
        ? 'Spring Festival'
        : '',
    content_ids: [],
    style: {
      ...(type === 'marquee' ? getMarqueeDefaultStyle() : {}),
      ...(type === 'weather' ? getWeatherDefaultStyle() : {}),
      ...(type === 'qr_action' ? getQrActionDefaultStyle() : {}),
      ...(type === 'countdown' ? getCountdownDefaultStyle() : {}),
      ...(type === 'album' ? getAlbumDefaultStyle() : {}),
      ...((type === 'clock' || type === 'date' || type === 'weekday') ? getTemporalDefaultStyle(type) : {}),
      color: type === 'text' ? '#000000' : undefined,
      fontSize: type === 'text' ? '24px' : undefined,
      fontFamily: type === 'text' ? 'Arial, sans-serif' : undefined,
      textAlign: type === 'text' ? 'left' : undefined,
      backgroundColor: type === 'text' ? 'transparent' : undefined,
      timeZone: type === 'clock' || type === 'date' || type === 'weekday' ? defaultTimeZone : undefined,
      objectFit: type === 'image' || type === 'video' ? 'cover' : (type === 'album' ? 'contain' : undefined),
    }
  }

  widgets.value.push(widget)
  widgetVisibility.value[widget.id] = true
  selectedWidgetId.value = widget.id

  nextTick(() => {
    updateSelectedWidgetElement()
  })
}

// Select widget
const selectWidget = (widgetId) => {
  selectedWidgetId.value = widgetId
  nextTick(() => {
    updateSelectedWidgetElement()
  })
}

// Update selected widget element reference
const updateSelectedWidgetElement = () => {
  if (selectedWidgetId.value && widgetRefs.value[selectedWidgetId.value]) {
    selectedWidgetElement.value = widgetRefs.value[selectedWidgetId.value]
  } else {
    selectedWidgetElement.value = null
  }
}

// Watch for widget selection changes
watch(selectedWidgetId, () => {
  nextTick(() => {
    updateSelectedWidgetElement()
  })
})

// Watch for canvas area changes to update bounds reactively
watch([canvasArea, scale], () => {
  // Force recomputation of bounds when canvas position/scale changes
  // This ensures Moveable bounds stay in sync with canvas position
  if (moveableRef.value && canvasArea.value) {
    nextTick(() => {
      if (moveableRef.value) {
        moveableRef.value.updateRect()
      }
    })
  }
}, { flush: 'post' })

// Delete widget
const deleteWidget = (widgetId) => {
  const index = widgets.value.findIndex(w => w.id === widgetId)
  if (index > -1) {
    widgets.value.splice(index, 1)
    if (selectedWidgetId.value === widgetId) {
      selectedWidgetId.value = null
    }
  }
}

const deleteSelectedWidget = () => {
  if (!selectedWidgetId.value) return
  deleteWidget(selectedWidgetId.value)
}

// Get widget style for rendering
const getWidgetStyle = (widget) => {
  // Keep sub-pixel precision during move/resize to avoid jitter.
  const x = Number(widget.x || 0)
  const y = Number(widget.y || 0)
  const width = Number(widget.width || 0)
  const height = Number(widget.height || 0)
  const rotation = Math.round(widget.rotation * 100) / 100 // Round to 2 decimal places for rotation
  
  // Check visibility
  const isVisible = widget.visible !== false
  const editorBgFallback = (type) => {
    switch (type) {
      case 'marquee': return '#111827'
      case 'qr_action': return '#ffffff'
      case 'weather': return '#0f172a'
      case 'countdown': return '#450a0a'
      default: return 'transparent'
    }
  }
  const widgetBg =
    (widget.type === 'text' || widget.type === 'marquee' || widget.type === 'clock' || widget.type === 'date' || widget.type === 'weekday' || widget.type === 'qr_action' || widget.type === 'countdown' || widget.type === 'weather')
      ? resolveWidgetBackgroundColor(widget.style, editorBgFallback(widget.type))
      : 'transparent'
  
  return {
    left: `${x}px`,
    top: `${y}px`,
    width: `${width}px`,
    height: `${height}px`,
    transform: `rotate(${rotation}deg)`,
    zIndex: widget.zIndex,
    display: isVisible ? 'block' : 'none',
    opacity: isVisible ? 1 : 0,
    backgroundColor: widgetBg,
    // Enable GPU acceleration to prevent flickering during movement
    willChange: 'transform, top, left',
  }
}

// Toggle widget visibility
const toggleWidgetVisibility = (widgetId) => {
  const widget = widgets.value.find(w => w.id === widgetId)
  if (widget) {
    widget.visible = widget.visible === false ? true : false
  }
}

// Start editing widget name
const startEditingWidgetName = (widgetId) => {
  const widget = widgets.value.find(w => w.id === widgetId)
  if (widget) {
    editingWidgetId.value = widgetId
    editingWidgetName.value = widget.name
    nextTick(() => {
      if (widgetNameInput.value) {
        const input = Array.isArray(widgetNameInput.value) ? widgetNameInput.value[0] : widgetNameInput.value
        if (input) {
          input.focus()
          input.select()
        }
      }
    })
  }
}

// Finish editing widget name
const finishEditingWidgetName = (widgetId) => {
  const widget = widgets.value.find(w => w.id === widgetId)
  if (widget && editingWidgetName.value.trim()) {
    widget.name = editingWidgetName.value.trim()
  }
  editingWidgetId.value = null
  editingWidgetName.value = ''
}

// Cancel editing widget name
const cancelEditingWidgetName = () => {
  editingWidgetId.value = null
  editingWidgetName.value = ''
}

// Open Media Library Modal
const openMediaLibrary = (widgetType) => {
  // Set filter type based on widget type
  mediaLibraryFilterType.value = widgetType === 'image' ? 'image' : widgetType === 'video' ? 'video' : null
  showMediaLibrary.value = true
}

const syncAlbumWidgetQueue = (widget) => {
  if (!widget || widget.type !== 'album') return
  if (!Array.isArray(widget.content_ids)) widget.content_ids = []
  if (!widget.style || typeof widget.style !== 'object') widget.style = getAlbumDefaultStyle()
  if (!Array.isArray(widget.style.playlist)) widget.style.playlist = []

  const normalizedPlaylist = []
  const normalizedIds = []
  widget.style.playlist.forEach((item, index) => {
    if (!item || !item.content_id) return
    const itemId = String(item.content_id)
    if (normalizedIds.includes(itemId)) return
    normalizedIds.push(itemId)
    normalizedPlaylist.push({
      content_id: itemId,
      name: item.name || '',
      order: index,
      durationSec: normalizeRange(item.durationSec, widget.style.defaultDurationSec || 10, 1, 300),
      transition: item.transition || widget.style.transition || 'fade',
      mediaType: item.mediaType || null,
      url: item.url || '',
    })
  })
  widget.style.playlist = normalizedPlaylist
  widget.content_ids = normalizedIds
  widget.content_id = normalizedIds[0] || null
}

const clearAlbumQueue = () => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'album') return
  selectedWidget.value.content = ''
  selectedWidget.value.content_id = null
  selectedWidget.value.content_ids = []
  if (!selectedWidget.value.style) selectedWidget.value.style = getAlbumDefaultStyle()
  selectedWidget.value.style.playlist = []
}

const removeAlbumItem = (contentId) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'album') return
  const targetId = String(contentId)
  selectedWidget.value.style.playlist = (selectedWidget.value.style.playlist || []).filter(
    (item) => String(item.content_id) !== targetId
  )
  syncAlbumWidgetQueue(selectedWidget.value)
}

const moveAlbumItem = (contentId, delta) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'album') return
  const list = [...(selectedWidget.value.style.playlist || [])]
  const currentIndex = list.findIndex(item => String(item.content_id) === String(contentId))
  if (currentIndex < 0) return
  const nextIndex = Math.max(0, Math.min(list.length - 1, currentIndex + delta))
  if (nextIndex === currentIndex) return
  const [moved] = list.splice(currentIndex, 1)
  list.splice(nextIndex, 0, moved)
  selectedWidget.value.style.playlist = list
  syncAlbumWidgetQueue(selectedWidget.value)
}

const updateAlbumItemDuration = (contentId, duration) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'album') return
  const list = selectedWidget.value.style?.playlist
  if (!Array.isArray(list)) return
  const row = list.find(item => String(item.content_id) === String(contentId))
  if (!row) return
  row.durationSec = normalizeRange(duration, selectedWidget.value.style.defaultDurationSec || 10, 1, 300)
}

// Handle media selection from library
const handleMediaSelect = async (data) => {
  if (!selectedWidget.value || !data.url) return

  if (selectedWidget.value.type === 'album') {
    if (!selectedWidget.value.style || typeof selectedWidget.value.style !== 'object') {
      selectedWidget.value.style = getAlbumDefaultStyle()
    }
    if (!Array.isArray(selectedWidget.value.style.playlist)) {
      selectedWidget.value.style.playlist = []
    }
    if (!Array.isArray(selectedWidget.value.content_ids)) {
      selectedWidget.value.content_ids = []
    }

    const contentId = data.content?.id ? String(data.content.id) : null
    if (!contentId) return
    const existing = selectedWidget.value.style.playlist.find(item => String(item.content_id) === contentId)
    if (!existing) {
      selectedWidget.value.style.playlist.push({
        content_id: contentId,
        name: data.content?.name || '',
        durationSec: selectedWidget.value.style.defaultDurationSec || 10,
        transition: selectedWidget.value.style.transition || 'fade',
        mediaType: data.content?.type || null,
        url: data.url || '',
      })
    }
    if (!selectedWidget.value.content) {
      selectedWidget.value.content = data.url
    }
    syncAlbumWidgetQueue(selectedWidget.value)
    notify.success('Media added to album queue')
    return
  }
  
  // Update widget content with selected URL
  updateWidgetProperty('content', data.url)
  if (!selectedWidget.value.style) {
    selectedWidget.value.style = {}
  }
  selectedWidget.value.style.imageVersion = Date.now()
  
  // CRITICAL: Store content_id in widget object for saving
  if (data.content && data.content.id) {
    selectedWidget.value.content_id = data.content.id
  }
  
  // Link content to widget if content ID is available and widget has backend ID
  if (data.content && data.content.id && selectedWidget.value.id) {
    try {
      // Check if widget ID is a UUID (backend format)
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      const isBackendWidget = uuidRegex.test(selectedWidget.value.id)
      
      if (isBackendWidget) {
        // Widget is saved to backend - link content to widget (PATCH: partial update; PUT would omit required fields)
        const { contentsAPI } = await import('@/services/api')
        await contentsAPI.patch(data.content.id, {
          widget: selectedWidget.value.id
        })
        notify.success('Content linked to widget')
      }
    } catch (error) {
      console.error('Failed to link content to widget:', error)
      // Don't show error to user - content URL is already set, linking is optional
    }
  }
}

// Handle preview image error
const handlePreviewError = (event) => {
  // Hide broken image
  event.target.style.display = 'none'
}

// Drag and drop handlers for z-index reordering
const handleDragStart = (event, widgetId) => {
  draggingWidgetId.value = widgetId
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', widgetId)
}

const handleDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const handleDrop = (event, targetWidgetId) => {
  event.preventDefault()
  
  if (!draggingWidgetId.value || draggingWidgetId.value === targetWidgetId) {
    dragOverWidgetId.value = null
    draggingWidgetId.value = null
    return
  }
  
  const draggedWidget = widgets.value.find(w => w.id === draggingWidgetId.value)
  const targetWidget = widgets.value.find(w => w.id === targetWidgetId)
  
  if (draggedWidget && targetWidget) {
    // Swap z-index values
    const tempZIndex = draggedWidget.zIndex
    draggedWidget.zIndex = targetWidget.zIndex
    targetWidget.zIndex = tempZIndex
    
    // Re-sort widgets array to maintain order
    widgets.value.sort((a, b) => a.zIndex - b.zIndex)
  }
  
  dragOverWidgetId.value = null
  draggingWidgetId.value = null
}

const handleDragMoveableStart = () => {
  if (!selectedWidget.value) return
  dragStartState.value = {
    x: Number(selectedWidget.value.x || 0),
    y: Number(selectedWidget.value.y || 0),
  }
}

// Handle drag
const handleDrag = ({ beforeTranslate, beforeDelta }) => {
  if (!selectedWidget.value) return

  const start = dragStartState.value || {
    x: Number(selectedWidget.value.x || 0),
    y: Number(selectedWidget.value.y || 0),
  }

  // Prefer absolute translate from drag start to avoid cumulative delta drift.
  const translate = beforeTranslate || beforeDelta || [0, 0]
  const deltaX = translate[0] / scale.value
  const deltaY = translate[1] / scale.value

  let newX = start.x + deltaX
  let newY = start.y + deltaY

  const maxX = canvasWidth.value - selectedWidget.value.width
  const maxY = canvasHeight.value - selectedWidget.value.height
  
  selectedWidget.value.x = Math.max(0, Math.min(maxX, newX))
  selectedWidget.value.y = Math.max(0, Math.min(maxY, newY))
}

const handleDragEnd = () => {
  dragStartState.value = null
}

// Handle resize
const handleResizeStart = () => {
  if (!selectedWidget.value) return
  resizeStartState.value = {
    x: Number(selectedWidget.value.x || 0),
    y: Number(selectedWidget.value.y || 0),
  }
}

const handleResize = (event) => {
  if (!selectedWidget.value || !event.target) return

  const { target, width, height, drag } = event

  // Use Moveable's resolved width/height directly.
  // Dividing by scale can cause sudden jump-to-fit at low zoom levels.
  const newWidth = Math.max(50, Number(width) || 0)
  const newHeight = Math.max(50, Number(height) || 0)
  target.style.width = `${newWidth}px`
  target.style.height = `${newHeight}px`
  selectedWidget.value.width = newWidth
  selectedWidget.value.height = newHeight

  // Position shift while resizing from left/top handles.
  if (drag && drag.beforeTranslate) {
    const start = resizeStartState.value || {
      x: Number(selectedWidget.value.x || 0),
      y: Number(selectedWidget.value.y || 0),
    }
    const dx = drag.beforeTranslate[0]
    const dy = drag.beforeTranslate[1]
    const newX = start.x + dx
    const newY = start.y + dy
    target.style.left = `${newX}px`
    target.style.top = `${newY}px`
    selectedWidget.value.x = newX
    selectedWidget.value.y = newY
  }
}

const handleResizeEnd = () => {
  resizeStartState.value = null
  // Sync Moveable's internal state after resize ends
  nextTick(() => {
    if (moveableRef.value) {
      moveableRef.value.updateRect()
    }
  })
}

// Handle rotate
const handleRotate = ({ target, rotation }) => {
  if (!selectedWidget.value) return
  selectedWidget.value.rotation = rotation
}

const handleRotateEnd = () => {
  // Optional: Save state or trigger update
}

// Update widget property
const updateWidgetProperty = (property, value) => {
  if (!selectedWidget.value) return
  let numValue = ['x', 'y', 'width', 'height', 'rotation', 'zIndex'].includes(property)
    ? Math.round(parseFloat(value) || 0) // Round to integer for clean coordinates
    : value

  // Enforce boundaries for position and size
  if (property === 'x') {
    numValue = Math.max(0, Math.min(canvasWidth.value - selectedWidget.value.width, numValue))
  } else if (property === 'y') {
    numValue = Math.max(0, Math.min(canvasHeight.value - selectedWidget.value.height, numValue))
  } else if (property === 'width') {
    numValue = Math.max(50, Math.min(canvasWidth.value - selectedWidget.value.x, numValue))
  } else if (property === 'height') {
    numValue = Math.max(50, Math.min(canvasHeight.value - selectedWidget.value.y, numValue))
  }

  selectedWidget.value[property] = numValue

  if (property === 'content' && (selectedWidget.value.type === 'image' || selectedWidget.value.type === 'video')) {
    if (!selectedWidget.value.style) {
      selectedWidget.value.style = {}
    }
    selectedWidget.value.style.imageVersion = Date.now()
  }

  nextTick(() => {
    if (moveableRef.value) {
      moveableRef.value.updateRect()
    }
  })
}

const applyWebviewUrl = () => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'webview') return
  updateWidgetProperty('content', webviewUrlDraft.value.trim())
}

function swapWidgetZIndex(idA, idB) {
  const a = widgets.value.find((w) => w.id === idA)
  const b = widgets.value.find((w) => w.id === idB)
  if (!a || !b) return
  const t = a.zIndex
  a.zIndex = b.zIndex
  b.zIndex = t
  nextTick(() => moveableRef.value?.updateRect?.())
}

function moveLayerOrder(widgetId, direction) {
  const sorted = [...widgets.value].sort((a, b) => a.zIndex - b.zIndex)
  const idx = sorted.findIndex((w) => w.id === widgetId)
  if (idx < 0) return
  if (direction === 'forward' && idx < sorted.length - 1) {
    swapWidgetZIndex(sorted[idx].id, sorted[idx + 1].id)
  } else if (direction === 'back' && idx > 0) {
    swapWidgetZIndex(sorted[idx].id, sorted[idx - 1].id)
  }
}

function bringLayerToFront(widgetId) {
  const maxZ = Math.max(...widgets.value.map((w) => w.zIndex), 0)
  const w = widgets.value.find((x) => x.id === widgetId)
  if (w) w.zIndex = maxZ + 1
  nextTick(() => moveableRef.value?.updateRect?.())
}

function sendLayerToBack(widgetId) {
  const minZ = Math.min(...widgets.value.map((w) => w.zIndex), 0)
  const w = widgets.value.find((x) => x.id === widgetId)
  if (w) w.zIndex = minZ - 1
  nextTick(() => moveableRef.value?.updateRect?.())
}

// Update widget style
const updateWidgetStyle = (property, value) => {
  if (!selectedWidget.value) return
  if (!selectedWidget.value.style) {
    selectedWidget.value.style = {}
  }
  selectedWidget.value.style[property] = value
}

/** Maps saved style (including legacy `inline`) to Date Display Mode select value */
const normalizeDateDisplayModeForEditor = (style) => {
  if (!style || typeof style !== 'object') return 'dateOnly'
  const raw = style.displayMode
  if (raw === 'stacked') return 'stacked'
  if (raw === 'datePlusWeekday' || raw === 'timePlusWeekday') return 'datePlusWeekday'
  if (raw === 'dateOnly' || raw === 'timeOnly') return 'dateOnly'
  if (raw === 'inline') return style.showWeekday === true ? 'datePlusWeekday' : 'dateOnly'
  return style.showWeekday === true ? 'datePlusWeekday' : 'dateOnly'
}

const onDateDisplayModeChange = (mode) => {
  updateWidgetStyle('displayMode', mode)
  if (mode === 'dateOnly') {
    updateWidgetStyle('showWeekday', false)
  } else {
    updateWidgetStyle('showWeekday', true)
  }
}

const handleChartWidgetUpdate = ({ content, stylePatch }) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'chart') return
  selectedWidget.value.content = content
  if (!selectedWidget.value.style) {
    selectedWidget.value.style = {}
  }
  selectedWidget.value.style = {
    ...selectedWidget.value.style,
    ...(stylePatch || {}),
  }
}

// Keyboard shortcuts
const handleKeyDown = (e) => {
  const activeElement = document.activeElement
  const isEditingField = activeElement && (
    ['INPUT', 'TEXTAREA', 'SELECT'].includes(activeElement.tagName) ||
    activeElement.isContentEditable
  )
  if (isEditingField || editingWidgetId.value) return

  if (e.key === 'Delete' && selectedWidgetId.value) {
    deleteWidget(selectedWidgetId.value)
  } else if (e.key.startsWith('Arrow') && selectedWidgetId.value) {
    e.preventDefault()
    const step = e.shiftKey ? 10 : 1
    if (e.key === 'ArrowLeft') {
      selectedWidget.value.x = Math.max(0, selectedWidget.value.x - step)
    } else if (e.key === 'ArrowRight') {
      selectedWidget.value.x = Math.min(canvasWidth.value - selectedWidget.value.width, selectedWidget.value.x + step)
    } else if (e.key === 'ArrowUp') {
      selectedWidget.value.y = Math.max(0, selectedWidget.value.y - step)
    } else if (e.key === 'ArrowDown') {
      selectedWidget.value.y = Math.min(canvasHeight.value - selectedWidget.value.height, selectedWidget.value.y + step)
    }
    
    // Round coordinates to integers
    selectedWidget.value.x = Math.round(selectedWidget.value.x)
    selectedWidget.value.y = Math.round(selectedWidget.value.y)
    
    nextTick(() => {
      if (moveableRef.value) {
        moveableRef.value.updateRect()
      }
    })
  }
}

// Convert percentage string to number
const parsePercentage = (value) => {
  if (typeof value === 'string' && value.endsWith('%')) {
    return parseFloat(value) / 100
  }
  return typeof value === 'number' ? value : parseFloat(value) || 0
}

const getFontSizeNumber = (value, fallback = 24) => {
  if (value === undefined || value === null || value === '') return fallback
  if (typeof value === 'number') return value
  const parsed = Number.parseFloat(String(value).replace('px', '').trim())
  return Number.isFinite(parsed) ? parsed : fallback
}

const getBackgroundHex = (value, fallback = '#000000') => {
  if (!value || typeof value !== 'string') return fallback
  const v = value.trim()
  if (v.startsWith('#')) {
    if (v.length === 4) {
      return `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`
    }
    return v.slice(0, 7)
  }
  const rgbaMatch = v.match(/rgba?\(([^)]+)\)/i)
  if (!rgbaMatch) return fallback
  const parts = rgbaMatch[1].split(',').map(p => Number.parseFloat(p.trim()))
  if (parts.length < 3 || parts.some(n => !Number.isFinite(n))) return fallback
  const toHex = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0')
  return `#${toHex(parts[0])}${toHex(parts[1])}${toHex(parts[2])}`
}

const normalizeRange = (value, fallback, min, max) => {
  const parsed = Number.parseFloat(String(value ?? '').trim())
  if (!Number.isFinite(parsed)) return fallback
  return Math.max(min, Math.min(max, parsed))
}

const normalizeQrRule = (rule = {}, index = 0) => ({
  name: typeof rule.name === 'string' ? rule.name : `Rule ${index + 1}`,
  priority: Math.max(1, Number.parseInt(String(rule.priority ?? index + 1), 10) || index + 1),
  startHour: rule.startHour === null || rule.startHour === undefined ? null : Math.max(0, Math.min(23, Number.parseInt(String(rule.startHour), 10) || 0)),
  endHour: rule.endHour === null || rule.endHour === undefined ? null : Math.max(0, Math.min(23, Number.parseInt(String(rule.endHour), 10) || 0)),
  daysOfWeek: Array.isArray(rule.daysOfWeek)
    ? [...new Set(rule.daysOfWeek.map((d) => Number.parseInt(String(d), 10)).filter((d) => Number.isFinite(d) && d >= 0 && d <= 6))]
    : [0, 1, 2, 3, 4, 5, 6],
  targetUrl: typeof rule.targetUrl === 'string' ? rule.targetUrl : '',
  isActive: rule.isActive !== false,
})

const ensureQrRules = () => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'qr_action') return
  if (!selectedWidget.value.style) selectedWidget.value.style = {}
  if (!Array.isArray(selectedWidget.value.style.rules) || selectedWidget.value.style.rules.length === 0) {
    selectedWidget.value.style.rules = [normalizeQrRule({}, 0)]
    return
  }
  selectedWidget.value.style.rules = selectedWidget.value.style.rules.map((rule, idx) => normalizeQrRule(rule, idx))
}

const currentQrRules = computed(() => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'qr_action') return []
  ensureQrRules()
  return selectedWidget.value.style.rules
})

const addQrRule = () => {
  ensureQrRules()
  const nextIndex = selectedWidget.value.style.rules.length
  selectedWidget.value.style.rules.push(normalizeQrRule({}, nextIndex))
}

const removeQrRule = (index) => {
  ensureQrRules()
  if (selectedWidget.value.style.rules.length <= 1) {
    selectedWidget.value.style.rules = [normalizeQrRule({}, 0)]
    return
  }
  selectedWidget.value.style.rules.splice(index, 1)
  selectedWidget.value.style.rules = selectedWidget.value.style.rules.map((rule, idx) => normalizeQrRule(rule, idx))
}

const updateQrRule = (index, key, value) => {
  ensureQrRules()
  const next = { ...selectedWidget.value.style.rules[index], [key]: value }
  selectedWidget.value.style.rules[index] = normalizeQrRule(next, index)
}

const toggleQrRuleDay = (index, day) => {
  ensureQrRules()
  const current = selectedWidget.value.style.rules[index]
  const days = Array.isArray(current.daysOfWeek) ? [...current.daysOfWeek] : []
  const exists = days.includes(day)
  const nextDays = exists ? days.filter((d) => d !== day) : [...days, day]
  updateQrRule(index, 'daysOfWeek', nextDays.length ? nextDays : [day])
}

const isQrRuleAllDay = (rule) => rule?.startHour === null && rule?.endHour === null

const setQrRuleTimeMode = (index, mode) => {
  if (mode === 'all_day') {
    updateQrRule(index, 'startHour', null)
    updateQrRule(index, 'endHour', null)
    return
  }
  const current = currentQrRules.value[index] || {}
  updateQrRule(index, 'startHour', current.startHour ?? 8)
  updateQrRule(index, 'endHour', current.endHour ?? 18)
}

const toRgb = (hex) => {
  const clean = String(hex || '').replace('#', '').trim()
  if (!clean) return null
  const full = clean.length === 3
    ? `${clean[0]}${clean[0]}${clean[1]}${clean[1]}${clean[2]}${clean[2]}`
    : clean.slice(0, 6)
  const asNumber = Number.parseInt(full, 16)
  if (!Number.isFinite(asNumber)) return null
  return {
    r: (asNumber >> 16) & 255,
    g: (asNumber >> 8) & 255,
    b: asNumber & 255,
  }
}

const relativeLuminance = (rgb) => {
  const f = (v) => {
    const x = v / 255
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * f(rgb.r) + 0.7152 * f(rgb.g) + 0.0722 * f(rgb.b)
}

const contrastRatio = (hexA, hexB) => {
  const a = toRgb(hexA)
  const b = toRgb(hexB)
  if (!a || !b) return 1
  const l1 = relativeLuminance(a)
  const l2 = relativeLuminance(b)
  const bright = Math.max(l1, l2)
  const dark = Math.min(l1, l2)
  return (bright + 0.05) / (dark + 0.05)
}

const qrReadabilityOk = (widget) => {
  const fg = widget?.style?.foregroundColor || '#000000'
  const bg = widget?.style?.backgroundColor || '#ffffff'
  const quiet = Number(widget?.style?.quietZone ?? 4)
  return contrastRatio(fg, bg) >= 4.5 && quiet >= 4
}

const qrReadabilityMessage = (widget) => {
  const fg = widget?.style?.foregroundColor || '#000000'
  const bg = widget?.style?.backgroundColor || '#ffffff'
  const ratio = contrastRatio(fg, bg)
  const quiet = Number(widget?.style?.quietZone ?? 4)
  if (ratio < 4.5) return `Low contrast (${ratio.toFixed(2)}:1). Use darker foreground on lighter background.`
  if (quiet < 4) return 'Quiet zone is too small. Use at least 4 modules.'
  return `Readable contrast (${ratio.toFixed(2)}:1) and quiet zone are valid.`
}

const applyMarqueePreset = (presetId) => {
  if (!selectedWidget.value || selectedWidget.value.type !== 'marquee') return
  const preset = marqueePresets.find(item => item.id === presetId)
  if (!preset) return
  if (!selectedWidget.value.style) {
    selectedWidget.value.style = {}
  }
  selectedWidget.value.style = {
    ...getMarqueeDefaultStyle(),
    ...selectedWidget.value.style,
    ...preset.style,
    preset: preset.id,
  }
}


// Load template data from API
const loadTemplateData = async () => {
  if (!templateId.value) return

  loading.value = true
  try {
    // Fetch template
    const template = await templatesStore.fetchTemplate(templateId.value)
    
    // Set template name and dimensions
    templateName.value = template.name || 'Untitled Template'
    canvasWidth.value = template.width || 1920
    canvasHeight.value = template.height || 1080
    
    // Set background if available in config_json
    if (template.config_json) {
      if (template.config_json.backgroundColor) {
        canvasBackgroundColor.value = template.config_json.backgroundColor
      }
      if (template.config_json.backgroundImage) {
        canvasBackgroundImage.value = template.config_json.backgroundImage
      }
    }
    
    // Load widgets from config_json (editor format)
    widgets.value = []
    
    if (template.config_json && template.config_json.widgets && Array.isArray(template.config_json.widgets)) {
      // Load widgets from config_json (editor's native format)
      for (const widget of template.config_json.widgets) {
        // Convert percentage positions to pixel positions for editing
        const x = typeof widget.x === 'string' && widget.x.endsWith('%')
          ? (parsePercentage(widget.x) * canvasWidth.value)
          : (parseFloat(widget.x) || 0)
        
        const y = typeof widget.y === 'string' && widget.y.endsWith('%')
          ? (parsePercentage(widget.y) * canvasHeight.value)
          : (parseFloat(widget.y) || 0)
        
        const width = typeof widget.width === 'string' && widget.width.endsWith('%')
          ? (parsePercentage(widget.width) * canvasWidth.value)
          : (parseFloat(widget.width) || 200)
        
        const height = typeof widget.height === 'string' && widget.height.endsWith('%')
          ? (parsePercentage(widget.height) * canvasHeight.value)
          : (parseFloat(widget.height) || 100)
        
        // Map widget data to editor format
        const editorWidget = {
          id: widget.id || generateId(),
          type: widget.type,
          name: widget.name || `${widget.type} Widget`,
          x: x,
          y: y,
          width: width,
          height: height,
          rotation: widget.rotation || 0,
          zIndex: widget.zIndex || widget.z_index || 0,
          visible: widget.visible !== undefined ? widget.visible : true, // Default to visible
          content: widget.content || '',
          content_id: widget.content_id || null, // Preserve content_id when loading
          content_ids: Array.isArray(widget.content_ids)
            ? widget.content_ids
            : (widget.content_id ? [widget.content_id] : []),
          style: widget.type === 'marquee'
            ? { ...getMarqueeDefaultStyle(), ...(widget.style || {}) }
            : widget.type === 'weather'
            ? { ...getWeatherDefaultStyle(), ...(widget.style || {}) }
            : widget.type === 'qr_action'
            ? { ...getQrActionDefaultStyle(), ...(widget.style || {}) }
            : widget.type === 'countdown'
            ? { ...getCountdownDefaultStyle(), ...(widget.style || {}) }
            : widget.type === 'album'
            ? { ...getAlbumDefaultStyle(), ...(widget.style || {}) }
            : widget.type === 'clock' || widget.type === 'date' || widget.type === 'weekday'
            ? { ...getTemporalDefaultStyle(widget.type), ...(widget.style || {}), format: (widget.style?.format || widget.content || undefined) }
            : (widget.style || {})
        }
        
        widgets.value.push(editorWidget)
        // Initialize visibility state
        if (editorWidget.visible !== undefined) {
          widgetVisibility.value[editorWidget.id] = editorWidget.visible !== false
        } else {
          widgetVisibility.value[editorWidget.id] = true
        }
      }
    }
    
    // Sort by z-index
    widgets.value.sort((a, b) => a.zIndex - b.zIndex)
    
  } catch (error) {
    console.error('Failed to load template:', error)
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to load template data')
  } finally {
    loading.value = false
  }
}

// Save template - Convert to percentage-based JSON
const saveTemplate = async () => {
  if (!canEditTemplates.value) {
    notify.warning('Your account cannot save templates.')
    return
  }

  if (!templateName.value || templateName.value.trim() === '') {
    notify.error('Please enter a template name')
    return
  }

  // Check if offline before attempting to save
  if (!isOnline.value) {
    notify.error('Cannot save while offline. Please wait for connection to be restored.')
    return
  }

  const unreadableQr = widgets.value.find((widget) => widget.type === 'qr_action' && !qrReadabilityOk(widget))
  if (unreadableQr) {
    notify.error(`Fix QR readability for "${unreadableQr.name}" before saving.`)
    return
  }

  saving.value = true
  try {
    // Build template data for API
    const templateData = {
      name: templateName.value.trim(),
      width: canvasWidth.value,
      height: canvasHeight.value,
      config_json: {
        backgroundColor: canvasBackgroundColor.value,
        backgroundImage: canvasBackgroundImage.value || undefined,
        widgets: widgets.value.map(widget => ({
          id: widget.id,
          type: widget.type,
          name: widget.name,
          // Convert pixels to percentages
          x: `${((widget.x / canvasWidth.value) * 100).toFixed(2)}%`,
          y: `${((widget.y / canvasHeight.value) * 100).toFixed(2)}%`,
          width: `${((widget.width / canvasWidth.value) * 100).toFixed(2)}%`,
          height: `${((widget.height / canvasHeight.value) * 100).toFixed(2)}%`,
          rotation: widget.rotation,
          zIndex: widget.zIndex,
          visible: widget.visible !== undefined ? widget.visible : true, // Include visibility state
          content: widget.content || '',
          content_id: widget.content_id || null, // Include content_id if available
          content_ids: Array.isArray(widget.content_ids) ? widget.content_ids : [],
          playlist_items: Array.isArray(widget.style?.playlist) ? widget.style.playlist : [],
          style: widget.style || {}
        }))
      }
    }
    
    // Add description if available from query params
    if (route.query.description) {
      templateData.description = route.query.description
    }
    
    // Add orientation if available
    if (route.query.orientation) {
      templateData.orientation = route.query.orientation
    }

    let savedTemplate
    if (templateId.value) {
      // Update existing template
      savedTemplate = await templatesStore.updateTemplate(templateId.value, templateData)
      notify.success('Template updated successfully')
    } else {
      // Create new template
      savedTemplate = await templatesStore.createTemplate(templateData)
      notify.success('Template created successfully')
      
      // Navigate to edit mode for the new template
      router.replace(`/templates/${savedTemplate.id}/edit`)
    }
    
    // CRITICAL: Reload template data to get backend widget IDs
    // After saving, widgets are synced to database and get backend UUIDs
    // We need to reload to update local widget IDs with backend UUIDs
    if (savedTemplate.id) {
      await loadTemplateData()
    }
    
    return savedTemplate
  } catch (error) {
    console.error('Failed to save template:', error)
    const parsed = error.apiError || normalizeApiError(error)
    const errorMessage = parsed.userMessage || 'Failed to save template'
    notify.error(errorMessage)
    throw error
  } finally {
    saving.value = false
  }
}

// Navigate back to templates list
const goBack = () => {
  router.push('/templates')
}

// Push to Screen functionality
const onlineScreens = computed(() => {
  return screensStore.onlineScreens || screensStore.screens.filter(s => screensStore.getScreenStatus(s) === 'online')
})

const handlePushToScreen = async () => {
  if (!canEditTemplates.value) {
    notify.warning('Your account cannot push templates to screens.')
    return
  }

  if (!templateId.value) {
    notify.error('Please save the template first before pushing to screen')
    return
  }

  // Fetch screens to ensure we have the latest online status
  try {
    await screensStore.fetchScreens()
    // Load current template data
    const template = await templatesStore.fetchTemplate(templateId.value)
    currentTemplate.value = template
    showPushModal.value = true
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to load screens')
  }
}

// Handle screen selection from push modal
const handlePushToScreenSelect = async (screen) => {
  if (!templateId.value || !currentTemplate.value) return
  
  pushing.value = true
  try {
    // Always save latest editor changes before pushing, so the screen receives
    // exactly what user sees in the editor (no manual refresh mismatch).
    await saveTemplate()

    // Step 1: Activate template on the screen
    await templatesStore.activateOnScreen(
      templateId.value,
      screen.id,
      true // sync_content
    )
    
    // Step 2: Send RELOAD command to the screen
    const { useCommandsStore } = await import('@/stores/commands')
    const commandsStore = useCommandsStore()
    
    await commandsStore.createCommand({
      screen_id: screen.id,
      type: 'refresh', // This is the RELOAD command
      payload: {},
      priority: 8, // High priority
    })
    
    notify.success(`Template successfully pushed to ${screen.name || screen.device_id}`)
    showPushModal.value = false
    currentTemplate.value = null
    
    // Refresh templates to update screen counts
    await templatesStore.fetchTemplates()
  } catch (error) {
    const parsed = error.apiError || normalizeApiError(error)
    notify.error(parsed.userMessage || 'Failed to push template to screen')
  } finally {
    pushing.value = false
  }
}

// Export JSON (Visitors: local snapshot only, no server save)
const exportJSON = async () => {
  if (!canEditTemplates.value) {
    const templateData = {
      name: templateName.value.trim(),
      width: canvasWidth.value,
      height: canvasHeight.value,
      config_json: {
        backgroundColor: canvasBackgroundColor.value,
        backgroundImage: canvasBackgroundImage.value || undefined,
        widgets: widgets.value.map(widget => ({
          id: widget.id,
          type: widget.type,
          name: widget.name,
          x: `${((widget.x / canvasWidth.value) * 100).toFixed(2)}%`,
          y: `${((widget.y / canvasHeight.value) * 100).toFixed(2)}%`,
          width: `${((widget.width / canvasWidth.value) * 100).toFixed(2)}%`,
          height: `${((widget.height / canvasHeight.value) * 100).toFixed(2)}%`,
          rotation: widget.rotation,
          zIndex: widget.zIndex,
          visible: widget.visible !== undefined ? widget.visible : true,
          content: widget.content || '',
          content_id: widget.content_id || null,
          content_ids: Array.isArray(widget.content_ids) ? widget.content_ids : [],
          playlist_items: Array.isArray(widget.style?.playlist) ? widget.style.playlist : [],
          style: widget.style || {}
        }))
      }
    }
    const blob = new Blob([JSON.stringify(templateData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${templateName.value || 'template'}-local.json`
    a.click()
    URL.revokeObjectURL(url)
    notify.success('Exported local preview (not saved to server)')
    return
  }

  const savedTemplate = await saveTemplate()
  const blob = new Blob([JSON.stringify(savedTemplate, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${templateName.value || 'template'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const templateEditorApi = reactive({
  Math,
  rightPanelTab,
  rightPanelCollapsed,
  selectedWidget,
  selectedWidgetId,
  widgets,
  sortedWidgetsByZIndex,
  updateWidgetProperty,
  updateWidgetStyle,
  getFontSizeNumber,
  getBackgroundHex,
  normalizeRange,
  applyMarqueePreset,
  marqueePresets,
  currentQrRules,
  updateQrRule,
  removeQrRule,
  addQrRule,
  isQrRuleAllDay,
  setQrRuleTimeMode,
  qrHourOptions,
  qrWeekdayOptions,
  toggleQrRuleDay,
  qrReadabilityOk,
  qrReadabilityMessage,
  openMediaLibrary,
  handlePreviewError,
  albumQueueItems,
  updateAlbumItemDuration,
  moveAlbumItem,
  removeAlbumItem,
  clearAlbumQueue,
  applyTemporalPreset,
  clockStylePresets,
  dateStylePresets,
  weekdayStylePresets,
  supportedLocales,
  defaultTimeZone,
  worldTimeZones,
  normalizeDateDisplayModeForEditor,
  onDateDisplayModeChange,
  countdownTargetLocal,
  onCountdownTargetAtInput,
  countdownStartLocal,
  onCountdownStartAtInput,
  applyCountdownTheme,
  countdownIsCustomTheme,
  countdownThemeHint,
  updateCountdownLabel,
  webviewUrlDraft,
  applyWebviewUrl,
  handleChartWidgetUpdate,
  selectWidget,
  handleDragStart,
  handleDragOver,
  handleDrop,
  editingWidgetId,
  startEditingWidgetName,
  editingWidgetName,
  finishEditingWidgetName,
  cancelEditingWidgetName,
  widgetNameInput,
  toggleWidgetVisibility,
  moveLayerOrder,
  sendLayerToBack,
  bringLayerToFront,
  deleteWidget,
  draggingWidgetId,
  dragOverWidgetId,
})

provide(TEMPLATE_EDITOR_INJECTION_KEY, templateEditorApi)

let canvasPinchCleanup = null
let desktopLayoutListener = null

// Lifecycle
// Offline detection
const isOnline = ref(navigator.onLine)
const offlineWarningShown = ref(false)

const handleOnline = () => {
  isOnline.value = true
  offlineWarningShown.value = false
  notify.success('Connection restored. Changes will now be saved.')
}

const handleOffline = () => {
  isOnline.value = false
  if (!offlineWarningShown.value) {
    offlineWarningShown.value = true
    notify.warning('You are offline. Your changes will not be saved until the connection returns.', {
      title: 'Offline Warning',
      duration: 0, // Persistent until connection returns
      persistent: true
    })
  }
}

onMounted(async () => {
  // Add offline/online event listeners
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  
  // Check initial online status
  if (!navigator.onLine) {
    handleOffline()
  }
  // Load template data if editing (must happen first to get canvas dimensions)
  if (templateId.value) {
    await loadTemplateData()
  }
  
  // Calculate scale after DOM is ready and template is loaded
  await nextTick()
  calculateScale()

  desktopLayoutMql = window.matchMedia('(min-width: 1024px)')
  const syncDesktopLayout = () => {
    isDesktopLayout.value = desktopLayoutMql.matches
    if (desktopLayoutMql.matches) {
      mobileLibraryOpen.value = false
      mobileInspectorOpen.value = false
      showMobileToolbarMore.value = false
    } else {
      rightPanelCollapsed.value = false
    }
  }
  syncDesktopLayout()
  desktopLayoutListener = syncDesktopLayout
  desktopLayoutMql.addEventListener('change', syncDesktopLayout)

  const el = canvasContainer.value
  if (el) {
    const onTouchStart = (e) => {
      if (e.touches.length === 2) {
        pinchZoomState.active = true
        pinchZoomState.startDist = canvasTouchDistance(e.touches)
        pinchZoomState.startScale = scale.value
      }
    }
    const onTouchMove = (e) => {
      if (!pinchZoomState.active || e.touches.length < 2) return
      e.preventDefault()
      const d = canvasTouchDistance(e.touches)
      if (d > 0 && pinchZoomState.startDist > 0) {
        const next = pinchZoomState.startScale * (d / pinchZoomState.startDist)
        scale.value = Math.max(0.1, Math.min(2, next))
      }
    }
    const onTouchEnd = (e) => {
      if (e.touches.length < 2) pinchZoomState.active = false
    }
    el.addEventListener('touchstart', onTouchStart, { passive: false })
    el.addEventListener('touchmove', onTouchMove, { passive: false })
    el.addEventListener('touchend', onTouchEnd)
    el.addEventListener('touchcancel', onTouchEnd)
    canvasPinchCleanup = () => {
      el.removeEventListener('touchstart', onTouchStart)
      el.removeEventListener('touchmove', onTouchMove)
      el.removeEventListener('touchend', onTouchEnd)
      el.removeEventListener('touchcancel', onTouchEnd)
    }
  }

  if (typeof ResizeObserver !== 'undefined' && canvasContainer.value) {
    canvasResizeObserver = new ResizeObserver(() => {
      nextTick(() => calculateScale())
    })
    canvasResizeObserver.observe(canvasContainer.value)
  }

  // Recalculate scale on window resize
  window.addEventListener('resize', calculateScale)
  window.addEventListener('keydown', handleKeyDown)
  
})

watch([canvasWidth, canvasHeight], () => {
  nextTick(() => {
    calculateScale()
  })
})

onUnmounted(() => {
  canvasResizeObserver?.disconnect()
  canvasResizeObserver = null
  canvasPinchCleanup?.()
  canvasPinchCleanup = null
  if (desktopLayoutMql && desktopLayoutListener) {
    desktopLayoutMql.removeEventListener('change', desktopLayoutListener)
  }
  desktopLayoutMql = null
  desktopLayoutListener = null
  window.removeEventListener('resize', calculateScale)
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped>
.template-editor {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.widget-element {
  user-select: none;
  outline: none;
  transition: box-shadow 0.4s ease;
}

.widget-element:focus {
  outline: none;
}

/* Widget Selection Border - High Contrast for Light Mode */
.widget-selected {
  box-shadow: 0 0 0 2px var(--accent-color);
  outline: 2px solid var(--accent-color);
  outline-offset: 2px;
}

.dark .widget-selected {
  box-shadow: 0 0 0 2px #3b82f6;
  outline: 2px solid #3b82f6;
}

/* Moveable Library Overrides for Light Mode */
:deep(.moveable-control-box) {
  border-color: var(--accent-color) !important;
}

.dark :deep(.moveable-control-box) {
  border-color: #3b82f6 !important;
}

:deep(.moveable-line) {
  background-color: var(--accent-color) !important;
  opacity: 0.6;
}

.dark :deep(.moveable-line) {
  background-color: #3b82f6 !important;
}

:deep(.moveable-control) {
  background-color: var(--accent-color) !important;
  border-color: var(--accent-color) !important;
}

.dark :deep(.moveable-control) {
  background-color: #3b82f6 !important;
  border-color: #3b82f6 !important;
}

/* Monitor Frame Styles - Wall-Mounted Display */
.monitor-frame {
  position: relative;
  display: inline-block;
  background-color: var(--editor-bezel);
  border-radius: 0.5rem;
  box-sizing: border-box;
  border-top: 1px solid var(--editor-bezel-highlight);
  border-left: 1px solid var(--editor-bezel-highlight);
  border-bottom: 1px solid rgba(0, 0, 0, 0.18);
  border-right: 1px solid rgba(0, 0, 0, 0.18);
  box-shadow: var(--editor-bezel-shadow);
}

.dark .monitor-frame {
  border-bottom: 1px solid rgba(0, 0, 0, 0.3);
  border-right: 1px solid rgba(0, 0, 0, 0.3);
}

.power-indicator {
  z-index: 10;
  box-shadow: 0 0 8px rgba(74, 222, 128, 0.6), 0 0 12px rgba(74, 222, 128, 0.4);
}

/* Canvas Area with Professional Grid Background - Eye-Care Optimized */
.canvas-area {
  background-color: var(--bg-primary);
  /* Premium light mode grid pattern */
  background-image: 
    linear-gradient(var(--grid-color) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
  background-size: 50px 50px;
  transition: background-color 0.4s ease, background-image 0.4s ease;
}

.dark .canvas-area {
  background-color: #1e293b;
  /* Dark mode cosmic grid pattern */
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
}

/* Widget soft shadows for light mode */
.canvas-area > * {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.4s ease;
}

.dark .canvas-area > * {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.widget-accordion-enter-active,
.widget-accordion-leave-active {
  transition: all 0.22s ease;
}

.widget-accordion-enter-from,
.widget-accordion-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>

<style>
/* Unscoped: inspector pill toggles (TemplateEditor + embedded Chart* panels) */
.editor-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.375rem 0.5rem;
  border-radius: 0.5rem;
  background: rgba(241, 245, 249, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.1);
}

.dark .editor-switch-row {
  background: rgba(30, 41, 59, 0.28);
  border: 1px solid rgba(100, 116, 139, 0.35);
}

.editor-switch-row--compact {
  padding: 0.25rem 0.4rem;
  gap: 0.5rem;
}

.editor-switch-row--disabled {
  opacity: 0.5;
  pointer-events: none;
}

.editor-switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.editor-switch-track {
  width: 2.5rem;
  height: 1.35rem;
  border-radius: 9999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: rgba(226, 232, 240, 0.95);
  display: inline-flex;
  align-items: center;
  padding: 0 2px;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.dark .editor-switch-track {
  border: 1px solid rgba(100, 116, 139, 0.5);
  background: rgba(51, 65, 85, 0.7);
}

.editor-switch-thumb {
  width: 1rem;
  height: 1rem;
  border-radius: 9999px;
  background: #f8fafc;
  transform: translateX(0);
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}

.editor-switch .peer:checked + .editor-switch-track {
  background: rgba(16, 185, 129, 0.35);
  border-color: rgba(16, 185, 129, 0.9);
}

.editor-switch .peer:checked + .editor-switch-track .editor-switch-thumb {
  transform: translateX(1.1rem);
  background: #ffffff;
}

.editor-switch .peer:focus-visible + .editor-switch-track {
  outline: 2px solid rgba(59, 130, 246, 0.9);
  outline-offset: 2px;
}

.editor-switch .peer:disabled + .editor-switch-track {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>

