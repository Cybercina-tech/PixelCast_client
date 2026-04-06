<template>
  <button
    @click="toggleTheme"
    :aria-label="`Switch to ${themeStore.theme === 'dark' ? 'light' : 'dark'} mode`"
    class="relative p-2 rounded-xl bg-card border border-border-color hover:bg-card transition-all duration-300 group focus:outline-none focus:ring-2 focus:ring-blue-500/50 dark:focus:ring-emerald-400/50"
    style="backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);"
  >
    <Transition
      name="theme-icon"
      mode="out-in"
    >
      <SunIcon
        v-if="themeStore.theme === 'dark'"
        key="sun"
        class="w-5 h-5 text-amber-500 dark:text-amber-400 transition-all duration-300 group-hover:rotate-180"
        stroke-width="2.5"
      />
      <MoonIcon
        v-else
        key="moon"
        class="w-5 h-5 text-blue-600 dark:text-slate-300 transition-all duration-300 group-hover:-rotate-12"
        stroke-width="2.5"
      />
    </Transition>
  </button>
</template>

<script setup>
import { SunIcon, MoonIcon } from '@heroicons/vue/24/outline'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

const toggleTheme = () => {
  themeStore.toggleTheme()
}
</script>

<style scoped>
.theme-icon-enter-active,
.theme-icon-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.theme-icon-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.8);
}

.theme-icon-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.8);
}
</style>

