<template>
  <div class="relative flex flex-col items-center justify-center">
    <!-- Circular Progress Gauge -->
    <div class="relative w-32 h-32">
      <svg class="transform -rotate-90 w-32 h-32" viewBox="0 0 120 120">
        <!-- Background Circle -->
        <circle
          cx="60"
          cy="60"
          r="50"
          :stroke="bgColor"
          stroke-width="8"
          fill="none"
          opacity="0.2"
        />
        <!-- Progress Circle -->
        <circle
          cx="60"
          cy="60"
          r="50"
          :stroke="progressColor"
          stroke-width="8"
          fill="none"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="strokeDashoffset"
          :class="glowClass"
          stroke-linecap="round"
          class="transition-all duration-500 ease-out"
        />
      </svg>
      <!-- Center Text -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-2xl font-bold" :class="textColor">{{ value }}%</span>
        <span class="text-xs text-muted mt-0.5">{{ label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0,
    validator: (v) => v >= 0 && v <= 100,
  },
  label: {
    type: String,
    default: '',
  },
})

const circumference = 2 * Math.PI * 50 // radius = 50

const strokeDashoffset = computed(() => {
  return circumference - (props.value / 100) * circumference
})

const progressColor = computed(() => {
  if (props.value <= 60) return '#10b981' // green-500
  if (props.value <= 85) return '#f59e0b' // amber-500
  return '#ef4444' // red-500
})

const bgColor = computed(() => {
  if (props.value <= 60) return '#10b981' // green-500
  if (props.value <= 85) return '#f59e0b' // amber-500
  return '#ef4444' // red-500
})

const glowClass = computed(() => {
  if (props.value <= 60) return 'drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]'
  if (props.value <= 85) return 'drop-shadow-[0_0_8px_rgba(245,158,11,0.6)]'
  return 'drop-shadow-[0_0_12px_rgba(239,68,68,0.8)] animate-pulse'
})

const textColor = computed(() => {
  if (props.value <= 60) return 'text-green-400'
  if (props.value <= 85) return 'text-amber-400'
  return 'text-red-400'
})
</script>

