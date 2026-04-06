<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
    <header class="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
        <div>
          <p class="text-cyan-300 text-xs font-semibold tracking-[0.16em] uppercase">PixelCast Data Center</p>
          <h1 class="text-xl sm:text-2xl font-bold">TV Catalog</h1>
        </div>
        <router-link to="/" class="btn-outline px-4 py-2 rounded-lg text-sm">Back to Home</router-link>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <section
        class="rounded-2xl border border-cyan-400/25 bg-gradient-to-br from-cyan-950/40 to-slate-900/90 p-5 sm:p-6 shadow-lg shadow-cyan-950/20"
      >
        <h2 class="text-lg font-semibold text-white mb-2">Download — Android TV app</h2>
        <p class="text-sm text-white/75 mb-3 max-w-3xl">
          One official APK for TVs and boxes that run <strong class="text-white/90">Android TV</strong> or
          <strong class="text-white/90">Google TV</strong>. The same build works across manufacturers—no per-brand
          packages.
        </p>
        <p class="text-xs text-white/55 mb-4 max-w-3xl">
          Displays on <strong class="text-white/70">Tizen</strong>, <strong class="text-white/70">webOS</strong>, or
          other non-Android platforms do not use this APK. Use the
          <router-link to="/player/connect" class="text-cyan-300 underline hover:text-cyan-200">Web Player</router-link>
          in the device browser instead.
        </p>
        <div v-if="apkDownloadUrl" class="flex flex-wrap gap-3 items-center">
          <a
            :href="apkDownloadUrl"
            class="btn-primary px-4 py-2.5 rounded-lg text-sm font-medium inline-flex items-center gap-2"
            rel="noopener noreferrer"
          >
            Download APK
          </a>
          <span class="text-xs text-white/50">Install, then pair the screen from your admin.</span>
        </div>
        <p v-else class="text-sm text-amber-100/90 leading-relaxed">
          Configure a download URL via server env
          <code class="mx-0.5 rounded bg-black/35 px-1.5 py-0.5 font-mono text-xs">ANDROID_TV_APK_URL</code>
          (recommended) or build-time
          <code class="mx-0.5 rounded bg-black/35 px-1.5 py-0.5 font-mono text-xs">VITE_ANDROID_TV_APK_URL</code>
          to show the button here.
        </p>
      </section>
      <section
        v-if="usingFallback"
        class="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100"
      >
        Catalog is shown from bundled data because the server database is not ready or migrations are pending.
        On the server run:
        <code class="mx-1 rounded bg-black/30 px-1.5 py-0.5 font-mono text-xs">python manage.py migrate</code>
        then
        <code class="mx-1 rounded bg-black/30 px-1.5 py-0.5 font-mono text-xs">python manage.py seed_tv_catalog</code>
      </section>
      <section class="card-base rounded-2xl p-5 sm:p-6 bg-white/5 border border-white/10">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            v-model.trim="search"
            class="input-base md:col-span-2 px-3 py-2 rounded-lg bg-slate-900/70"
            type="text"
            placeholder="Search by brand, model, series, platform..."
          />
          <select v-model="platform" class="select-base px-3 py-2 rounded-lg bg-slate-900/70">
            <option value="">All Platforms</option>
            <option v-for="item in platformOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
          <select v-model="operationTime" class="select-base px-3 py-2 rounded-lg bg-slate-900/70">
            <option value="">All Operation Time</option>
            <option value="16_7">16/7</option>
            <option value="18_7">18/7</option>
            <option value="24_7">24/7</option>
          </select>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            v-for="brightness in brightnessOptions"
            :key="brightness.value"
            type="button"
            class="px-3 py-1.5 rounded-full text-xs border transition"
            :class="brightnessClass === brightness.value ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200' : 'bg-transparent border-white/20 text-white/70 hover:border-white/40'"
            @click="toggleBrightness(brightness.value)"
          >
            {{ brightness.label }}
          </button>
          <button type="button" class="px-3 py-1.5 rounded-full text-xs border border-white/20 text-white/70 hover:border-white/40" @click="resetFilters">
            Reset
          </button>
        </div>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <article
          v-for="brand in filteredBrands"
          :key="brand.id"
          class="rounded-2xl border border-white/10 bg-white/5 overflow-hidden backdrop-blur"
        >
          <div class="p-5 border-b border-white/10">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="inline-flex items-center rounded-md border border-cyan-400/30 bg-cyan-400/10 px-2 py-1 text-[11px] font-semibold tracking-[0.1em] uppercase text-cyan-200">
                  {{ brand.logo_text || brand.name }}
                </div>
                <h2 class="mt-3 text-lg font-semibold">{{ brand.name }}</h2>
                <p class="mt-1 text-sm text-white/70">{{ brand.description || 'Professional display lineup for signage deployments.' }}</p>
              </div>
              <span class="text-xs text-white/60">{{ brand.models.length }} models</span>
            </div>
          </div>

          <div class="p-4 space-y-3">
            <div
              v-for="model in brand.models"
              :key="model.id"
              class="rounded-xl border p-3 transition"
              :class="selectedModelId === model.id ? 'border-cyan-400/60 bg-cyan-400/10' : 'border-white/10 bg-slate-900/40'"
            >
              <div class="flex items-start justify-between gap-2">
                <div>
                  <h3 class="font-semibold text-sm">{{ model.name }}</h3>
                  <p class="text-xs text-white/60">{{ model.series || '-' }} • {{ model.platform_display }}</p>
                </div>
                <span class="text-[11px] rounded-full px-2 py-0.5 bg-white/10 text-white/70">{{ model.operation_time_display }}</span>
              </div>

              <div class="mt-2 flex flex-wrap gap-1.5">
                <span class="text-[11px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-200">{{ model.brightness_class_display }}</span>
                <span v-for="port in model.control_ports || []" :key="`${model.id}-${port}`" class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-200">
                  {{ port }}
                </span>
              </div>

              <p v-if="model.notes" class="mt-2 text-xs text-white/70 leading-relaxed">{{ model.notes }}</p>

              <div class="mt-3 flex items-center gap-2">
                <button
                  type="button"
                  class="btn-primary px-3 py-1.5 rounded-lg text-xs"
                  @click="selectedModelId = model.id"
                >
                  {{ selectedModelId === model.id ? 'Selected' : 'Select TV' }}
                </button>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section v-if="!loading && !error && filteredBrands.length === 0" class="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-white/70">
        No result found for the current filters.
      </section>
      <section v-if="loading" class="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-white/70">Loading catalog...</section>
      <section v-if="error && !usingFallback" class="rounded-2xl border border-red-400/30 bg-red-500/10 p-6 text-red-200">
        <p>{{ error }}</p>
        <button type="button" class="mt-3 btn-outline px-4 py-2 rounded-lg text-sm" @click="fetchCatalog">Retry</button>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watchEffect } from 'vue'
import { tvCatalogAPI, publicAPI } from '@/services/api'
import { normalizeApiError } from '@/utils/apiError'
import { getTvCatalogFallback } from '@/data/tvCatalogFallback'

const loading = ref(false)
const error = ref('')
const brands = ref([])
const usingFallback = ref(false)

const search = ref('')
const platform = ref('')
const operationTime = ref('')
const brightnessClass = ref('')
const selectedModelId = ref(localStorage.getItem('selected_tv_model_id') || '')
const apkDownloadUrl = ref('')

const platformOptions = [
  { value: 'android_tv', label: 'Android TV' },
  { value: 'google_tv', label: 'Google TV' },
  { value: 'tizen', label: 'Tizen' },
  { value: 'webos', label: 'webOS' },
  { value: 'android_soc', label: 'Android SoC' },
  { value: 'other', label: 'Other' },
]

const brightnessOptions = [
  { value: 'indoor', label: 'Indoor 300-350 nits' },
  { value: 'high_bright', label: 'High Bright 500-700 nits' },
  { value: 'window', label: 'Window Facing 2500+ nits' },
]

const normalizedSearch = computed(() => search.value.toLowerCase())

const filteredBrands = computed(() => {
  return brands.value
    .map((brand) => {
      const filteredModels = (brand.models || []).filter((model) => {
        const searchBlob = [
          brand.name,
          model.name,
          model.series,
          model.model_code,
          model.platform_display,
          model.notes,
        ].join(' ').toLowerCase()

        if (normalizedSearch.value && !searchBlob.includes(normalizedSearch.value)) return false
        if (platform.value && model.platform !== platform.value) return false
        if (operationTime.value && model.operation_time !== operationTime.value) return false
        if (brightnessClass.value && model.brightness_class !== brightnessClass.value) return false
        return true
      })

      return { ...brand, models: filteredModels }
    })
    .filter((brand) => brand.models.length > 0)
})

function toggleBrightness(value) {
  brightnessClass.value = brightnessClass.value === value ? '' : value
}

function resetFilters() {
  search.value = ''
  platform.value = ''
  operationTime.value = ''
  brightnessClass.value = ''
}

function isMissingTvTableError(err) {
  const msg = String(
    err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      err?.apiError?.userMessage ||
      ''
  ).toLowerCase()
  return msg.includes('core_tv_brand') || msg.includes('does not exist')
}

async function loadApkDownloadUrl() {
  try {
    const response = await publicAPI.downloads()
    const url = response?.data?.android_tv_apk_url
    if (url && String(url).trim()) {
      apkDownloadUrl.value = String(url).trim()
      return
    }
  } catch {
    /* optional: server offline or not configured */
  }
  const viteUrl = import.meta.env.VITE_ANDROID_TV_APK_URL
  if (viteUrl) apkDownloadUrl.value = String(viteUrl).trim()
}

async function fetchCatalog() {
  loading.value = true
  error.value = ''
  usingFallback.value = false
  try {
    const response = await tvCatalogAPI.list()
    const results = response?.data?.results || response?.data || []
    brands.value = Array.isArray(results) ? results : []
  } catch (err) {
    const parsed = err.apiError || normalizeApiError(err)
    const msg = parsed.userMessage || err?.message || 'Failed to load TV catalog.'
    if (isMissingTvTableError(err) || parsed.status >= 500 || !err?.response) {
      brands.value = getTvCatalogFallback()
      usingFallback.value = true
      error.value = ''
    } else {
      error.value = msg
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadApkDownloadUrl()
  fetchCatalog()
})

watchEffect(() => {
  if (selectedModelId.value) {
    localStorage.setItem('selected_tv_model_id', selectedModelId.value)
  } else {
    localStorage.removeItem('selected_tv_model_id')
  }
})
</script>
