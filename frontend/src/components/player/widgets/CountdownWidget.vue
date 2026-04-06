<template>
  <div
    v-if="shouldRenderRoot"
    class="countdown-widget"
    :class="rootThemeClass"
    :style="containerStyle"
  >
    <div v-if="invalidTarget" class="cd-zero cd-warn">
      Set a valid target date and time
    </div>
    <template v-else-if="!isFinished">
      <div v-if="eventTitle" class="cd-title">{{ eventTitle }}</div>
      <div class="cd-units" :class="{ 'cd-units--tight': mode === 'hms' }">
        <template v-if="mode === 'dh'">
          <div class="cd-unit">
            <div class="cd-unit-box">
              <span class="cd-num">{{ parts.d }}</span>
              <span class="cd-lbl">{{ labels.days }}</span>
            </div>
          </div>
          <div class="cd-unit">
            <div class="cd-unit-box">
              <span class="cd-num">{{ parts.h }}</span>
              <span class="cd-lbl">{{ labels.hours }}</span>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="cd-unit">
            <div class="cd-unit-box">
              <span class="cd-num">{{ parts.hh }}</span>
              <span class="cd-lbl">{{ labels.hours }}</span>
            </div>
          </div>
          <div class="cd-unit">
            <div class="cd-unit-box">
              <span class="cd-num">{{ parts.mm }}</span>
              <span class="cd-lbl">{{ labels.minutes }}</span>
            </div>
          </div>
          <div class="cd-unit">
            <div class="cd-unit-box">
              <span class="cd-num">{{ parts.ss }}</span>
              <span class="cd-lbl">{{ labels.seconds }}</span>
            </div>
          </div>
        </template>
      </div>
      <div v-if="showProgressBar" class="cd-progress-wrap" aria-hidden="true">
        <div class="cd-progress-fill" :style="{ width: `${progressPct}%` }" />
      </div>
    </template>
    <div v-else class="cd-zero">
      {{ zeroMessage }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { resolveWidgetBackgroundColor } from '@/utils/widgetBackground'
import { COUNTDOWN_THEME_DEFAULT_ID, COUNTDOWN_THEME_IDS } from '@/constants/countdownThemes'

const props = defineProps({
  widget: {
    type: Object,
    required: true,
  },
})

const playerStore = usePlayerStore()
const tick = ref(0)
let timerId = null
const mountedAtMs = ref(null)

const styleJson = computed(() => props.widget?.content_json || {})

const serverOffsetMs = computed(() => Number(playerStore.serverTimeOffsetMs) || 0)

const nowMs = computed(() => {
  tick.value
  return Date.now() + serverOffsetMs.value
})

const targetMs = computed(() => {
  const raw = styleJson.value?.targetAt
  if (!raw) return NaN
  const t = new Date(raw).getTime()
  return Number.isNaN(t) ? NaN : t
})

const invalidTarget = computed(() => Number.isNaN(targetMs.value))

const startMs = computed(() => {
  const raw = styleJson.value?.startAt
  if (raw) {
    const t = new Date(raw).getTime()
    if (!Number.isNaN(t)) return t
  }
  return mountedAtMs.value ?? Date.now()
})

const eventTitle = computed(() => {
  const fromStyle = styleJson.value?.eventTitle
  if (typeof fromStyle === 'string' && fromStyle.trim()) return fromStyle.trim()
  const content = props.widget?.content
  if (typeof content === 'string' && content.trim()) return content.trim()
  // Playback merge maps template `content` → `content_url` for the player payload
  const fromUrl = props.widget?.content_url
  if (typeof fromUrl === 'string' && fromUrl.trim()) return fromUrl.trim()
  const name = props.widget?.name
  if (typeof name === 'string' && name.trim()) return name.trim()
  return ''
})

const labels = computed(() => ({
  days: styleJson.value?.labels?.days || 'Days',
  hours: styleJson.value?.labels?.hours || 'Hours',
  minutes: styleJson.value?.labels?.minutes || 'Minutes',
  seconds: styleJson.value?.labels?.seconds || 'Seconds',
}))

const zeroMode = computed(() => (styleJson.value?.zeroStateMode === 'hideWidget' ? 'hideWidget' : 'showMessage'))

const zeroMessage = computed(() => {
  const m = styleJson.value?.zeroStateMessage
  if (typeof m === 'string' && m.trim()) return m.trim()
  return 'The event has started!'
})

const theme = computed(() => {
  const raw = styleJson.value?.theme || COUNTDOWN_THEME_DEFAULT_ID
  return COUNTDOWN_THEME_IDS.includes(raw) ? raw : COUNTDOWN_THEME_DEFAULT_ID
})

const rootThemeClass = computed(() => `cd-theme-${theme.value}`)

const showProgressBar = computed(() => styleJson.value?.showProgress === true)

const remainingMs = computed(() => {
  if (Number.isNaN(targetMs.value)) return NaN
  return Math.max(0, targetMs.value - nowMs.value)
})

const isFinished = computed(() => {
  if (Number.isNaN(targetMs.value)) return false
  return remainingMs.value <= 0
})

const shouldRenderRoot = computed(() => {
  if (zeroMode.value === 'hideWidget' && isFinished.value) return false
  return true
})

const mode = computed(() => {
  if (Number.isNaN(remainingMs.value)) return 'hms'
  const sec = Math.floor(remainingMs.value / 1000)
  return sec > 86400 ? 'dh' : 'hms'
})

const parts = computed(() => {
  const sec = Number.isNaN(remainingMs.value)
    ? 0
    : Math.max(0, Math.floor(remainingMs.value / 1000))
  const pad = (n) => String(n).padStart(2, '0')
  if (mode.value === 'dh') {
    const d = Math.floor(sec / 86400)
    const h = Math.floor((sec % 86400) / 3600)
    return { d, h, hh: pad(0), mm: pad(0), ss: pad(0) }
  }
  const hh = Math.floor(sec / 3600)
  const mm = Math.floor((sec % 3600) / 60)
  const ss = sec % 60
  return {
    d: 0,
    h: 0,
    hh: pad(hh),
    mm: pad(mm),
    ss: pad(ss),
  }
})

const progressPct = computed(() => {
  if (!showProgressBar.value) return 0
  const end = targetMs.value
  const start = startMs.value
  if (Number.isNaN(end) || end <= start) return 0
  tick.value
  const p = (nowMs.value - start) / (end - start)
  return Math.min(100, Math.max(0, p * 100))
})

const containerStyle = computed(() => {
  const s = styleJson.value
  const fs = typeof s?.fontSize === 'number' ? `${s.fontSize}px` : (s?.fontSize || '32px')
  return {
    width: '100%',
    height: '100%',
    boxSizing: 'border-box',
    padding: '12px 14px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    color: s?.color || '#f8fafc',
    fontSize: fs,
    fontFamily: s?.fontFamily || "'Inter', system-ui, sans-serif",
    fontWeight: s?.fontWeight || '800',
    textAlign: s?.textAlign || 'center',
    background: resolveWidgetBackgroundColor(s),
    borderRadius: s?.borderRadius || '12px',
    textShadow: s?.textShadow || 'none',
    overflow: 'hidden',
  }
})

onMounted(() => {
  mountedAtMs.value = Date.now()
  timerId = window.setInterval(() => {
    tick.value++
  }, 1000)
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>

<style scoped>
.countdown-widget {
  user-select: none;
  position: relative;
}

.cd-title {
  font-size: 0.42em;
  font-weight: 700;
  opacity: 0.92;
  line-height: 1.25;
  text-align: center;
  max-width: 100%;
  padding: 0 0.15em;
}

.cd-units {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  justify-content: center;
  gap: 0.4em 0.55em;
  width: 100%;
}

.cd-units--tight {
  gap: 0.28em 0.38em;
}

.cd-warn {
  font-size: 0.4em;
  font-weight: 600;
  opacity: 0.9;
}

.cd-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 2.5em;
  flex: 0 1 auto;
}

.cd-unit-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 2.35em;
  padding: 0.18em 0.32em 0.12em;
  border-radius: 0.35em;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.cd-num {
  font-size: 1em;
  line-height: 1.05;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
}

.cd-lbl {
  font-size: 0.26em;
  font-weight: 650;
  opacity: 0.88;
  margin-top: 0.18em;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.cd-progress-wrap {
  width: 100%;
  max-width: 98%;
  height: 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
  margin-top: 2px;
}

.cd-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.88);
  transition: width 1s linear;
}

.cd-zero {
  font-size: 0.52em;
  font-weight: 800;
  text-align: center;
  line-height: 1.35;
  padding: 0.25em 0.35em;
}

/* --- Theme: unit chrome (root background comes from style JSON) --- */
.cd-theme-urgency .cd-unit-box {
  background: rgba(127, 29, 29, 0.45);
  border: 1px solid rgba(254, 202, 202, 0.22);
  box-shadow: 0 0 20px rgba(248, 113, 113, 0.12);
}
.cd-theme-urgency .cd-progress-fill {
  background: linear-gradient(90deg, #f87171, #fecaca);
}

.cd-theme-celebration .cd-unit-box {
  background: rgba(120, 53, 15, 0.5);
  border: 1px solid rgba(251, 191, 36, 0.35);
  box-shadow: 0 0 18px rgba(251, 191, 36, 0.15);
}
.cd-theme-celebration {
  animation: cdCelebrate 3.5s ease-in-out infinite;
}
.cd-theme-celebration .cd-progress-fill {
  background: linear-gradient(90deg, #fde68a, #fbbf24, #f59e0b);
  background-size: 200% 100%;
  animation: cdShimmer 4s linear infinite;
}

.cd-theme-midnight .cd-unit-box {
  background: rgba(79, 70, 229, 0.2);
  border: 1px solid rgba(165, 180, 252, 0.35);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.cd-theme-midnight .cd-progress-fill {
  background: linear-gradient(90deg, #818cf8, #c4b5fd);
}

.cd-theme-neon .cd-unit-box {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(34, 211, 238, 0.45);
  box-shadow:
    0 0 12px rgba(34, 211, 238, 0.25),
    inset 0 0 20px rgba(217, 70, 239, 0.08);
}
.cd-theme-neon .cd-lbl {
  color: rgba(207, 250, 254, 0.85);
}
.cd-theme-neon .cd-progress-fill {
  background: linear-gradient(90deg, #22d3ee, #e879f9);
}

.cd-theme-minimal .cd-unit-box {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(248, 250, 252, 0.12);
}
.cd-theme-minimal .cd-progress-fill {
  background: rgba(226, 232, 240, 0.85);
}

.cd-theme-corporate .cd-unit-box {
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(125, 211, 252, 0.2);
}
.cd-theme-corporate .cd-progress-fill {
  background: linear-gradient(90deg, #38bdf8, #0ea5e9);
}

.cd-theme-sport .cd-unit-box {
  background: rgba(0, 0, 0, 0.55);
  border: 2px solid #fef08a;
  box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.5);
}
.cd-theme-sport .cd-progress-fill {
  background: #fef08a;
}

.cd-theme-forest .cd-unit-box {
  background: rgba(20, 83, 45, 0.45);
  border: 1px solid rgba(74, 222, 128, 0.28);
}
.cd-theme-forest .cd-progress-fill {
  background: linear-gradient(90deg, #4ade80, #22c55e);
}

.cd-theme-sunset .cd-unit-box {
  background: rgba(159, 18, 57, 0.35);
  border: 1px solid rgba(251, 113, 133, 0.35);
  box-shadow: 0 0 16px rgba(244, 63, 94, 0.15);
}
.cd-theme-sunset .cd-progress-fill {
  background: linear-gradient(90deg, #fb7185, #f97316);
}

.cd-theme-ice .cd-unit-box {
  background: rgba(8, 47, 73, 0.55);
  border: 1px solid rgba(186, 230, 253, 0.35);
}
.cd-theme-ice .cd-progress-fill {
  background: linear-gradient(90deg, #7dd3fc, #38bdf8);
}

.cd-theme-luxury .cd-unit-box {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(253, 230, 138, 0.45);
  box-shadow: 0 0 0 1px rgba(253, 230, 138, 0.08);
}
.cd-theme-luxury .cd-progress-fill {
  background: linear-gradient(90deg, #fde68a, #d97706);
}

.cd-theme-retro .cd-unit-box {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(74, 222, 128, 0.4);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.cd-theme-retro .cd-lbl {
  opacity: 0.95;
}
.cd-theme-retro .cd-progress-fill {
  background: #4ade80;
}

.cd-theme-ocean .cd-unit-box {
  background: rgba(17, 94, 89, 0.45);
  border: 1px solid rgba(45, 212, 191, 0.35);
}
.cd-theme-ocean .cd-progress-fill {
  background: linear-gradient(90deg, #2dd4bf, #14b8a6);
}

.cd-theme-aurora .cd-unit-box {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(167, 243, 208, 0.25);
  box-shadow: 0 0 22px rgba(52, 211, 153, 0.12);
}
.cd-theme-aurora .cd-progress-fill {
  background: linear-gradient(90deg, #34d399, #22d3ee, #a78bfa);
  background-size: 200% 100%;
  animation: cdShimmer 6s linear infinite;
}

/* Custom: flat tiles — user controls root via color pickers */
.cd-theme-custom .cd-unit-box {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
}
.cd-theme-custom .cd-progress-fill {
  background: rgba(248, 250, 252, 0.75);
}

@keyframes cdCelebrate {
  0%,
  100% {
    filter: brightness(1);
  }
  50% {
    filter: brightness(1.06);
  }
}

@keyframes cdShimmer {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cd-theme-celebration,
  .cd-theme-aurora .cd-progress-fill,
  .cd-theme-celebration .cd-progress-fill {
    animation: none !important;
  }
}
</style>
