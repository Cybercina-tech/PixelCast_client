<template>
  <AppLayout>
    <!-- Background - Hidden in Light Mode for Eye-Care -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden z-0 opacity-0 dark:opacity-100 transition-opacity duration-400">
      <!-- Animated Stars (Dark Mode Only) -->
      <div class="absolute inset-0" ref="starsContainer"></div>
      <!-- Gradient Glow (Dark Mode Only) -->
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      <div class="absolute top-1/2 left-1/2 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
    </div>

    <!-- Dashboard Content -->
    <div class="relative z-10 min-h-full space-y-6 md:space-y-8 pb-6 md:pb-8">
        <!-- Header with Live Clock -->
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold text-primary mb-2">
              <span class="text-primary dark:bg-gradient-to-r dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 dark:bg-clip-text dark:text-transparent">
                Command Center
              </span>
            </h1>
            <p class="text-muted">Real-time monitoring and control</p>
          </div>
          <!-- Live Clock Widget -->
          <div class="card-base backdrop-blur-md rounded-2xl p-4 md:p-6">
            <div class="text-center">
              <div class="text-2xl md:text-3xl font-mono font-bold text-primary mb-1">
                {{ currentTime }}
              </div>
              <div class="text-sm text-muted">{{ currentDate }}</div>
            </div>
          </div>
        </div>

        <OnboardingChecklist />


        <!-- Loading Skeleton -->
        <div v-if="loading && !hasData" class="space-y-6 md:space-y-8">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div v-for="i in 4" :key="i" class="card-base rounded-2xl p-6 animate-pulse">
              <div class="h-4 bg-card rounded w-24 mb-4"></div>
              <div class="h-8 bg-card rounded w-16"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div class="card-base rounded-2xl p-6 animate-pulse">
              <div class="h-6 bg-card rounded w-32 mb-6"></div>
              <div class="h-48 bg-card rounded"></div>
            </div>
            <div class="card-base rounded-2xl p-6 animate-pulse">
              <div class="h-6 bg-card rounded w-32 mb-6"></div>
              <div class="space-y-4">
                <div v-for="i in 5" :key="i" class="h-16 bg-card rounded"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Dashboard Content -->
        <div v-else class="space-y-6 md:space-y-8">
          <!-- Hero Stat Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <!-- Total Screens Card -->
            <div class="card-base rounded-2xl p-6 hover:shadow-xl transition-all duration-400 group relative overflow-hidden screen-stat-card">
              <div class="relative z-10">
                <div class="flex items-start justify-between mb-4">
                  <div>
                    <p class="text-sm font-medium text-muted mb-1">Total Screens</p>
                    <p class="text-3xl font-bold text-primary">
                      {{ stats.totalScreens }}
                    </p>
                    <p class="text-xs text-muted mt-1">{{ stats.onlineScreens }} online / {{ stats.offlineScreens }} offline</p>
                  </div>
                  <div class="w-12 h-12 rounded-xl bg-card flex items-center justify-center transition-colors">
                    <TvIcon class="w-6 h-6 text-accent-color" style="color: var(--accent-color);" />
                  </div>
                </div>
                <!-- Sparkline Chart -->
                <div class="h-12 mt-4">
                  <svg class="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <polyline
                      :points="generateSparklinePoints(screenTrend)"
                      fill="none"
                      stroke="var(--accent-color)"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      opacity="0.6"
                    />
                  </svg>
                </div>
              </div>
            </div>

            <!-- Online Now Card -->
            <div class="card-base rounded-2xl p-6 hover:shadow-xl transition-all duration-400 group relative overflow-hidden screen-stat-card screen-stat-card-online">
              <div class="relative z-10">
                <div class="flex items-start justify-between mb-4">
                  <div>
                    <p class="text-sm font-medium text-muted mb-1">Online Now</p>
                    <p class="text-3xl font-bold text-primary">
                      {{ stats.onlineScreens }}
                    </p>
                    <p class="text-xs text-muted mt-1">{{ onlinePercentage }}% availability</p>
                  </div>
                  <div class="w-12 h-12 rounded-xl bg-card flex items-center justify-center transition-colors">
                    <div class="w-3 h-3 rounded-full bg-forest-green animate-pulse"></div>
                  </div>
                </div>
                <!-- Sparkline Chart -->
                <div class="h-12 mt-4">
                  <svg class="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <polyline
                      :points="generateSparklinePoints(onlineTrend)"
                      fill="none"
                      stroke="#166534"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      opacity="0.6"
                    />
                  </svg>
                </div>
              </div>
            </div>

            <!-- Storage Used Card -->
            <div class="card-base rounded-2xl p-6 hover:shadow-xl transition-all duration-400 group relative overflow-hidden screen-stat-card">
              <div class="relative z-10">
                <div class="flex items-start justify-between mb-4">
                  <div class="flex-1">
                    <p class="text-sm font-medium text-muted mb-1">Storage Used</p>
                    <p class="text-3xl font-bold text-primary mb-2">
                      {{ storageUsedFormatted }}
                    </p>
                    <!-- Glass-morphic Progress Bar -->
                    <div class="w-full h-3 bg-card rounded-full overflow-hidden backdrop-blur-sm" style="background: rgba(0, 0, 0, 0.05);">
                      <div
                        class="h-full rounded-full transition-all duration-1000 ease-out glass-progress-bar"
                        :style="{ width: `${storagePercentage}%` }"
                      ></div>
                    </div>
                    <p class="text-xs text-muted mt-1">{{ storageUsageText }}</p>
                  </div>
                  <div class="w-12 h-12 rounded-xl bg-card flex items-center justify-center transition-colors ml-4">
                    <ServerIcon class="w-6 h-6 text-accent-color" style="color: var(--accent-color);" />
                  </div>
                </div>
              </div>
            </div>

            <!-- Active Templates Card -->
            <div class="card-base rounded-2xl p-6 hover:shadow-xl transition-all duration-400 group relative overflow-hidden screen-stat-card">
              <div class="relative z-10">
                <div class="flex items-start justify-between mb-4">
                  <div>
                    <p class="text-sm font-medium text-muted mb-1">Active Templates</p>
                    <p class="text-3xl font-bold text-primary">
                      {{ stats.activeTemplates }}
                    </p>
                    <p class="text-xs text-muted mt-1">{{ activeTemplatesRatioText }}</p>
                  </div>
                  <div class="w-12 h-12 rounded-xl bg-card flex items-center justify-center transition-colors">
                    <DocumentTextIcon class="w-6 h-6 text-accent-color" style="color: var(--accent-color);" />
                  </div>
                </div>
                <!-- Sparkline Chart -->
                <div class="h-12 mt-4">
                  <svg class="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <polyline
                      :points="generateSparklinePoints(templateTrend)"
                      fill="none"
                      stroke="var(--accent-color)"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      opacity="0.6"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- System Health & Connectivity -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Screen Status Chart -->
            <div class="card-base rounded-2xl p-6">
              <h3 class="text-lg font-semibold text-primary mb-4">Screen Status</h3>
              <div class="flex flex-col sm:flex-row sm:items-center gap-6">
                <div class="flex-1 space-y-2 order-2 sm:order-1 min-w-0">
                  <div class="flex items-center justify-between text-sm gap-3">
                    <div class="flex items-center gap-2 min-w-0">
                      <div class="w-3 h-3 rounded-full shrink-0 bg-forest-green" />
                      <span class="text-muted">Online Screens</span>
                    </div>
                    <span class="text-primary font-semibold tabular-nums shrink-0">{{ stats.onlineScreens }}</span>
                  </div>
                  <div class="flex items-center justify-between text-sm gap-3">
                    <div class="flex items-center gap-2 min-w-0">
                      <div class="w-3 h-3 rounded-full shrink-0 bg-dusty-red" />
                      <span class="text-muted">Offline Screens</span>
                    </div>
                    <span class="text-primary font-semibold tabular-nums shrink-0">{{ stats.offlineScreens }}</span>
                  </div>
                </div>
                <div class="relative w-44 h-44 sm:w-48 sm:h-48 shrink-0 mx-auto sm:mx-0 order-1 sm:order-2">
                  <Chart
                    v-if="chartData"
                    :data="chartData"
                    :options="chartOptions"
                    type="doughnut"
                    container-class="w-full h-full min-h-0"
                  />
                  <!-- Fallback Circular Progress -->
                  <div v-else class="relative w-full h-full">
                    <svg class="transform -rotate-90 w-full h-full" viewBox="0 0 192 192">
                      <circle
                        cx="96"
                        cy="96"
                        r="88"
                        :stroke="chartUiTheme.track"
                        stroke-width="16"
                        fill="none"
                      />
                      <circle
                        cx="96"
                        cy="96"
                        r="88"
                        :stroke-dasharray="circumference"
                        :stroke-dashoffset="circumference - (onlinePercentage / 100) * circumference"
                        :stroke="chartUiTheme.online"
                        stroke-width="16"
                        fill="none"
                        stroke-linecap="round"
                        class="transition-all duration-500"
                      />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <p class="text-3xl sm:text-4xl font-bold text-primary">{{ onlinePercentage }}%</p>
                      <p class="text-sm text-muted mt-1">Online</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Recent Activities Card -->
            <div class="card-base rounded-2xl p-6 flex flex-col recent-activities-card">
              <div class="flex items-center justify-between mb-6 flex-shrink-0">
                <h3 class="text-lg font-semibold text-primary">Recent Activities</h3>
                <button
                  @click="refreshActivities"
                  class="text-sm text-accent-color hover:opacity-80 transition-all duration-400"
                  style="color: var(--accent-color);"
                  :disabled="loading"
                >
                  {{ loading ? 'Loading...' : 'Refresh' }}
                </button>
              </div>
              <div class="space-y-4 flex-1 overflow-y-auto custom-scrollbar min-h-0 pr-1">
                <div v-if="activities.length === 0 && !loading" class="text-center py-8 text-muted">
                  No recent activities
                </div>
                <div
                  v-for="activity in activities"
                  :key="activity.id"
                  class="flex items-start space-x-3 p-3 bg-surface-inset rounded-xl border border-border-color/60 hover:border-border-color transition-all duration-400"
                >
                  <div class="flex-shrink-0 mt-1">
                    <div
                      :class="[
                        'w-2 h-2 rounded-full',
                        activity.type === 'template' ? 'activity-dot-template' : '',
                        activity.type === 'screen' ? 'activity-dot-screen' : '',
                        activity.type === 'command' ? 'activity-dot-command' : '',
                        activity.type === 'content' ? 'activity-dot-content' : '',
                        activity.type === 'alert' ? 'activity-dot-alert' : '',
                        activity.type === 'update' ? 'activity-dot-update' : '',
                      ]"
                    ></div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm text-primary">{{ activity.message }}</p>
                    <p class="text-xs text-muted mt-1">{{ formatTime(activity.timestamp) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions Grid -->
          <div class="card-base rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-primary mb-6">Quick Actions</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <router-link
                to="/templates?action=create"
                class="group flex items-center space-x-4 p-4 bg-surface-inset hover:bg-surface-inset border border-border-color hover:border-accent-color/50 rounded-xl transition-all duration-400"
                style="--accent-color: var(--accent-color);"
              >
                <div class="w-12 h-12 rounded-xl bg-surface-inset group-hover:bg-surface-inset flex items-center justify-center transition-colors border border-border-color/50">
                  <PlusIcon class="w-6 h-6 text-accent-color" style="color: var(--accent-color);" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-primary">Create New Template</p>
                  <p class="text-xs text-muted">Design a new display template</p>
                </div>
              </router-link>

              <router-link
                to="/screens/add"
                class="group flex items-center space-x-4 p-4 bg-surface-inset hover:bg-surface-inset border border-border-color hover:border-accent-color/50 rounded-xl transition-all duration-400"
                style="--accent-color: var(--accent-color);"
              >
                <div class="w-12 h-12 rounded-xl bg-surface-inset group-hover:bg-surface-inset flex items-center justify-center transition-colors border border-border-color/50">
                  <TvIcon class="w-6 h-6 text-accent-color" style="color: var(--accent-color);" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-primary">Pair New Screen</p>
                  <p class="text-xs text-muted">Register a new display screen</p>
                </div>
              </router-link>

              <button
                @click="showEmergencyAlert = true"
                class="group flex items-center space-x-4 p-4 bg-surface-inset hover:bg-surface-inset border border-border-color hover:border-dusty-red/50 rounded-xl transition-all duration-400 text-left w-full"
              >
                <div class="w-12 h-12 rounded-xl bg-surface-inset group-hover:bg-surface-inset flex items-center justify-center transition-colors border border-border-color/50">
                  <ExclamationTriangleIcon class="w-6 h-6 text-dusty-red" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-primary">Emergency Alert</p>
                  <p class="text-xs text-muted">Clear all screens</p>
                </div>
              </button>
            </div>
          </div>

          <!-- Recent Templates -->
          <div class="card-base rounded-2xl p-6">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-semibold text-primary">Recent Templates</h3>
              <router-link
                to="/templates"
                class="text-sm text-accent-color hover:opacity-80 transition-all duration-400"
                style="color: var(--accent-color);"
              >
                View All â†’
              </router-link>
            </div>
            <div v-if="recentTemplates.length === 0" class="text-center py-8 text-muted">
              No templates yet. Create your first template!
            </div>
            <div v-else class="flex space-x-4 overflow-x-auto pb-4 custom-scrollbar">
              <div
                v-for="template in recentTemplates"
                :key="template.id"
                class="flex-shrink-0 group cursor-pointer"
                @click="$router.push(`/templates/${template.id}`)"
              >
                <div class="w-64 card-base rounded-xl overflow-hidden hover:shadow-xl transition-all duration-400">
                  <!-- Template Preview (16:9 aspect ratio) -->
                  <div class="aspect-video bg-card flex items-center justify-center relative overflow-hidden">
                    <div class="relative z-10 text-center p-4">
                      <DocumentTextIcon class="w-12 h-12 text-accent-color mx-auto mb-2" style="color: var(--accent-color);" />
                      <p class="text-xs text-primary font-medium">{{ template.name }}</p>
                    </div>
                    <div class="absolute top-2 right-2">
                      <span
                        :class="[
                          'px-2 py-1 rounded text-xs font-medium',
                          template.is_active ? 'bg-forest-green/20 text-forest-green' : 'bg-card text-muted'
                        ]"
                      >
                        {{ template.is_active ? 'Active' : 'Draft' }}
                      </span>
                    </div>
                  </div>
                  <div class="p-4">
                    <p class="text-sm font-semibold text-primary mb-1">{{ template.name }}</p>
                    <p class="text-xs text-muted">{{ formatTime(template.updated_at || template.created_at) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>

    <!-- Emergency Alert Modal -->
    <div
      v-if="showEmergencyAlert"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 dark:bg-black/50 backdrop-blur-sm"
      @click.self="showEmergencyAlert = false"
    >
      <div class="card-base backdrop-blur-md rounded-2xl p-6 max-w-md w-full">
        <div class="flex items-center space-x-3 mb-4">
          <div class="w-12 h-12 rounded-xl bg-dusty-red/20 flex items-center justify-center">
            <ExclamationTriangleIcon class="w-6 h-6 text-dusty-red" />
          </div>
          <h3 class="text-lg font-semibold text-primary">Emergency Alert</h3>
        </div>
        <p class="text-sm text-muted mb-6">
          This will clear all screens and display an emergency message. Are you sure you want to proceed?
        </p>
        <div class="flex space-x-3">
          <button
            @click="showEmergencyAlert = false"
            class="btn-outline flex-1 px-4 py-2 rounded-xl"
          >
            Cancel
          </button>
          <button
            @click="handleEmergencyAlert"
            class="btn-danger flex-1 px-4 py-2 rounded-xl"
          >
            Clear All Screens
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useTemplatesStore } from '@/stores/templates'
import { useScreensStore } from '@/stores/screens'
import { useNotification } from '@/composables/useNotification'
import { contentsAPI } from '@/services/api'
import AppLayout from '@/components/layout/AppLayout.vue'
import OnboardingChecklist from '@/components/onboarding/OnboardingChecklist.vue'
import Chart from '@/components/common/Chart.vue'
import { useThemeStore } from '@/stores/theme'
import {
  buildDoughnutTooltipOptions,
  colorWithAlpha,
  getChartUiTheme,
} from '@/utils/chartTheme'
import {
  TvIcon,
  ServerIcon,
  DocumentTextIcon,
  PlusIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

const dashboardStore = useDashboardStore()
const templatesStore = useTemplatesStore()
const screensStore = useScreensStore()
const notify = useNotification()
const themeStore = useThemeStore()

// State
const loading = ref(true)
const showEmergencyAlert = ref(false)
const currentTime = ref('')
const currentDate = ref('')
const starsContainer = ref(null)

// Stats
const stats = computed(() => ({
  totalScreens: (dashboardStore.stats?.online_screens || 0) + (dashboardStore.stats?.offline_screens || 0),
  onlineScreens: dashboardStore.stats?.online_screens || 0,
  offlineScreens: dashboardStore.stats?.offline_screens || 0,
  activeTemplates: templatesStore.activeTemplates?.length || 0,
}))
const totalTemplates = computed(() => templatesStore.templates?.length || 0)
const activeTemplatesRatioText = computed(() => {
  if (!totalTemplates.value) return '0% active'
  const ratio = Math.round((stats.value.activeTemplates / totalTemplates.value) * 100)
  return `${ratio}% active (${stats.value.activeTemplates}/${totalTemplates.value})`
})

// Storage stats
const storageUsedBytes = ref(0)
const storageLimitBytes = ref(5 * 1024 * 1024 * 1024)
const storageUsedMB = computed(() => Math.round(storageUsedBytes.value / (1024 * 1024)))
const storageLimitMB = computed(() => Math.round(storageLimitBytes.value / (1024 * 1024)))
const storagePercentage = computed(() => {
  if (storageLimitBytes.value === 0) return 0
  return Math.min(100, Math.round((storageUsedBytes.value / storageLimitBytes.value) * 100))
})
const storageUsedFormatted = computed(() => `${storagePercentage.value}%`)
const storageUsageText = computed(() => `${formatBytes(storageUsedBytes.value)} / ${formatBytes(storageLimitBytes.value)}`)

// Activities
const activities = computed(() => {
  return dashboardStore.activities || []
})

// Recent Templates
const recentTemplates = computed(() => {
  return templatesStore.templates
    .sort((a, b) => {
      const dateA = new Date(a.updated_at || a.created_at)
      const dateB = new Date(b.updated_at || b.created_at)
      return dateB - dateA
    })
    .slice(0, 4)
})

const chartUiTheme = computed(() => {
  void themeStore.theme
  return getChartUiTheme()
})

const chartData = computed(() => {
  if (stats.value.totalScreens === 0) return null

  const theme = chartUiTheme.value
  return {
    labels: ['Online', 'Offline'],
    datasets: [{
      data: [stats.value.onlineScreens, stats.value.offlineScreens],
      backgroundColor: [
        colorWithAlpha(theme.online, 0.9),
        colorWithAlpha(theme.offline, 0.85),
      ],
      borderColor: [theme.online, theme.offline],
      hoverBackgroundColor: [theme.online, theme.offline],
      hoverBorderColor: [theme.online, theme.offline],
      borderWidth: 2,
    }],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: buildDoughnutTooltipOptions(chartUiTheme.value),
  },
  cutout: '70%',
}))

// Computed properties
const onlinePercentage = computed(() => {
  if (stats.value.totalScreens === 0) return 0
  return Math.round((stats.value.onlineScreens / stats.value.totalScreens) * 100)
})

const circumference = computed(() => {
  return 2 * Math.PI * 88 // radius = 88
})

const hasData = computed(() => {
  return stats.value.totalScreens > 0 || activities.value.length > 0 || recentTemplates.value.length > 0
})

const MAX_TREND_POINTS = 12
const trendHistory = ref({
  totalScreens: [],
  onlineScreens: [],
  activeTemplates: [],
  storagePercentage: [],
})

const pushTrendPoint = () => {
  const nextPoint = {
    totalScreens: Math.max(0, Number(stats.value.totalScreens || 0)),
    onlineScreens: Math.max(0, Number(stats.value.onlineScreens || 0)),
    activeTemplates: Math.max(0, Number(stats.value.activeTemplates || 0)),
    storagePercentage: Math.max(0, Math.min(100, Number(storagePercentage.value || 0))),
  }

  Object.keys(nextPoint).forEach((key) => {
    const series = trendHistory.value[key]
    if (!Array.isArray(series)) return
    series.push(nextPoint[key])
    if (series.length > MAX_TREND_POINTS) {
      series.shift()
    }
  })
}

const screenTrend = computed(() => {
  const history = trendHistory.value.totalScreens
  if (history.length >= 2) return history
  const base = Math.max(0, Number(stats.value.totalScreens || 0))
  return [base, base, base]
})

const onlineTrend = computed(() => {
  const history = trendHistory.value.onlineScreens
  if (history.length >= 2) return history
  const base = Math.max(0, Number(stats.value.onlineScreens || 0))
  return [base, base, base]
})

const templateTrend = computed(() => {
  const history = trendHistory.value.activeTemplates
  if (history.length >= 2) return history
  const base = Math.max(0, Number(stats.value.activeTemplates || 0))
  return [base, base, base]
})

// Helper functions
const generateSparklinePoints = (data) => {
  if (!data || data.length === 0) return ''
  const safeData = data.map((value) => Math.max(0, Number(value || 0)))
  const max = Math.max(...safeData)
  const min = Math.min(...safeData)
  const range = max - min || 1
  const width = 100
  const height = 40
  const stepX = safeData.length > 1 ? width / (safeData.length - 1) : width
  
  return safeData.map((value, index) => {
    const x = index * stepX
    const y = height - ((value - min) / range) * height
    return `${x},${y}`
  }).join(' ')
}

const formatTime = (date) => {
  if (!date) return ''
  const now = new Date()
  const diff = now - new Date(date)
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 MB'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(2)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(2)} MB`
}

const getActivityColor = (type) => {
  const colors = {
    template: 'var(--accent-color)',
    screen: '#166534', // Forest Green
    command: 'var(--accent-color)',
    content: 'var(--accent-color)',
    alert: '#B91C1C', // Dusty Red
    update: '#D97706', // Muted Amber
  }
  return colors[type] || 'var(--text-muted)'
}

const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  currentDate.value = now.toLocaleDateString('en-US', { 
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const refreshActivities = async () => {
  await dashboardStore.fetchActivities()
}

const fetchStorageStats = async () => {
  try {
    const response = await contentsAPI.storageStats()
    const data = response.data || {}
    storageUsedBytes.value = Number(data.used_bytes || 0)
    storageLimitBytes.value = Number(data.limit_bytes || (5 * 1024 * 1024 * 1024))
  } catch (error) {
    if (error?.response?.data?.message?.includes('screen_id') ||
        error?.response?.data?.error?.includes('screen_id')) {
      console.debug('Suppressed screen_id error in storage stats')
      return
    }
    console.warn('Could not fetch storage stats:', error)
  }
}

const handleEmergencyAlert = async () => {
  // TODO: Implement emergency alert API call
  try {
    // This would call an API to send emergency command to all screens
    notify.success('Emergency alert sent to all screens')
    showEmergencyAlert.value = false
  } catch (error) {
    notify.error('Failed to send emergency alert')
  }
}

// Create animated stars
const createStars = () => {
  if (!starsContainer.value) return
  
  const starsCount = 50
  for (let i = 0; i < starsCount; i++) {
    const star = document.createElement('div')
    star.className = 'absolute rounded-full bg-white'
    star.style.width = `${Math.random() * 2 + 1}px`
    star.style.height = star.style.width
    star.style.left = `${Math.random() * 100}%`
    star.style.top = `${Math.random() * 100}%`
    star.style.opacity = Math.random() * 0.5 + 0.2
    star.style.animation = `starry-twinkle ${Math.random() * 3 + 2}s ease-in-out infinite`
    star.style.animationDelay = `${Math.random() * 2}s`
    starsContainer.value.appendChild(star)
  }
}

let clockInterval = null
let refreshInterval = null

onMounted(async () => {
  // Initialize clock
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
  
  // Create animated stars
  createStars()
  
  // Fetch initial data - only use global/aggregated endpoints
  loading.value = true
  try {
    // Fetch data in parallel, but handle errors gracefully
    const results = await Promise.allSettled([
      dashboardStore.fetchStats(),
      dashboardStore.fetchActivities(),
      templatesStore.fetchTemplates(),
      screensStore.fetchScreens(), // This is a global list, not screen-specific
    ])
    
    // Check for errors and log them (but don't fail the whole dashboard)
    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        const error = result.reason
        // Suppress screen_id errors - these are expected if no screen is selected
        if (error?.response?.data?.message?.includes('screen_id') || 
            error?.response?.data?.error?.includes('screen_id')) {
          console.debug('Suppressed screen_id error (expected for global dashboard):', error.message)
          return
        }
        console.warn(`Dashboard data fetch ${index} failed:`, error)
      }
    })
    
    await fetchStorageStats()
    pushTrendPoint()
  } catch (error) {
    // Suppress screen_id errors
    if (error?.response?.data?.message?.includes('screen_id') || 
        error?.response?.data?.error?.includes('screen_id')) {
      console.debug('Suppressed screen_id error (expected for global dashboard)')
    } else {
      console.error('Error loading dashboard data:', error)
      notify.error('Failed to load dashboard data')
    }
  } finally {
    loading.value = false
  }
  
  // Refresh stats every 30 seconds - only global endpoints
  refreshInterval = setInterval(async () => {
    try {
      await Promise.allSettled([
        dashboardStore.fetchStats(),
        dashboardStore.fetchActivities(),
        fetchStorageStats(),
      ])
      pushTrendPoint()
    } catch (error) {
      // Suppress screen_id errors and network errors
      if (error?.response?.data?.message?.includes('screen_id') || 
          error?.response?.data?.error?.includes('screen_id')) {
        console.debug('Suppressed screen_id error during refresh')
        return
      }
      if (error.message && !error.message.includes('Broken pipe')) {
        console.error('Error refreshing dashboard data:', error)
      }
    }
  }, 30000)
})

onUnmounted(() => {
  if (clockInterval) {
    clearInterval(clockInterval)
  }
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: var(--border-color);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--text-muted);
  border-radius: 3px;
  opacity: 0.5;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  opacity: 0.7;
}

.dark .custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Screen Stat Cards - Floating Shadow Effect */
.screen-stat-card {
  background: var(--surface-3);
  box-shadow: 
    0 8px 18px -8px rgba(15, 23, 42, 0.2),
    0 3px 8px -4px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(30, 41, 59, 0.08);
}

/* Keep Recent Activities card height stable; scroll list inside */
.recent-activities-card {
  height: 28rem;
  min-height: 28rem;
  max-height: 28rem;
  overflow: hidden;
}

.dark .screen-stat-card {
  background: rgba(255, 255, 255, 0.05);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.screen-stat-card:hover {
  box-shadow: 
    0 14px 24px -10px rgba(15, 23, 42, 0.25),
    0 8px 14px -8px rgba(15, 23, 42, 0.18),
    0 0 0 1px rgba(37, 99, 235, 0.15);
  transform: translateY(-3px);
}

.dark .screen-stat-card:hover {
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
  transform: none;
}

/* Online Card - Outer Glow Effect */
.screen-stat-card-online {
  position: relative;
}

.screen-stat-card-online::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 1rem;
  background: linear-gradient(135deg, rgba(22, 101, 52, 0.1), rgba(22, 101, 52, 0.05));
  opacity: 0;
  transition: opacity 0.4s ease;
  z-index: -1;
}

.screen-stat-card-online:hover::before {
  opacity: 1;
}

.dark .screen-stat-card-online::before {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
}

/* Glass-morphic Progress Bar */
.glass-progress-bar {
  background: linear-gradient(90deg, rgba(9, 132, 227, 0.6), rgba(9, 132, 227, 0.4));
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 2px 4px rgba(9, 132, 227, 0.2);
}

.dark .glass-progress-bar {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.8), rgba(99, 102, 241, 0.8));
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

/* Activity Dots - Light Mode Colors */
.activity-dot-template {
  background: var(--accent-color);
}

.activity-dot-screen {
  background: #166534; /* Forest Green */
}

.activity-dot-command {
  background: var(--accent-color);
}

.activity-dot-content {
  background: var(--accent-color);
}

.activity-dot-alert {
  background: #B91C1C; /* Dusty Red */
}

.activity-dot-update {
  background: #D97706; /* Muted Amber */
}

.dark .activity-dot-template {
  background: rgb(99, 102, 241);
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.5);
}

.dark .activity-dot-screen {
  background: rgb(16, 185, 129);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.dark .activity-dot-command {
  background: rgb(59, 130, 246);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

.dark .activity-dot-content {
  background: rgb(168, 85, 247);
  box-shadow: 0 0 8px rgba(168, 85, 247, 0.5);
}

.dark .activity-dot-alert {
  background: rgb(239, 68, 68);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
}

.dark .activity-dot-update {
  background: rgb(234, 179, 8);
  box-shadow: 0 0 8px rgba(234, 179, 8, 0.5);
}
</style>
