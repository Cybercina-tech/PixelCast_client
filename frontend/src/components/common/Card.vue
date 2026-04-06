<template>
  <div class="card-base rounded-2xl p-6" :class="cardClass">
    <div v-if="title" class="mb-4">
      <h3 class="text-lg font-semibold text-primary leading-tight">{{ title }}</h3>
      <p v-if="subtitle" class="mt-1.5 text-sm text-secondary leading-relaxed">{{ subtitle }}</p>
    </div>
    <slot></slot>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  cardClass: {
    type: String,
    default: '',
  },
})
</script>
