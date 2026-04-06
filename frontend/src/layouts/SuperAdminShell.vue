<template>
  <div class="flex h-screen overflow-hidden starry-background relative text-primary">
    <div class="starry-blobs pointer-events-none" aria-hidden="true">
      <div class="starry-blob starry-blob-1" />
      <div class="starry-blob starry-blob-2" />
      <div class="starry-blob starry-blob-3" />
    </div>

    <!-- Mobile overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden"
      @click="sidebarOpen = false"
    />

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed lg:static inset-y-0 left-0 z-40 w-72 max-w-[88vw] shrink-0 flex flex-col backdrop-blur-xl shadow-[var(--shadow-soft)] transition-transform duration-300 ease-out',
        sidebarSurfaceClass,
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]"
      aria-label="Super Admin navigation"
    >
      <div :class="['p-4 border-b', isDarkTheme ? 'border-slate-700/70' : 'border-slate-200']">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-cyan-500/90 to-violet-600/90 text-white shadow-lg shrink-0"
          >
            <ShieldCheckIcon class="w-6 h-6" />
          </div>
          <div class="min-w-0 flex-1">
            <p :class="['text-sm font-bold truncate', isDarkTheme ? 'text-white' : 'text-slate-900']">Super Admin</p>
            <p :class="['text-xs truncate', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">SaaS control plane</p>
          </div>
          <span :class="['text-[10px] px-2 py-1 rounded-full', isDarkTheme ? 'border-cyan-500/30 bg-cyan-500/12 text-cyan-300' : 'border-cyan-600/30 bg-cyan-600/10 text-cyan-700']">
            LIVE
          </span>
        </div>
        <div :class="['mt-3 rounded-xl border px-3 py-2 text-xs', isDarkTheme ? 'border-slate-700/70 bg-slate-800/70 text-slate-400' : 'border-slate-200 bg-white/75 text-slate-500']">
          {{ activeGroupLabel }}
          <span class="mx-1">•</span>
          {{ navItemCount }} sections
        </div>
      </div>

      <nav class="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-4">
        <div v-for="group in SUPER_ADMIN_NAV_GROUPS" :key="group.id">
          <p :class="['px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-wider', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">
            {{ group.label }}
          </p>
          <ul class="space-y-1">
            <li v-for="link in group.items" :key="link.to">
              <router-link
                :to="link.to"
                class="group flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-all"
                :class="navClass(link)"
                @click="sidebarOpen = false"
              >
                <component :is="iconFor(link.icon)" class="w-5 h-5 shrink-0 transition-transform group-hover:scale-105" />
                <span class="truncate">{{ link.label }}</span>
              </router-link>
            </li>
          </ul>
        </div>
      </nav>

      <div :class="['p-3 border-t space-y-2', isDarkTheme ? 'border-slate-700/70' : 'border-slate-200']">
        <router-link
          to="/dashboard"
          :class="[
            'flex items-center justify-center gap-2 w-full rounded-xl px-3 py-2.5 text-sm font-medium border transition-colors',
            isDarkTheme
              ? 'text-slate-200 border-slate-700 hover:bg-slate-800/80'
              : 'text-slate-700 border-slate-200 hover:bg-slate-100',
          ]"
        >
          <ArrowLeftIcon class="w-4 h-4 shrink-0" />
          Back to app
        </router-link>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0 relative z-10">
      <header
        :class="[
          'shrink-0 sticky top-0 z-20 border-b px-4 md:px-6 py-3 flex items-center gap-3 backdrop-blur-md',
          isDarkTheme
            ? 'border-slate-700/70 bg-slate-900/70'
            : 'border-slate-200 bg-white/75',
        ]"
      >
        <button
          type="button"
          :class="[
            'lg:hidden p-2 rounded-lg border',
            isDarkTheme
              ? 'border-slate-700 text-slate-200 hover:bg-slate-800'
              : 'border-slate-200 text-slate-700 hover:bg-slate-100',
          ]"
          aria-label="Open menu"
          @click="sidebarOpen = true"
        >
          <Bars3Icon class="w-5 h-5" />
        </button>
        <div class="flex-1 min-w-0">
          <p :class="['text-[11px] uppercase tracking-wider mb-0.5', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">Control Plane</p>
          <h1 :class="['text-lg md:text-xl font-bold truncate', isDarkTheme ? 'text-white' : 'text-slate-900']">{{ pageTitle }}</h1>
          <p v-if="pageSubtitle" :class="['text-xs truncate mt-0.5', isDarkTheme ? 'text-slate-400' : 'text-slate-500']">{{ pageSubtitle }}</p>
        </div>
        <div :class="['hidden md:flex items-center gap-2 text-xs shrink-0', isDarkTheme ? 'text-slate-300' : 'text-slate-600']">
          <span :class="['px-2 py-1 rounded-lg border', isDarkTheme ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : 'bg-amber-500/12 text-amber-700 border-amber-600/30']">
            Developer
          </span>
        </div>
      </header>
      <main class="flex-1 overflow-y-auto custom-scrollbar p-4 md:p-6 lg:p-8">
        <div class="mx-auto max-w-[1400px]">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import {
  ArrowLeftIcon,
  Bars3Icon,
  ShieldCheckIcon,
  Squares2X2Icon,
  BuildingOffice2Icon,
  UsersIcon,
  CurrencyDollarIcon,
  TagIcon,
  ArrowPathIcon,
  BellAlertIcon,
  ChartBarIcon,
  ServerStackIcon,
  ChatBubbleLeftRightIcon,
  ClipboardDocumentListIcon,
  CpuChipIcon,
  FlagIcon,
  Cog6ToothIcon,
  EnvelopeIcon,
  NewspaperIcon,
  SparklesIcon,
  KeyIcon,
} from '@heroicons/vue/24/outline'
import { SUPER_ADMIN_NAV_GROUPS } from '@/config/superAdminNav'

const route = useRoute()
const sidebarOpen = ref(false)
const themeStore = useThemeStore()

const iconMap = {
  Squares2X2Icon,
  BuildingOffice2Icon,
  UsersIcon,
  CurrencyDollarIcon,
  TagIcon,
  ArrowPathIcon,
  BellAlertIcon,
  ChartBarIcon,
  ServerStackIcon,
  ChatBubbleLeftRightIcon,
  ClipboardDocumentListIcon,
  CpuChipIcon,
  FlagIcon,
  Cog6ToothIcon,
  EnvelopeIcon,
  NewspaperIcon,
  SparklesIcon,
  KeyIcon,
}

function iconFor(name) {
  return iconMap[name] || Squares2X2Icon
}

function isTicketsQueueNavActive(path) {
  const p = path.replace(/\/$/, '') || '/'
  if (p === '/super-admin/tickets') return true
  if (!p.startsWith('/super-admin/tickets/')) return false
  const first = p.slice('/super-admin/tickets/'.length).split('/')[0]
  if (!first) return false
  if (first === 'analytics' || first === 'settings') return false
  return true
}

function isNavActive(link) {
  if (link.match === 'exact') {
    return route.path === link.to || route.path === `${link.to}/`
  }
  if (link.match === 'tickets-queue') {
    return isTicketsQueueNavActive(route.path)
  }
  return route.path === link.to || route.path.startsWith(`${link.to}/`)
}

function navClass(link) {
  if (isNavActive(link)) {
    return isDarkTheme.value
      ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-[0_0_0_1px_rgba(56,189,248,.25)]'
      : 'bg-cyan-50 text-cyan-700 border border-cyan-200 shadow-[0_0_0_1px_rgba(14,116,144,.08)]'
  }
  return isDarkTheme.value
    ? 'text-slate-300 hover:bg-slate-800/80 hover:text-white border border-transparent'
    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-transparent'
}

const pageTitle = computed(() => route.meta.superAdminTitle || 'Super Admin')
const isDarkTheme = computed(() => themeStore.isDarkMode)

const sidebarSurfaceClass = computed(() =>
  isDarkTheme.value
    ? 'border-r border-slate-700/80 bg-slate-900/90'
    : 'border-r border-slate-200 bg-white/90'
)

const pageSubtitle = computed(() => route.meta.superAdminSubtitle || '')

const navItemCount = computed(() =>
  SUPER_ADMIN_NAV_GROUPS.reduce((acc, group) => acc + group.items.length, 0)
)

const activeGroupLabel = computed(() => {
  const group = SUPER_ADMIN_NAV_GROUPS.find((g) => g.items.some((item) => isNavActive(item)))
  return group?.label || 'Overview'
})
</script>
