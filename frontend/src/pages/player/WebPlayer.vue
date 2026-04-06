<template>
  <div
    ref="playerContainer"
    class="web-player"
    :style="containerStyle"
  >
    <!-- Pairing flow (embedded — no redirect needed) -->
    <PairingFlow
      v-if="showPairing"
      @paired="handlePaired"
    />

    <!-- On-screen message overlay (display_message command) -->
    <div v-if="overlayVisible" class="message-overlay">
      <div class="message-box">
        <div class="message-text">{{ overlayMessage }}</div>
      </div>
    </div>

    <!-- Empty state when screen has no assigned content -->
    <div v-if="showNoTemplateState" class="no-template-screen">
      <div class="no-template-content">
        <div class="status-signal" aria-hidden="true">
          <span class="signal-pulse"></span>
        </div>
        <h2 class="no-template-title">No content assigned</h2>
        <p class="no-template-description">
          This screen is paired and online, but nothing is assigned to display yet.
        </p>
        <p class="no-template-hint">
          Assign a template or schedule from the dashboard to start playback.
        </p>
      </div>
    </div>

    <!-- Unpaired / revoked state -->
    <UnpairMessage v-if="!showPairing && status === 'unpaired'" @return-to-pairing="enterPairing" />

    <!-- Error state -->
    <div v-else-if="!showPairing && status === 'error'" class="error-screen">
      <div class="error-message">
        <p>Connection Error</p>
        <p class="error-detail">{{ errorMessage }}</p>
        <p class="retry-info">Retrying in {{ retryCountdown }}s...</p>
      </div>
    </div>

    <!-- Loading state -->
    <div v-else-if="!showPairing && status === 'loading'" class="loading-screen" />

    <!-- Template rendering -->
    <div
      v-else-if="!showPairing && status === 'success' && template"
      ref="templateContainer"
      class="template-container"
      :style="templateContainerStyle"
    >
      <!-- Logical canvas: template pixel space (e.g. 1920×1080), scaled to fit viewport (contain) -->
      <div class="template-scaler" :key="templateMountKey" :style="templateScalerStyle">
        <LayerRenderer
          v-for="layer in sortedLayers"
          :key="layer.id"
          :layer="layer"
          :template-width="template.width || 1920"
          :template-height="template.height || 1080"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useResponsiveScaling } from '@/composables/useResponsiveScaling'
import { buildPlaybackLayers } from '@/utils/templatePlaybackLayers'
import LayerRenderer from '@/components/player/LayerRenderer.vue'
import UnpairMessage from '@/components/player/UnpairMessage.vue'
import PairingFlow from '@/components/player/PairingFlow.vue'

const playerStore = usePlayerStore()
const route = useRoute()
const router = useRouter()
const playerContainer = ref(null)
const templateContainer = ref(null)

const showPairing = ref(false)
const routeScreenId = computed(() => {
  const raw = route.params.screenId
  return raw ? String(raw).trim() : null
})
const isConnectRoute = computed(() => route.name === 'player-connect')

const status = computed(() => playerStore.status)
const template = computed(() => playerStore.template)
const errorMessage = computed(() => playerStore.errorMessage)
const retryCountdown = computed(() => playerStore.retryCountdown)
const overlayVisible = computed(() => playerStore.overlayVisible)
const overlayMessage = computed(() => playerStore.overlayMessage)
/** Bumped on remote "restart" command to remount layers/widgets without reloading the page. */
const templateMountKey = computed(() => playerStore.templateMountKey)
const showNoTemplateState = ref(false)
let noTemplateTimer = null

function clearNoTemplateTimer() {
  if (noTemplateTimer) {
    clearTimeout(noTemplateTimer)
    noTemplateTimer = null
  }
}

// When status becomes 'unpaired' and we have no device identity, show pairing
watch(status, (s) => {
  if (s === 'unpaired' && !playerStore.hasDeviceIdentity(routeScreenId.value)) {
    showPairing.value = true
  }
})

watch(showPairing, (isPairing) => {
  if (!isPairing) return
  clearNoTemplateTimer()
  showNoTemplateState.value = false
})

watch([routeScreenId, isConnectRoute], async ([newScreenId, connectMode], [oldScreenId, oldConnectMode]) => {
  if (newScreenId === oldScreenId && connectMode === oldConnectMode) return
  playerStore.stopPolling()
  clearNoTemplateTimer()
  showNoTemplateState.value = false

  if (connectMode) {
    playerStore.setActiveScreen(null)
    showPairing.value = true
    return
  }

  if (!newScreenId) {
    await router.replace({ name: 'player-connect' })
    return
  }

  playerStore.setActiveScreen(newScreenId)
  if (!playerStore.hasDeviceIdentity(newScreenId)) {
    showPairing.value = true
    return
  }

  showPairing.value = false
  try {
    await playerStore.initialize(newScreenId, { allowFallback: false })
    if (playerStore.status !== 'unpaired') {
      playerStore.startPolling()
    }
  } catch (_) {
    showPairing.value = true
  }
})

watch(status, (newStatus) => {
  clearNoTemplateTimer()

  if (showPairing.value) {
    showNoTemplateState.value = false
    return
  }

  if (newStatus === 'no_template') {
    // Wait briefly after connection before showing empty-state UI.
    showNoTemplateState.value = false
    noTemplateTimer = setTimeout(() => {
      if (!showPairing.value && status.value === 'no_template') {
        showNoTemplateState.value = true
      }
      noTemplateTimer = null
    }, 3000)
    return
  }

  showNoTemplateState.value = false
})

function enterPairing() {
  playerStore.clearDeviceIdentity(routeScreenId.value)
  playerStore.stopPolling()
  showPairing.value = true
}

function handlePaired({ screenId, deviceToken }) {
  const expectedScreenId = routeScreenId.value
  if (expectedScreenId && screenId && expectedScreenId !== String(screenId)) {
    playerStore.status = 'unpaired'
    playerStore.errorMessage = 'Paired to a different screen. Please pair this TV with the screen from the current URL.'
    showPairing.value = true
    return
  }

  const targetScreenId = expectedScreenId || screenId
  if (!targetScreenId) {
    playerStore.status = 'error'
    playerStore.errorMessage = 'Pairing completed without a valid screen ID.'
    showPairing.value = true
    return
  }
  playerStore.saveDeviceIdentity(targetScreenId, deviceToken)
  showPairing.value = false

  if (isConnectRoute.value) {
    router.replace({ name: 'player-screen', params: { screenId: String(targetScreenId) } })
    return
  }

  // Re-initialize the player with the new identity
  playerStore.initialize(targetScreenId, { allowFallback: false }).then(() => {
    playerStore.startPolling()
  }).catch((err) => {
    console.error('[WebPlayer] Post-pairing init failed:', err)
  })
}

const sortedLayers = computed(() => buildPlaybackLayers(template.value))

const {
  viewportWidth,
  viewportHeight,
  scaleFactor,
  offsetX,
  offsetY,
  updateViewport,
  setupResizeListener,
  cleanupResizeListener,
} = useResponsiveScaling(template)

watch(
  () => template.value,
  () => {
    nextTick(() => updateViewport())
  }
)

/** Fill dynamic viewport (mobile browser chrome); pixel box kept via composable for template scaling only */
const containerStyle = computed(() => ({
  position: 'fixed',
  inset: 0,
  width: '100%',
  maxWidth: '100%',
  height: '100%',
  minHeight: '100dvh',
  overflow: 'hidden',
  backgroundColor: '#000000',
  boxSizing: 'border-box',
}))

const templateContainerStyle = computed(() => ({
  width: `${viewportWidth.value}px`,
  height: `${viewportHeight.value}px`,
  maxWidth: '100%',
  maxHeight: '100%',
  position: 'relative',
  visibility: 'visible',
  opacity: 1,
  overflow: 'hidden',
}))

const templateScalerStyle = computed(() => {
  const t = template.value
  if (!t) {
    return { display: 'none' }
  }
  const tw = Number(t.width) || 1920
  const th = Number(t.height) || 1080
  return {
    position: 'absolute',
    left: '0',
    top: '0',
    width: `${tw}px`,
    height: `${th}px`,
    transform: `translate(${offsetX.value}px, ${offsetY.value}px) scale(${scaleFactor.value})`,
    transformOrigin: '0 0',
    willChange: 'transform',
  }
})

let contextMenuHandler = null
let keydownHandler = null

const toggleFullscreen = async () => {
  const el = playerContainer.value
  if (!el) return
  try {
    if (!document.fullscreenElement) {
      await (el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen || el.msRequestFullscreen).call(el)
    } else {
      await (document.exitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen || document.msExitFullscreen).call(document)
    }
  } catch (_) { /* ignore */ }
}

onMounted(async () => {
  setupResizeListener()

  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'

  contextMenuHandler = (e) => e.preventDefault()
  document.addEventListener('contextmenu', contextMenuHandler)

  keydownHandler = (e) => {
    if (e.key === 'F12') return
    if (e.key === 'f' || e.key === 'F') { toggleFullscreen(); e.preventDefault(); return }
    if (e.ctrlKey || e.metaKey) return
    e.preventDefault()
  }
  document.addEventListener('keydown', keydownHandler, true)
  document.addEventListener('selectstart', (e) => e.preventDefault())
  document.addEventListener('dragstart', (e) => e.preventDefault())

  if (isConnectRoute.value) {
    playerStore.setActiveScreen(null)
    showPairing.value = true
    return
  }

  if (!routeScreenId.value) {
    await router.replace({ name: 'player-connect' })
    return
  }

  playerStore.setActiveScreen(routeScreenId.value)

  // Decide: pair or play
  if (!playerStore.hasDeviceIdentity(routeScreenId.value)) {
    showPairing.value = true
    return
  }

  try {
    await playerStore.initialize(routeScreenId.value, { allowFallback: false })

    if (playerStore.status === 'unpaired') {
      showPairing.value = true
      return
    }

    playerStore.startPolling()
  } catch (error) {
    if (
      error.code === 'SCREEN_NOT_PAIRED' ||
      error.code === 'DEVICE_NOT_PAIRED' ||
      error.code === 'DEVICE_AUTH_FAILED'
    ) {
      playerStore.clearDeviceIdentity(routeScreenId.value)
      showPairing.value = true
      return
    }
    playerStore.status = 'error'
    playerStore.errorMessage = error.message || 'Initialization failed'
  }
})

onUnmounted(() => {
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  if (contextMenuHandler) document.removeEventListener('contextmenu', contextMenuHandler)
  if (keydownHandler) document.removeEventListener('keydown', keydownHandler, true)
  clearNoTemplateTimer()
  cleanupResizeListener()
  playerStore.stopPolling()
})
</script>

<style scoped>
.web-player {
  margin: 0;
  padding: 0;
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 100%;
  height: 100%;
  min-height: 100dvh;
  min-height: -webkit-fill-available;
  overflow: hidden;
  box-sizing: border-box;
}

.no-template-screen,
.loading-screen {
  width: 100%;
  height: 100%;
  background-color: #000000;
}

.no-template-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f3f4f6;
  padding: 24px;
}

.no-template-content {
  max-width: 720px;
  text-align: center;
  background: rgba(17, 24, 39, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 28px 32px;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.35);
}

.status-signal {
  margin: 0 auto 14px;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #f59e0b;
  position: relative;
}

.signal-pulse {
  position: absolute;
  inset: -8px;
  border-radius: 999px;
  border: 2px solid rgba(245, 158, 11, 0.7);
  animation: pulseSignal 1.8s ease-out infinite;
}

.no-template-title {
  margin: 0;
  font-size: clamp(26px, 3vw, 40px);
  font-weight: 700;
  color: #ffffff;
}

.no-template-description {
  margin: 14px 0 0;
  font-size: clamp(14px, 1.5vw, 22px);
  color: #e5e7eb;
  line-height: 1.55;
}

.no-template-hint {
  margin: 10px 0 0;
  font-size: clamp(12px, 1.2vw, 18px);
  color: #9ca3af;
}

@keyframes pulseSignal {
  0% {
    transform: scale(0.65);
    opacity: 0.95;
  }
  100% {
    transform: scale(1.25);
    opacity: 0;
  }
}

.message-overlay {
  position: fixed;
  inset: 0;
  width: 100%;
  max-width: 100%;
  height: 100%;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  z-index: 99999;
  pointer-events: none;
}

.message-box {
  max-width: 70vw;
  padding: 18px 22px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  pointer-events: auto;
}

.message-text {
  font-size: 20px;
  color: #ffffff;
  text-align: center;
  line-height: 1.5;
  word-break: break-word;
}

.error-screen {
  width: 100%;
  height: 100%;
  background-color: #000000;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
}

.error-message {
  text-align: center;
  font-size: clamp(14px, 2vw, 24px);
}

.error-message p {
  margin: 10px 0;
}

.error-detail {
  font-size: clamp(12px, 1.5vw, 16px);
  color: #888888;
}

.retry-info {
  font-size: clamp(10px, 1.2vw, 14px);
  color: #666666;
}

.template-container {
  position: relative;
  overflow: visible;
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  contain: layout style;
}
</style>
