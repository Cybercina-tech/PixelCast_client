<template>
  <div class="date-widget" :style="dateStyle">
    <div v-if="displayMode === 'stacked'" class="date-stacked">
      <span class="date-main">{{ formattedDate }}</span>
      <span v-if="showWeekday" class="date-weekday">{{ formattedWeekday }}</span>
    </div>
    <span v-else>{{ inlineValue }}</span>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { formatDateValue, formatWeekdayValue } from '@/utils/dateTimeFormatters'
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

/** Mirrors clock widget: dateOnly | datePlusWeekday | stacked; legacy `inline` maps from showWeekday */
const displayMode = computed(() => {
  const raw = styleJson.value?.displayMode
  if (raw === 'stacked' || raw === 'datePlusWeekday') return raw
  if (raw === 'timePlusWeekday') return 'datePlusWeekday'
  if (raw === 'dateOnly' || raw === 'timeOnly') return 'dateOnly'
  if (raw === 'inline') {
    return styleJson.value?.showWeekday === true ? 'datePlusWeekday' : 'dateOnly'
  }
  return 'dateOnly'
})

const showWeekday = computed(() => {
  if (styleJson.value?.showWeekday === true) return true
  return displayMode.value !== 'dateOnly'
})

const formattedDate = computed(() => {
  return formatDateValue(now.value, {
    ...styleJson.value,
    format: styleJson.value?.format || props.widget?.content || props.widget?.content_url || 'YYYY-MM-DD'
  }, 'YYYY-MM-DD')
})

const formattedWeekday = computed(() => formatWeekdayValue(now.value, styleJson.value || {}))

const inlineValue = computed(() => {
  if (!showWeekday.value) return formattedDate.value
  if (displayMode.value === 'datePlusWeekday') {
    return `${formattedWeekday.value} | ${formattedDate.value}`
  }
  return formattedDate.value
})

const dateStyle = computed(() => {
  const style = styleJson.value
  const resolvedFontSize = typeof style.fontSize === 'number'
    ? `${style.fontSize}px`
    : (typeof style.fontSize === 'string' && style.fontSize.trim() ? style.fontSize : '40px')

  return {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: style.textAlign === 'right' ? 'flex-end' : style.textAlign === 'left' ? 'flex-start' : 'center',
    color: style.color || '#ffffff',
    fontSize: resolvedFontSize,
    fontFamily: style.fontFamily || 'Arial, sans-serif',
    fontWeight: style.fontWeight || '600',
    backgroundColor: resolveWidgetBackgroundColor(style),
    padding: '12px',
    boxSizing: 'border-box',
    textAlign: style.textAlign || 'center',
    borderRadius: style.borderRadius || '0',
    textShadow: style.textShadow || 'none'
  }
})

onMounted(() => {
  timerId = setInterval(() => {
    now.value = new Date()
  }, 60000)
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>

<style scoped>
.date-widget {
  user-select: none;
  overflow: hidden;
  white-space: nowrap;
}

.date-stacked {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.date-weekday {
  margin-top: 0.25em;
  font-size: 0.5em;
  opacity: 0.95;
}
</style>
