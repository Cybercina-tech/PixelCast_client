<template>
  <div class="marquee-widget" :style="containerStyle">
    <div v-if="!resolvedText" class="marquee-fallback" :style="textVisualStyle">[No marquee content]</div>
    <div
      v-else
      class="marquee-track"
      :class="[
        `mode-${safeMode}`,
        `dir-${effectiveDirection}`,
        {
          'is-vertical': isVertical,
          'fade-enabled': fadeEdgeEnabled,
        }
      ]"
      :style="trackStyle"
    >
      <template v-if="safeMode === 'continuous'">
        <span class="marquee-item" dir="auto" :style="itemStyle">{{ resolvedText }}</span>
        <span class="marquee-item" dir="auto" :style="itemStyle">{{ resolvedText }}</span>
      </template>
      <template v-else>
        <span class="marquee-item single" dir="auto" :style="itemStyle">{{ resolvedText }}</span>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { resolveWidgetBackgroundColor } from '@/utils/widgetBackground'

const props = defineProps({
  widget: {
    type: Object,
    required: true,
  },
})

const clamp = (value, fallback, min, max) => {
  const parsed = Number.parseFloat(String(value ?? '').trim())
  if (!Number.isFinite(parsed)) return fallback
  return Math.max(min, Math.min(max, parsed))
}

const styleJson = computed(() => props.widget?.content_json || {})

const resolvedText = computed(() => {
  const contents = Array.isArray(props.widget?.contents) ? props.widget.contents : []
  const active = contents
    .filter(content => content?.is_active !== false)
    .sort((a, b) => (a?.order || 0) - (b?.order || 0))
  const first = active[0]
  const text = first?.text_content || first?.content_json?.text || styleJson.value?.text || ''
  if (typeof text !== 'string') return ''
  const separator = styleJson.value.separator || ' • '
  const sanitized = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean).join(` ${separator} `)
  return styleJson.value.uppercase ? sanitized.toUpperCase() : sanitized
})

const safeMode = computed(() => {
  const mode = styleJson.value.mode
  return ['continuous', 'step', 'bounce'].includes(mode) ? mode : 'continuous'
})

const safeDirection = computed(() => {
  const direction = styleJson.value.direction
  return ['left', 'right', 'up', 'down'].includes(direction) ? direction : 'left'
})

const reverseEnabled = computed(() => styleJson.value.reverse === true)
const oppositeDirection = {
  left: 'right',
  right: 'left',
  up: 'down',
  down: 'up',
}
const effectiveDirection = computed(() => (
  reverseEnabled.value ? oppositeDirection[safeDirection.value] : safeDirection.value
))
const isVertical = computed(() => effectiveDirection.value === 'up' || effectiveDirection.value === 'down')

const durationSeconds = computed(() => {
  const speed = clamp(styleJson.value.speed, 120, 20, 800)
  // Keep deterministic speed: base travel distance of 1200px for horizontal and 800px for vertical.
  const baseline = isVertical.value ? 800 : 1200
  return Math.max(1.2, baseline / speed)
})

const holdSeconds = computed(() => {
  if (safeMode.value === 'step') return clamp(styleJson.value.stepHold, 1.5, 0.2, 12)
  if (safeMode.value === 'bounce') return clamp(styleJson.value.bounceHold, 0.8, 0, 5)
  return 0
})

const loopEnabled = computed(() => styleJson.value.loop !== false)
const gapPx = computed(() => clamp(styleJson.value.gap, 80, 16, 500))
const fadeEdgeEnabled = computed(() => styleJson.value.fadeEdge !== false)
const containerStyle = computed(() => {
  const bg = resolveWidgetBackgroundColor(styleJson.value, '#111827')
  return {
    '--marquee-duration': `${durationSeconds.value}s`,
    '--marquee-hold': `${holdSeconds.value}s`,
    '--marquee-gap': `${gapPx.value}px`,
    '--marquee-iteration': loopEnabled.value ? 'infinite' : '1',
    '--marquee-bg': bg,
    width: '100%',
    height: '100%',
    boxSizing: 'border-box',
    paddingTop: '3px',
    paddingBottom: '6px',
    overflow: 'hidden',
    backgroundColor: bg,
    position: 'relative',
  }
})

const buildShadow = (raw) => {
  if (!raw || typeof raw !== 'string') return 'none'
  return raw
}

const textVisualStyle = computed(() => ({
  fontFamily: styleJson.value.fontFamily || "'Segoe UI', Arial, sans-serif",
  fontSize: styleJson.value.fontSize || '42px',
  fontWeight: styleJson.value.fontWeight || '700',
  lineHeight: styleJson.value.lineHeight || 1.2,
  letterSpacing: styleJson.value.letterSpacing || '0.01em',
  color: styleJson.value.color || '#ffffff',
  textShadow: buildShadow(styleJson.value.textShadow),
  WebkitTextStroke: styleJson.value.strokeWidth ? `${clamp(styleJson.value.strokeWidth, 1, 0, 10)}px ${styleJson.value.strokeColor || '#000000'}` : undefined,
}))

/**
 * Continuous marquee must size the track to the duplicated content width/height so that
 * translate(-50%) in keyframes equals exactly one copy (classic ticker). A track forced
 * to 100% width made -50% = half the viewport, not half the strip — broken loop + clipping.
 */
const trackStyle = computed(() => {
  const flexRow = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-start',
  }
  if (safeMode.value === 'continuous') {
    if (isVertical.value) {
      return {
        ...flexRow,
        flexDirection: 'column',
        width: '100%',
        height: 'max-content',
      }
    }
    return {
      ...flexRow,
      width: 'max-content',
      maxWidth: 'none',
      height: '100%',
      direction: 'ltr',
    }
  }
  return {
    ...flexRow,
    width: '100%',
    height: '100%',
  }
})

const itemStyle = computed(() => ({
  ...textVisualStyle.value,
}))
</script>

<style scoped>
.marquee-widget {
  width: 100%;
  height: 100%;
  user-select: none;
  contain: layout style;
  position: relative;
  z-index: 0;
}

.marquee-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  text-align: center;
  background: rgba(15, 23, 42, 0.75);
}

.marquee-track {
  will-change: transform;
  position: relative;
}

.marquee-item {
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
  flex: 0 0 auto;
  padding-right: var(--marquee-gap, 80px);
  position: relative;
  z-index: 2;
}

.marquee-track.is-vertical {
  flex-direction: column;
  justify-content: flex-start;
}

.marquee-track.is-vertical .marquee-item {
  writing-mode: horizontal-tb;
  white-space: normal;
  width: 100%;
  text-align: center;
  justify-content: center;
  padding-right: 0;
  padding-bottom: var(--marquee-gap, 80px);
}

.mode-continuous.dir-left {
  animation: marquee-left var(--marquee-duration) linear var(--marquee-iteration);
}

.mode-continuous.dir-right {
  animation: marquee-right var(--marquee-duration) linear var(--marquee-iteration);
}

.mode-continuous.dir-up {
  animation: marquee-up var(--marquee-duration) linear var(--marquee-iteration);
}

.mode-continuous.dir-down {
  animation: marquee-down var(--marquee-duration) linear var(--marquee-iteration);
}

/* Horizontal step: forward = text travels right→left (matches continuous dir-left); reverse = left→right */
.mode-step.dir-left {
  animation: marquee-step-forward calc(var(--marquee-duration) + var(--marquee-hold)) linear var(--marquee-iteration);
}

.mode-step.dir-right {
  animation: marquee-step-reverse calc(var(--marquee-duration) + var(--marquee-hold)) linear var(--marquee-iteration);
}

.mode-step.dir-up {
  animation: marquee-step-up calc(var(--marquee-duration) + var(--marquee-hold)) linear var(--marquee-iteration);
}

.mode-step.dir-down {
  animation: marquee-step-down calc(var(--marquee-duration) + var(--marquee-hold)) linear var(--marquee-iteration);
}

.mode-bounce.dir-left {
  animation: marquee-bounce-forward calc(var(--marquee-duration) + var(--marquee-hold)) ease-in-out var(--marquee-iteration);
}

.mode-bounce.dir-right {
  animation: marquee-bounce-reverse calc(var(--marquee-duration) + var(--marquee-hold)) ease-in-out var(--marquee-iteration);
}

.mode-bounce.dir-up {
  animation: marquee-bounce-up calc(var(--marquee-duration) + var(--marquee-hold)) ease-in-out var(--marquee-iteration);
}

.mode-bounce.dir-down {
  animation: marquee-bounce-down calc(var(--marquee-duration) + var(--marquee-hold)) ease-in-out var(--marquee-iteration);
}

@keyframes marquee-left {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

@keyframes marquee-right {
  from { transform: translateX(-50%); }
  to { transform: translateX(0); }
}

@keyframes marquee-up {
  from { transform: translateY(0); }
  to { transform: translateY(-50%); }
}

@keyframes marquee-down {
  from { transform: translateY(-50%); }
  to { transform: translateY(0); }
}

@keyframes marquee-step-forward {
  0% { transform: translateX(100%); }
  75% { transform: translateX(-100%); }
  100% { transform: translateX(-100%); }
}

@keyframes marquee-step-reverse {
  0% { transform: translateX(-100%); }
  75% { transform: translateX(100%); }
  100% { transform: translateX(100%); }
}

@keyframes marquee-step-up {
  0% { transform: translateY(100%); }
  75% { transform: translateY(-100%); }
  100% { transform: translateY(-100%); }
}

@keyframes marquee-step-down {
  0% { transform: translateY(-100%); }
  75% { transform: translateY(100%); }
  100% { transform: translateY(100%); }
}

@keyframes marquee-bounce-forward {
  0% { transform: translateX(100%); }
  50% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes marquee-bounce-reverse {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}

@keyframes marquee-bounce-up {
  0% { transform: translateY(100%); }
  50% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

@keyframes marquee-bounce-down {
  0% { transform: translateY(-100%); }
  50% { transform: translateY(100%); }
  100% { transform: translateY(-100%); }
}

.marquee-track.fade-enabled::before,
.marquee-track.fade-enabled::after {
  content: '';
  position: absolute;
  pointer-events: none;
  z-index: 1;
}

.marquee-track.fade-enabled:not(.is-vertical)::before,
.marquee-track.fade-enabled:not(.is-vertical)::after {
  top: 0;
  bottom: 0;
  width: 6%;
}

.marquee-track.fade-enabled:not(.is-vertical)::before {
  left: 0;
  background: linear-gradient(to right, var(--marquee-bg), transparent);
}

.marquee-track.fade-enabled:not(.is-vertical)::after {
  right: 0;
  background: linear-gradient(to left, var(--marquee-bg), transparent);
}

.marquee-track.fade-enabled.is-vertical::before,
.marquee-track.fade-enabled.is-vertical::after {
  left: 0;
  right: 0;
  height: 16%;
}

.marquee-track.fade-enabled.is-vertical::before {
  top: 0;
  background: linear-gradient(to bottom, var(--marquee-bg), transparent);
}

.marquee-track.fade-enabled.is-vertical::after {
  bottom: 0;
  background: linear-gradient(to top, var(--marquee-bg), transparent);
}
</style>
