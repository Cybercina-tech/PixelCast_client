<template>
  <div class="flex flex-col h-full min-h-0 bg-card border-r border-border-color transition-all duration-200">
    <div class="bg-card border-b border-border-color px-4 py-3 shrink-0 flex items-center justify-between gap-2">
      <h2 class="text-lg font-semibold text-primary">Widget Library</h2>
      <slot name="headerEnd" />
    </div>
    <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar scroll-container p-2 p-4">
      <div class="space-y-3">
        <div
          v-for="section in sections"
          :key="section.id"
          class="rounded-xl border border-border-color/80 bg-card/60 backdrop-blur-sm shadow-soft overflow-hidden"
          :style="widgetSectionCardStyle(section.id)"
        >
          <button
            class="w-full px-3 py-2.5 flex items-center justify-between text-left transition-colors"
            :style="widgetSectionHeaderStyle(section.id)"
            @click="toggleWidgetSection(section.id)"
          >
            <span class="text-[11px] uppercase tracking-wide text-muted font-semibold">
              {{ section.label }}
            </span>
            <svg
              class="w-4 h-4 text-muted transition-transform duration-200"
              :class="{ 'rotate-180': isWidgetSectionOpen(section.id) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <transition name="widget-accordion">
            <div
              v-show="isWidgetSectionOpen(section.id)"
              class="space-y-2 p-2 pt-0"
            >
              <button
                v-for="item in section.items"
                :key="item.type"
                @click="$emit('add-widget', item.type)"
                class="w-full px-4 py-3 bg-card hover:bg-card active:scale-95 rounded-lg text-left text-primary transition-all duration-300 flex items-center gap-2 font-medium border border-border-color hover:border-accent-color/50"
                style="--accent-color: var(--accent-color);"
              >
                <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.iconPath" />
                </svg>
                <span>{{ item.label }}</span>
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sections: { type: Array, required: true },
  widgetSectionCardStyle: { type: Function, required: true },
  widgetSectionHeaderStyle: { type: Function, required: true },
  isWidgetSectionOpen: { type: Function, required: true },
  toggleWidgetSection: { type: Function, required: true },
})

defineEmits(['add-widget'])
</script>
