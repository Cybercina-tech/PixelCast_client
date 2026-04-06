<template>
  <button
    :class="[
      'toggle-switch',
      { 'toggle-switch-active': modelValue, 'toggle-switch-disabled': disabled },
    ]"
    @click="toggle"
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :aria-label="ariaLabel"
    :disabled="disabled"
  >
    <span class="toggle-switch-track">
      <span class="toggle-switch-thumb"></span>
    </span>
  </button>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  ariaLabel: {
    type: String,
    default: 'Toggle',
  },
})

const emit = defineEmits(['update:modelValue'])

const toggle = () => {
  if (props.disabled) return
  emit('update:modelValue', !props.modelValue)
}
</script>

<style scoped>
.toggle-switch {
  position: relative;
  width: 46px;
  height: 26px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.toggle-switch-track {
  width: 100%;
  height: 100%;
  border-radius: 9999px;
  background: rgba(148, 163, 184, 0.25);
  border: 1px solid rgba(148, 163, 184, 0.35);
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.toggle-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.28);
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.toggle-switch-active .toggle-switch-track {
  background: rgba(6, 182, 212, 0.35);
  border-color: rgba(6, 182, 212, 0.9);
}

.toggle-switch-active .toggle-switch-thumb {
  transform: translateX(20px);
  background: #06b6d4;
}

.toggle-switch:hover:not(.toggle-switch-disabled) .toggle-switch-track {
  border-color: rgba(6, 182, 212, 0.6);
}

.toggle-switch:focus-visible {
  outline: 2px solid rgba(6, 182, 212, 0.9);
  outline-offset: 2px;
}

.toggle-switch-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>

