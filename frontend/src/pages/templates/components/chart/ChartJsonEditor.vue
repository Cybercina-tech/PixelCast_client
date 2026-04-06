<template>
  <div class="space-y-2">
    <h4 class="text-xs font-semibold uppercase text-gray-400">Advanced JSON</h4>
    <textarea
      :value="modelValue"
      rows="10"
      class="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-xs text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  error: {
    type: String,
    default: '',
  },
})

defineEmits(['update:modelValue'])
</script>
