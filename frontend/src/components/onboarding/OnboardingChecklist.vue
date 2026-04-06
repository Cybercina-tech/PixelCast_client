<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="opacity-0 translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 -translate-y-1"
  >
    <section
      v-if="show"
      class="onboarding-checklist relative isolate overflow-hidden rounded-2xl border border-border-color bg-card/90 backdrop-blur-sm shadow-lg shadow-black/5 dark:shadow-black/20 text-slate-600 dark:text-slate-300"
      role="region"
      aria-label="Getting started checklist"
    >
      <!-- Decorative gradient -->
      <div
        class="pointer-events-none absolute inset-0 bg-gradient-to-br from-emerald-500/[0.07] via-transparent to-violet-500/[0.08] dark:from-emerald-400/10 dark:to-violet-500/10"
        aria-hidden="true"
      />
      <div
        class="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-emerald-500/10 blur-3xl dark:bg-emerald-400/15"
        aria-hidden="true"
      />

      <div class="relative p-4 sm:p-5 md:p-6">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div class="min-w-0 flex-1 space-y-1">
            <div class="flex items-center gap-2">
              <span
                class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-600 dark:bg-emerald-400/20 dark:text-emerald-400"
                aria-hidden="true"
              >
                <SparklesIcon class="h-4 w-4" />
              </span>
              <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white sm:text-xl">
                Get started
              </h2>
            </div>
            <p class="text-sm leading-relaxed text-muted pl-0 sm:pl-10">
              Finish these steps to connect screens, design layouts, and publish on a schedule.
            </p>
          </div>
          <button
            type="button"
            class="group inline-flex shrink-0 items-center justify-center gap-1.5 self-end rounded-lg px-3 py-2 text-xs font-medium text-muted transition-colors hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800/80 dark:hover:text-white sm:self-start"
            @click="dismiss"
          >
            <span>Dismiss</span>
            <XMarkIcon class="h-4 w-4 opacity-70 transition group-hover:opacity-100" aria-hidden="true" />
          </button>
        </div>

        <!-- Progress -->
        <div class="mt-5 space-y-2 sm:mt-6">
          <div class="flex items-center justify-between gap-3 text-xs sm:text-sm">
            <span class="font-medium text-slate-800 dark:text-slate-200 tabular-nums">
              {{ completedCount }} of {{ steps.length }} complete
            </span>
            <span class="tabular-nums text-muted">{{ progressPercent }}%</span>
          </div>
          <div
            class="h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-700/80"
            role="progressbar"
            :aria-valuenow="progressPercent"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="`Setup progress, ${completedCount} of ${steps.length} steps complete`"
          >
            <div
              class="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500 ease-out dark:from-emerald-400 dark:to-teal-400"
              :style="{ width: `${progressPercent}%` }"
            />
          </div>
        </div>

        <!-- Steps -->
        <ol class="mt-5 space-y-2 sm:mt-6">
          <li v-for="(step, index) in steps" :key="step.id">
            <RouterLink
              v-if="!step.done"
              :to="step.to"
              class="onboarding-step-link group flex min-h-[3.25rem] items-center gap-3 rounded-xl border border-border-color bg-white/80 px-3 py-2.5 text-slate-900 transition sm:gap-4 sm:px-4 dark:bg-slate-900/30 dark:text-white hover:border-emerald-500/40 hover:bg-emerald-50/90 dark:hover:border-emerald-400/30 dark:hover:bg-emerald-500/[0.06] active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40"
            >
              <span class="flex h-9 w-9 shrink-0 items-center justify-center" aria-hidden="true">
                <span
                  class="flex h-9 w-9 items-center justify-center rounded-full border-2 border-dashed border-slate-300 text-sm font-semibold text-muted transition group-hover:border-emerald-500/50 group-hover:text-emerald-700 dark:border-slate-600 dark:group-hover:border-emerald-400/50 dark:group-hover:text-emerald-300"
                >
                  {{ index + 1 }}
                </span>
              </span>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium leading-snug text-slate-900 dark:text-white sm:text-base">
                  {{ step.label }}
                </p>
                <p v-if="step.hint" class="mt-0.5 text-xs text-muted">
                  {{ step.hint }}
                </p>
              </div>
              <span
                class="onboarding-step-cta inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 sm:text-sm"
              >
                <span class="hidden sm:inline">{{ step.cta }}</span>
                <ArrowRightIcon class="h-4 w-4 transition group-hover:translate-x-0.5 sm:h-5 sm:w-5" aria-hidden="true" />
              </span>
            </RouterLink>
            <div
              v-else
              class="onboarding-step-done flex min-h-[3.25rem] items-center gap-3 rounded-xl border border-emerald-500/25 bg-emerald-50/90 px-3 py-2.5 text-slate-900 sm:gap-4 sm:px-4 dark:border-emerald-400/20 dark:bg-emerald-500/10 dark:text-white"
            >
              <span class="flex h-9 w-9 shrink-0 items-center justify-center" aria-hidden="true">
                <CheckCircleIcon class="h-9 w-9 text-emerald-500 dark:text-emerald-400" />
              </span>
              <div class="min-w-0 flex-1">
                <p
                  class="text-sm font-medium leading-snug line-through decoration-emerald-600/40 sm:text-base text-muted dark:decoration-emerald-400/50"
                >
                  {{ step.label }}
                </p>
              </div>
              <span class="shrink-0 text-xs font-medium text-emerald-600/90 dark:text-emerald-400/90">
                Done
              </span>
            </div>
          </li>
        </ol>
      </div>
    </section>
  </Transition>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  ArrowRightIcon,
  CheckCircleIcon,
  SparklesIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { usersAPI } from '@/services/api'
import { hasPermission } from '@/utils/permissions'

const authStore = useAuthStore()
const dismissed = ref(false)

const STORAGE_PREFIX = 'screengram_onboarding_dismissed_'

function loadDismissed(userId) {
  if (typeof window === 'undefined' || !userId) return false
  try {
    return window.localStorage.getItem(`${STORAGE_PREFIX}${userId}`) === '1'
  } catch {
    return false
  }
}

function persistDismissed(userId) {
  if (typeof window === 'undefined' || !userId) return
  try {
    window.localStorage.setItem(`${STORAGE_PREFIX}${userId}`, '1')
  } catch {
    /* ignore */
  }
}

const progress = computed(() => authStore.user?.onboarding_progress || {})

const userId = computed(() => authStore.user?.id)

watch(
  userId,
  (id) => {
    dismissed.value = id ? loadDismissed(id) : false
  },
  { immediate: true }
)

const steps = computed(() => {
  const p = progress.value || {}
  const u = authStore.user

  const screenTo =
    u && hasPermission(u, 'create_screens') ? '/screens/add' : '/screens'
  const screenCta = u && hasPermission(u, 'create_screens') ? 'Add or pair' : 'Open screens'

  return [
    {
      id: 'screen',
      label: 'Add or pair a screen',
      hint: 'Connect a player or register a new display.',
      done: !!p.has_screen,
      to: screenTo,
      cta: screenCta,
    },
    {
      id: 'template',
      label: 'Create or open a template',
      hint: 'Build a layout with widgets and branding.',
      done: !!p.has_template,
      to: '/templates',
      cta: 'Templates',
    },
    {
      id: 'schedule',
      label: 'Assign content to a schedule',
      hint: 'Publish your template and content on a timeline.',
      done: !!p.has_schedule,
      to: '/schedules',
      cta: 'Schedules',
    },
  ]
})

const completedCount = computed(() => steps.value.filter((s) => s.done).length)
const progressPercent = computed(() => {
  if (!steps.value.length) return 0
  return Math.round((completedCount.value / steps.value.length) * 100)
})

const show = computed(() => {
  if (dismissed.value) return false
  return steps.value.some((s) => !s.done)
})

async function syncProgress() {
  try {
    const { data } = await usersAPI.me()
    authStore.user = data
  } catch {
    /* ignore */
  }
}

watch(
  () => authStore.user?.id,
  () => {
    syncProgress()
  },
  { immediate: true }
)

function dismiss() {
  dismissed.value = true
  if (userId.value) {
    persistDismissed(userId.value)
  }
}
</script>

<style scoped>
/*
 * Light mode: Tailwind does not set -webkit-text-fill-color; a wrong value can inherit from
 * ancestor layers (blur / compositing) and paint white text. Force ink + fill on the card.
 */
html:not(.dark) .onboarding-checklist :deep(.onboarding-step-link),
html:not(.dark) .onboarding-checklist :deep(h2) {
  color: rgb(15 23 42) !important;
  -webkit-text-fill-color: rgb(15 23 42) !important;
}

html.dark .onboarding-checklist :deep(.onboarding-step-link),
html.dark .onboarding-checklist :deep(h2) {
  color: rgb(255 255 255) !important;
  -webkit-text-fill-color: rgb(255 255 255) !important;
}

html:not(.dark) .onboarding-checklist :deep(.onboarding-step-done) {
  color: rgb(15 23 42) !important;
  -webkit-text-fill-color: rgb(15 23 42) !important;
}

html.dark .onboarding-checklist :deep(.onboarding-step-done) {
  color: rgb(255 255 255) !important;
  -webkit-text-fill-color: rgb(255 255 255) !important;
}

html:not(.dark) .onboarding-checklist :deep(.onboarding-step-cta) {
  color: rgb(5 150 105) !important;
  -webkit-text-fill-color: rgb(5 150 105) !important;
}

html.dark .onboarding-checklist :deep(.onboarding-step-cta) {
  color: rgb(52 211 153) !important;
  -webkit-text-fill-color: rgb(52 211 153) !important;
}
</style>
