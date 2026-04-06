<template>
  <div v-if="shouldRender" class="weather-widget" :class="[`tone-${conditionTone}`, { night: isNight }]" :style="containerStyle">
    <div class="weather-glow"></div>

    <div class="weather-header">
      <div class="weather-location-wrap">
        <div class="weather-location">{{ locationLabel }}</div>
        <div class="weather-description" v-if="weatherDescription">{{ weatherDescription }}</div>
      </div>
      <div class="weather-updated" v-if="updatedLabel">Updated {{ updatedLabel }}</div>
    </div>

    <div v-if="hasWeatherData" class="weather-main">
      <div class="weather-icon-shell">
        <img v-if="iconUrl" :src="iconUrl" class="weather-icon" alt="Weather icon" />
      </div>
      <div class="weather-main-text">
        <div class="weather-temp">{{ currentTemp }}</div>
        <div class="weather-range">H/L {{ tempRange }}</div>
      </div>
    </div>

    <div v-else class="weather-unavailable">
      <div class="weather-unavailable-title">Weather temporarily unavailable</div>
      <div class="weather-unavailable-sub">Waiting for provider response...</div>
    </div>

    <div v-if="showExtended && hasWeatherData" class="weather-forecast">
      <div v-for="(item, idx) in forecastRows" :key="`${item.date || idx}`" class="forecast-item">
        <div class="forecast-day">{{ formatDay(item.date) }}</div>
        <img v-if="item.icon" :src="iconFor(item.icon)" class="forecast-icon" alt="Forecast icon" />
        <div class="forecast-range">{{ formatTemp(item.temp_min) }} / {{ formatTemp(item.temp_max) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  widget: {
    type: Object,
    required: true,
  },
})

const styleJson = computed(() => props.widget?.content_json || {})
const weatherData = computed(() => styleJson.value?.weatherData || null)
const weatherMeta = computed(() => styleJson.value?.weatherMeta || {})
const hasWeatherData = computed(() => Boolean(weatherData.value && weatherData.value.current))
const weatherDescription = computed(() => (weatherData.value?.current?.description || '').trim())

const units = computed(() => (String(styleJson.value?.units || 'celsius').toLowerCase() === 'fahrenheit' ? 'fahrenheit' : 'celsius'))
const unitSuffix = computed(() => (units.value === 'fahrenheit' ? 'F' : 'C'))
const hideAfterHours = computed(() => {
  const raw = Number(styleJson.value?.hideAfterHours)
  if (!Number.isFinite(raw) || raw <= 0) return 6
  return Math.min(24, Math.max(1, raw))
})

const updatedAt = computed(() => {
  const value = weatherData.value?.updated_at
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
})

const isStaleBeyondLimit = computed(() => {
  if (!updatedAt.value) return true
  const ageMs = Date.now() - updatedAt.value.getTime()
  return ageMs > hideAfterHours.value * 60 * 60 * 1000
})

const shouldRender = computed(() => {
  // Keep widget visible when configured, even if provider is temporarily unavailable.
  // This avoids the confusing "widget disappeared" state.
  if (!styleJson.value?.location) return false
  if (hasWeatherData.value) return !isStaleBeyondLimit.value
  return true
})

const containerStyle = computed(() => ({
  color: styleJson.value?.color || '#ffffff',
  background: dynamicBackground.value,
  border: '1px solid rgba(255,255,255,0.14)',
  boxShadow: isNight.value
    ? '0 12px 28px rgba(2, 6, 23, 0.55), inset 0 1px 0 rgba(255,255,255,0.07)'
    : '0 12px 28px rgba(30, 41, 59, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)',
}))

const showExtended = computed(() => String(styleJson.value?.layout || 'compact').toLowerCase() === 'extended')
const forecastRows = computed(() => {
  const rows = Array.isArray(weatherData.value?.forecast) ? weatherData.value.forecast : []
  const desired = Number(styleJson.value?.forecastDays) || 3
  return rows.slice(0, Math.min(5, Math.max(3, desired)))
})

const locationLabel = computed(() => weatherData.value?.location?.label || styleJson.value?.location || 'Weather')

const formatTemp = (value) => {
  const n = Number(value)
  if (!Number.isFinite(n)) return '--'
  return `${Math.round(n)}${unitSuffix.value}`
}

const currentTemp = computed(() => formatTemp(weatherData.value?.current?.temp))
const tempRange = computed(() => {
  const min = formatTemp(weatherData.value?.current?.temp_min)
  const max = formatTemp(weatherData.value?.current?.temp_max)
  return `${min} / ${max}`
})

const iconFor = (code) => {
  if (!code) return ''
  return `https://openweathermap.org/img/wn/${code}@2x.png`
}

const iconUrl = computed(() => iconFor(weatherData.value?.current?.icon))
const iconCode = computed(() => String(weatherData.value?.current?.icon || '').toLowerCase())
const iconGroup = computed(() => iconCode.value.slice(0, 2))
const isNight = computed(() => iconCode.value.endsWith('n'))

const conditionTone = computed(() => {
  if (iconGroup.value === '01') return 'sunny'
  if (['02', '03', '04'].includes(iconGroup.value)) return 'cloudy'
  if (['09', '10'].includes(iconGroup.value)) return 'rainy'
  if (iconGroup.value === '11') return 'storm'
  if (iconGroup.value === '13') return 'snow'
  if (iconGroup.value === '50') return 'mist'
  return 'default'
})

const dynamicBackground = computed(() => {
  if (styleJson.value?.transparentBackground === true) return 'transparent'
  if (styleJson.value?.backgroundColor) return styleJson.value.backgroundColor
  const night = isNight.value
  switch (conditionTone.value) {
    case 'sunny':
      return night
        ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%)'
        : 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 55%, #1d4ed8 100%)'
    case 'cloudy':
      return night
        ? 'linear-gradient(135deg, #111827 0%, #1f2937 55%, #374151 100%)'
        : 'linear-gradient(135deg, #64748b 0%, #475569 55%, #334155 100%)'
    case 'rainy':
      return 'linear-gradient(135deg, #0f172a 0%, #1d4ed8 50%, #0f172a 100%)'
    case 'storm':
      return 'linear-gradient(135deg, #111827 0%, #1e1b4b 45%, #312e81 100%)'
    case 'snow':
      return night
        ? 'linear-gradient(135deg, #1f2937 0%, #334155 50%, #475569 100%)'
        : 'linear-gradient(135deg, #bae6fd 0%, #93c5fd 50%, #60a5fa 100%)'
    case 'mist':
      return 'linear-gradient(135deg, #475569 0%, #64748b 50%, #475569 100%)'
    default:
      return night
        ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%)'
        : 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 55%, #0ea5e9 100%)'
  }
})

const formatDay = (dateStr) => {
  if (!dateStr) return ''
  const parsed = new Date(dateStr)
  if (Number.isNaN(parsed.getTime())) return dateStr
  return parsed.toLocaleDateString(undefined, { weekday: 'short' })
}

const updatedLabel = computed(() => {
  if (!updatedAt.value) return ''
  return updatedAt.value.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
})
</script>

<style scoped>
.weather-widget {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  box-sizing: border-box;
  overflow: hidden;
  border-radius: 14px;
  backdrop-filter: blur(3px);
  position: relative;
}

.weather-glow {
  position: absolute;
  right: -18%;
  top: -28%;
  width: 52%;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 70%);
  pointer-events: none;
}

.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  opacity: 0.95;
  position: relative;
  z-index: 1;
}

.weather-location-wrap {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.weather-location {
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35);
}

.weather-description {
  font-size: 11px;
  opacity: 0.86;
  text-transform: capitalize;
}

.weather-updated {
  font-size: 11px;
  opacity: 0.8;
  white-space: nowrap;
}

.weather-main {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.weather-icon-shell {
  width: 58px;
  height: 58px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.weather-icon {
  width: 52px;
  height: 52px;
  animation: iconFloat 3.6s ease-in-out infinite;
}

.weather-main-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.weather-temp {
  font-size: clamp(24px, 4vw, 48px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  text-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
}

.weather-range {
  font-size: clamp(11px, 1.25vw, 14px);
  opacity: 0.85;
  margin-top: 2px;
}

.weather-unavailable {
  font-size: 12px;
  opacity: 0.85;
  position: relative;
  z-index: 1;
}

.weather-unavailable-title {
  font-weight: 600;
}

.weather-unavailable-sub {
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.8;
}

.weather-forecast {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(72px, 1fr));
  gap: 8px;
  position: relative;
  z-index: 1;
}

.forecast-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 11px;
  border-radius: 10px;
  padding: 6px 4px;
  background: rgba(15, 23, 42, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.forecast-day {
  opacity: 0.85;
  font-weight: 600;
}

.forecast-icon {
  width: 30px;
  height: 30px;
}

.forecast-range {
  font-size: 10px;
  opacity: 0.9;
  margin-top: 2px;
}

.weather-widget.night .weather-glow {
  background: radial-gradient(circle, rgba(148, 163, 184, 0.18) 0%, rgba(255, 255, 255, 0) 70%);
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-3px); }
}
</style>
