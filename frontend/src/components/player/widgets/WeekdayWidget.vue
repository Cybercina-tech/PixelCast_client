<template>
  <div class="weekday-widget" :style="weekdayStyle">
    {{ formattedWeekday }}
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { formatWeekdayValue } from '@/utils/dateTimeFormatters'
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

const formattedWeekday = computed(() => formatWeekdayValue(now.value, styleJson.value || {}))

const weekdayStyle = computed(() => {
  const style = styleJson.value
  const resolvedFontSize = typeof style.fontSize === 'number'
    ? `${style.fontSize}px`
    : (typeof style.fontSize === 'string' && style.fontSize.trim() ? style.fontSize : '42px')

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
.weekday-widget {
  user-select: none;
  overflow: hidden;
  white-space: nowrap;
}
</style>
