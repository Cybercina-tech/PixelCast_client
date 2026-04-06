<template>
  <div class="clock-widget" :style="clockStyle">
    <div v-if="displayMode === 'stacked'" class="clock-stacked">
      <span class="clock-time">{{ formattedTime }}</span>
      <span v-if="showWeekday" class="clock-weekday">{{ formattedWeekday }}</span>
    </div>
    <span v-else>{{ inlineValue }}</span>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { formatClockValue, formatWeekdayValue } from '@/utils/dateTimeFormatters'
import { resolveWidgetBackgroundColor } from '@/utils/widgetBackground'

const props = defineProps({
  widget: {
    type: Object,
    required: true
  }
})

const now = ref(new Date())
let timerId = null

const styleJson = computed(() => props.widget?.content_json || {})

const clockStyle = computed(() => {
  const style = styleJson.value
  const resolvedFontSize = typeof style.fontSize === 'number'
    ? `${style.fontSize}px`
    : (typeof style.fontSize === 'string' && style.fontSize.trim() ? style.fontSize : '48px')
  return {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: style.textAlign === 'right' ? 'flex-end' : style.textAlign === 'left' ? 'flex-start' : 'center',
    color: style.color || '#ffffff',
    fontSize: resolvedFontSize,
    fontFamily: style.fontFamily || 'Arial, sans-serif',
    fontWeight: style.fontWeight || '700',
    lineHeight: style.lineHeight || 1.1,
    letterSpacing: style.letterSpacing || '0',
    backgroundColor: resolveWidgetBackgroundColor(style),
    padding: '12px',
    boxSizing: 'border-box',
    textAlign: style.textAlign || 'center',
    borderRadius: style.borderRadius || '0',
    textShadow: style.textShadow || 'none'
  }
})

const displayMode = computed(() => {
  const raw = styleJson.value?.displayMode
  if (raw === 'stacked' || raw === 'timePlusWeekday') return raw
  return 'timeOnly'
})

const showWeekday = computed(() => {
  if (styleJson.value?.showWeekday === true) return true
  return displayMode.value !== 'timeOnly'
})

const formattedTime = computed(() => {
  const d = now.value
  return formatClockValue(d, {
    ...styleJson.value,
    format: styleJson.value?.format || props.widget?.content || props.widget?.content_url || 'HH:mm:ss'
  }, 'HH:mm:ss')
})

const formattedWeekday = computed(() => {
  return formatWeekdayValue(now.value, styleJson.value || {})
})

const inlineValue = computed(() => {
  if (!showWeekday.value) return formattedTime.value
  if (displayMode.value === 'timePlusWeekday') {
    return `${formattedWeekday.value} | ${formattedTime.value}`
  }
  return formattedTime.value
})

onMounted(() => {
  timerId = setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>

<style scoped>
.clock-widget {
  user-select: none;
  overflow: hidden;
  white-space: nowrap;
}

.clock-stacked {
  display: flex;
  flex-direction: column;
  width: 100%;
  line-height: 1.1;
}

.clock-time {
  font-size: inherit;
}

.clock-weekday {
  margin-top: 0.2em;
  font-size: 0.45em;
  opacity: 0.95;
}
</style>
