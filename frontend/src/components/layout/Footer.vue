<template>
  <footer class="system-status-bar">
    <div class="status-bar-container">
      <!-- Left: System Status -->
      <div class="status-section status-left">
        <span class="status-dot status-operational"></span>
        <span class="status-text">System Ready</span>
      </div>

      <!-- Center: Copyright & Version -->
      <div class="status-section status-center">
        <span class="status-meta">
          © {{ new Date().getFullYear() }} PixelCast Signage
        </span>
        <span class="status-separator">·</span>
        <span class="status-meta status-version">
          v{{ appVersion }}
        </span>
      </div>

      <!-- Right: Clock & Latency -->
      <div class="status-section status-right">
        <div class="status-time">
          <ClockIcon class="w-3 h-3" />
          <span class="time-text">{{ currentTime }}</span>
        </div>
        <div class="status-latency">
          <span class="latency-label">Latency</span>
          <span class="latency-value">{{ serverLatency }}ms</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ClockIcon } from '@heroicons/vue/24/outline'

// App version
const appVersion = ref(typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '2.1.0')

// Current time
const currentTime = ref('')
const timeInterval = ref(null)

// Server latency (mock - replace with real API call)
const serverLatency = ref(24)
const latencyInterval = ref(null)

// Update time
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

// Check server latency
const checkLatency = async () => {
  try {
    const start = performance.now()
    await fetch('/api/health/', {
      method: 'GET',
      signal: AbortSignal.timeout(2000)
    })
    const end = performance.now()
    serverLatency.value = Math.round(end - start)
  } catch (error) {
    serverLatency.value = 0
  }
}

onMounted(() => {
  updateTime()
  timeInterval.value = setInterval(updateTime, 1000)
  
  checkLatency()
  latencyInterval.value = setInterval(checkLatency, 30000) // Check every 30 seconds
})

onUnmounted(() => {
  if (timeInterval.value) {
    clearInterval(timeInterval.value)
  }
  if (latencyInterval.value) {
    clearInterval(latencyInterval.value)
  }
})
</script>

<style scoped>
/* Light theme (default): match Antler surfaces — dark mode overrides below */
.system-status-bar {
  position: relative;
  width: 100%;
  z-index: 20;
  background: var(--card-bg);
  backdrop-filter: var(--card-bg-backdrop);
  -webkit-backdrop-filter: var(--card-bg-backdrop);
  border-top: 1px solid var(--border-color);
  box-shadow: 0 -1px 0 rgba(15, 23, 42, 0.04);
  padding: 0.375rem 1.5rem;
  height: 30px;
  max-height: 30px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

html.dark .system-status-bar {
  background: rgba(10, 10, 26, 0.4);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: none;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.status-bar-container {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.status-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-left {
  flex: 0 0 auto;
}

.status-center {
  flex: 1;
  justify-content: center;
}

.status-right {
  flex: 0 0 auto;
  gap: 1rem;
}

/* System Status Indicator */
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}

.status-text {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
  letter-spacing: 0.05em;
}

html.dark .status-text {
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
}

/* Copyright & Version */
.status-meta {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 400;
  letter-spacing: 0.03em;
}

html.dark .status-meta {
  color: rgba(255, 255, 255, 0.35);
}

.status-version {
  font-family: 'Courier New', 'Consolas', monospace;
  letter-spacing: 0.08em;
}

.status-separator {
  color: var(--text-muted);
  opacity: 0.45;
  font-size: 9px;
  user-select: none;
  margin: 0 0.25rem;
}

html.dark .status-separator {
  color: rgba(255, 255, 255, 0.15);
  opacity: 1;
}

/* Clock & Latency */
.status-time {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-muted);
}

html.dark .status-time {
  color: rgba(255, 255, 255, 0.5);
}

.status-time svg {
  color: var(--text-muted);
  width: 12px;
  height: 12px;
}

html.dark .status-time svg {
  color: rgba(255, 255, 255, 0.35);
}

.time-text {
  font-size: 10px;
  font-family: 'Courier New', 'Consolas', monospace;
  color: var(--text-main);
  font-weight: 500;
  letter-spacing: 0.05em;
}

html.dark .time-text {
  color: rgba(255, 255, 255, 0.6);
}

.status-latency {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.latency-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

html.dark .latency-label {
  color: rgba(255, 255, 255, 0.35);
}

.latency-value {
  font-size: 10px;
  font-family: 'Courier New', 'Consolas', monospace;
  color: var(--accent-color);
  font-weight: 600;
  letter-spacing: 0.05em;
}

html.dark .latency-value {
  color: #00d2ff;
  text-shadow: 0 0 6px rgba(0, 210, 255, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .system-status-bar {
    padding: 0.375rem 1rem;
    height: auto;
    min-height: 30px;
  }

  .status-bar-container {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .status-center {
    order: 3;
    width: 100%;
    justify-content: center;
    padding-top: 0.25rem;
    border-top: 1px solid var(--border-color);
  }

  html.dark .status-center {
    border-top-color: rgba(255, 255, 255, 0.03);
  }

  .status-right {
    gap: 0.75rem;
  }

  .status-text {
    font-size: 9px;
  }

  .status-meta {
    font-size: 9px;
  }

  .time-text {
    font-size: 9px;
  }

  .latency-value {
    font-size: 9px;
  }
}

@media (max-width: 640px) {
  .status-latency {
    display: none;
  }

  .status-time {
    gap: 0.25rem;
  }
}
</style>
