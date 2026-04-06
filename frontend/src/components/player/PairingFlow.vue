<template>
  <div class="activation-page">
    <!-- Deep Space Background -->
    <div class="starfield-background"></div>
    
    <!-- Radial Glow Effect -->
    <div class="radial-glow"></div>

    <!-- Main Content Container -->
    <div class="activation-container">
      <!-- Loading State -->
      <div v-if="status === 'loading'" class="loading-state">
        <div class="loading-spinner"></div>
        <h2 class="loading-text">Generating Activation Code...</h2>
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <!-- Pairing State — single viewport, no scroll (TV / browser chrome) -->
      <div v-else-if="status === 'pairing'" class="pairing-state">
        <div class="pairing-body">
          <!-- Title -->
          <h1 class="main-title">Activate Your Screen</h1>

          <!-- 6-Digit Code Display -->
          <div class="code-section">
            <div class="code-label">Activation Code</div>
            <div class="code-container">
              <div
                v-for="(digit, index) in codeDigits"
                :key="index"
                class="digit-card"
              >
                <span class="digit-text">{{ digit }}</span>
              </div>
            </div>
          </div>

          <!-- QR Code Section -->
          <div class="qr-section">
            <div class="qr-wrapper">
              <div class="qr-ring"></div>
              <div class="qr-inner">
                <img
                  v-if="qrCodeDataUrl"
                  :src="qrCodeDataUrl"
                  alt="QR Code"
                  class="qr-image"
                />
                <div v-else class="qr-placeholder">
                  <div class="qr-spinner"></div>
                </div>
              </div>
            </div>
            <p class="qr-label">Scan with your device</p>
          </div>

          <!-- Step-by-Step Instructions -->
          <div class="instructions-section">
            <div class="instruction-card">
              <div class="instruction-icon step-1">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                </svg>
              </div>
              <div class="instruction-content">
                <h3 class="instruction-title">Step 1</h3>
                <p class="instruction-text">Scan the QR code or visit our URL</p>
              </div>
            </div>

            <div class="instruction-card">
              <div class="instruction-icon step-2">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="instruction-content">
                <h3 class="instruction-title">Step 2</h3>
                <p class="instruction-text">Enter the code shown above</p>
              </div>
            </div>

            <div class="instruction-card">
              <div class="instruction-icon step-3">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="instruction-content">
                <h3 class="instruction-title">Step 3</h3>
                <p class="instruction-text">Enjoy your smart screen!</p>
              </div>
            </div>
          </div>
        </div>

        <div class="pairing-footer">
          <!-- Countdown Timer -->
          <div class="countdown-section">
            <div class="countdown-card">
              <span class="countdown-label">Code expires in</span>
              <span class="countdown-value">{{ formattedCountdown }}</span>
            </div>
          </div>

          <!-- Status Indicator -->
          <div class="status-section">
            <div class="status-indicator">
              <span class="status-text">Waiting for connection</span>
              <div class="status-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>

          <!-- Status Message -->
          <div v-if="statusMessage" class="status-message" :class="statusMessageClass">
            {{ statusMessage }}
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="status === 'error'" class="error-state">
        <div class="error-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 class="error-title">Connection Error</h2>
        <p class="error-message">{{ errorMessage }}</p>
        <button @click="retry" class="retry-button">Retry</button>
      </div>

      <!-- Success State with Welcome Animation -->
      <div v-else-if="status === 'success'" class="success-state">
        <div class="welcome-animation">
          <div class="welcome-circle"></div>
          <div class="welcome-check">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 class="welcome-title">Welcome!</h2>
          <p class="welcome-subtitle">Screen activated successfully</p>
          <p class="welcome-message">Redirecting to your content...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { pairingAPI } from '@/services/api'
import * as QRCode from 'qrcode'

const emit = defineEmits(['paired'])

// State
const status = ref('loading') // loading | pairing | error | success
const pairingCode = ref('')
const pairingToken = ref('')
const qrCodeDataUrl = ref('')
const expiresAt = ref(null)
const countdown = ref(300) // 5 minutes in seconds
const statusMessage = ref('')
const statusMessageType = ref('') // 'info' | 'error' | 'success'
const errorMessage = ref('')

// Computed
const codeDigits = computed(() => {
  return pairingCode.value.padStart(6, '0').split('')
})

const formattedCountdown = computed(() => {
  const minutes = Math.floor(countdown.value / 60)
  const seconds = countdown.value % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})

const statusMessageClass = computed(() => {
  if (statusMessageType.value === 'error') {
    return 'status-message-error'
  } else if (statusMessageType.value === 'success') {
    return 'status-message-success'
  } else {
    return 'status-message-info'
  }
})

// Timers
let countdownTimer = null
let statusPollTimer = null
let themeObserver = null

function clearPairingTimers() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (statusPollTimer) {
    clearInterval(statusPollTimer)
    statusPollTimer = null
  }
}

/** Expired / invalid session: show message on this page only, then refresh session (no global toast). */
function handleSessionExpired() {
  clearPairingTimers()
  statusMessage.value =
    'This activation code has expired. Generating a new code…'
  statusMessageType.value = 'error'
  setTimeout(() => {
    generatePairingSession()
  }, 2000)
}

function isExpiredStatusError(error) {
  const data = error?.response?.data
  if (!data) return false
  if (data.status === 'expired') return true
  const msg = String(data.message || data.error || '').toLowerCase()
  return msg.includes('expired') || msg.includes('invalid')
}

// Methods
async function generatePairingSession() {
  try {
    status.value = 'loading'
    errorMessage.value = ''
    
    const response = await pairingAPI.generate()
    
    if (response.data.status === 'success') {
      const session = response.data.pairing_session
      pairingCode.value = session.pairing_code
      pairingToken.value = session.pairing_token
      expiresAt.value = new Date(session.expires_at)
      
      // Calculate initial countdown
      const now = new Date()
      const expires = new Date(session.expires_at)
      countdown.value = Math.max(0, Math.floor((expires - now) / 1000))
      
      // Generate QR code
      await generateQRCode(session.qr_code_url)
      
      // Watch for theme changes and regenerate QR code
      watchThemeChanges()
      
      // Start countdown
      startCountdown()
      
      // Start polling for pairing status
      startStatusPolling()
      
      status.value = 'pairing'
    } else {
      throw new Error('Failed to generate pairing session')
    }
  } catch (error) {
    console.error('Pairing generation error:', error)
    status.value = 'error'
    errorMessage.value = error.response?.data?.error || error.message || 'Failed to generate pairing code'
  }
}

async function generateQRCode(url) {
  try {
    // Detect dark mode
    const isDark = document.documentElement.classList.contains('dark')
    
    const dataUrl = await QRCode.toDataURL(url, {
      width: 400,
      margin: 2,
      color: {
        dark: '#FFFFFF',
        light: '#000000'
      },
      errorCorrectionLevel: 'M'
    })
    qrCodeDataUrl.value = dataUrl
  } catch (error) {
    console.error('QR code generation error:', error)
    statusMessage.value = 'Failed to generate QR code'
    statusMessageType.value = 'error'
  }
}

function startCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      handleSessionExpired()
    }
  }, 1000)
}

function startStatusPolling() {
  if (statusPollTimer) {
    clearInterval(statusPollTimer)
  }
  
  // Poll every 2 seconds
  statusPollTimer = setInterval(async () => {
    if (!pairingToken.value) return
    
    try {
      const response = await pairingAPI.status({ pairing_token: pairingToken.value })
      
      if (response.data.status === 'paired') {
        clearPairingTimers()

        status.value = 'success'
        statusMessage.value = 'Screen paired successfully!'
        statusMessageType.value = 'success'

        const { screen_id, device_token } = response.data

        // Emit to parent (WebPlayer) after the welcome animation
        setTimeout(() => {
          emit('paired', { screenId: screen_id, deviceToken: device_token })
        }, 3000)
      } else if (response.data.status === 'expired') {
        handleSessionExpired()
      }
    } catch (error) {
      if (isExpiredStatusError(error)) {
        handleSessionExpired()
        return
      }
      console.error('Status polling error:', error)
    }
  }, 2000)
}

function retry() {
  generatePairingSession()
}

// Watch for theme changes and regenerate QR code
function watchThemeChanges() {
  if (themeObserver) {
    themeObserver.disconnect()
  }
  
  // Watch for class changes on html element
  themeObserver = new MutationObserver(() => {
    if (pairingToken.value && qrCodeDataUrl.value) {
      // Regenerate QR code with new theme colors
      const baseUrl = window.location.origin
      const qrUrl = `${baseUrl}/screens/add?token=${pairingToken.value}`
      generateQRCode(qrUrl)
    }
  })
  
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
}

onMounted(() => {
  generatePairingSession()
})

onUnmounted(() => {
  clearPairingTimers()
  if (themeObserver) {
    themeObserver.disconnect()
  }
})
</script>

<style scoped>
.activation-page {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  overscroll-behavior: none;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 25%, #0f172a 50%, #1e293b 75%, #0a0e27 100%);
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
  width: 100%;
  max-width: 100%;
  height: 100%;
  max-height: 100%;
  min-height: 0;
  box-sizing: border-box;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* Starfield Background */
.starfield-background {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
  overflow: hidden;
  z-index: 0;
}

.starfield-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(2px 2px at 20% 30%, white, transparent),
    radial-gradient(2px 2px at 60% 70%, white, transparent),
    radial-gradient(1px 1px at 50% 50%, white, transparent),
    radial-gradient(1px 1px at 80% 10%, white, transparent),
    radial-gradient(2px 2px at 30% 80%, white, transparent),
    radial-gradient(1px 1px at 90% 40%, white, transparent);
  background-repeat: repeat;
  background-size: 200% 200%;
  animation: starfield 20s linear infinite;
  opacity: 0.6;
}

@keyframes starfield {
  from { transform: translateY(0); }
  to { transform: translateY(-2000px); }
}

/* Radial Glow */
.radial-glow {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80vw;
  height: 80vh;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%);
  pointer-events: none;
  z-index: 1;
  animation: pulseGlow 4s ease-in-out infinite;
}

@keyframes pulseGlow {
  0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.8; transform: translate(-50%, -50%) scale(1.1); }
}

/* Main container — fills one viewport; pairing UI scales inside (no page scroll) */
.activation-container {
  position: relative;
  z-index: 10;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  padding:
    max(clamp(0.35rem, 1.5vmin, 1rem), env(safe-area-inset-top))
    max(clamp(0.5rem, 2vw, 1.25rem), env(safe-area-inset-right))
    max(clamp(0.35rem, 1.5vmin, 1rem), env(safe-area-inset-bottom))
    max(clamp(0.5rem, 2vw, 1.25rem), env(safe-area-inset-left));
  color: white;
}

/* Loading State */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 0;
}

.loading-spinner {
  width: 80px;
  height: 80px;
  border: 4px solid rgba(6, 182, 212, 0.2);
  border-top-color: #06b6d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 2rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: clamp(1.25rem, 6vmin, 2.5rem);
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.loading-dots {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.loading-dots span {
  width: 12px;
  height: 12px;
  background: #06b6d4;
  border-radius: 50%;
  animation: dotPulse 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* Main Title */
.main-title {
  font-size: clamp(1.1rem, 3.2vmin, 2.25rem);
  font-weight: 800;
  text-align: center;
  margin: 0;
  line-height: 1.15;
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
  letter-spacing: -0.02em;
  flex-shrink: 0;
}

.pairing-state {
  width: 100%;
  max-width: 1200px;
  height: 100%;
  min-height: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

.pairing-body {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: clamp(0.15rem, 1vmin, 0.65rem);
  overflow: hidden;
}

.pairing-footer {
  flex: 0 0 auto;
  width: 100%;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: clamp(0.35rem, 2vmin, 1.25rem);
  row-gap: clamp(0.25rem, 1vmin, 0.5rem);
}

/* Code Section */
.code-section {
  margin: 0;
  text-align: center;
  flex-shrink: 1;
  min-height: 0;
}

.code-label {
  font-size: clamp(0.6rem, 1.5vmin, 0.95rem);
  font-weight: 600;
  margin: 0 0 clamp(0.2rem, 1vmin, 0.5rem);
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.code-container {
  display: flex;
  gap: clamp(0.35rem, 2vmin, 1rem);
  justify-content: center;
  flex-wrap: wrap;
  width: 100%;
  max-width: 100%;
  padding: 0 env(safe-area-inset-left) 0 env(safe-area-inset-right);
  box-sizing: border-box;
}

.digit-card {
  width: clamp(32px, 7vmin, 72px);
  height: clamp(40px, 9vmin, 90px);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 2px solid rgba(6, 182, 212, 0.3);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  animation: digitBreath 3s ease-in-out infinite;
  box-shadow: 0 8px 32px rgba(6, 182, 212, 0.2), 
              0 0 0 1px rgba(6, 182, 212, 0.1),
              inset 0 0 20px rgba(6, 182, 212, 0.1);
}

.digit-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(139, 92, 246, 0.1));
  opacity: 0;
  transition: opacity 0.3s;
}

.digit-card:hover::before {
  opacity: 1;
}

.digit-card:nth-child(1) { animation-delay: 0s; }
.digit-card:nth-child(2) { animation-delay: 0.2s; }
.digit-card:nth-child(3) { animation-delay: 0.4s; }
.digit-card:nth-child(4) { animation-delay: 0.6s; }
.digit-card:nth-child(5) { animation-delay: 0.8s; }
.digit-card:nth-child(6) { animation-delay: 1s; }

@keyframes digitBreath {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 8px 32px rgba(6, 182, 212, 0.2), 
                0 0 0 1px rgba(6, 182, 212, 0.1),
                inset 0 0 20px rgba(6, 182, 212, 0.1);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 12px 48px rgba(6, 182, 212, 0.4), 
                0 0 0 2px rgba(6, 182, 212, 0.3),
                inset 0 0 30px rgba(6, 182, 212, 0.2);
  }
}

.digit-text {
  font-size: clamp(1.1rem, 5vmin, 2.75rem);
  font-weight: 700;
  font-family: 'Courier New', 'Monaco', monospace;
  color: #06b6d4;
  text-shadow: 
    0 0 20px rgba(6, 182, 212, 0.8),
    0 0 40px rgba(6, 182, 212, 0.5),
    0 0 60px rgba(139, 92, 246, 0.3);
  position: relative;
  z-index: 1;
}

/* QR Code Section */
.qr-section {
  margin: 0;
  text-align: center;
  flex-shrink: 3;
  min-height: 0;
}

.qr-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: clamp(0.2rem, 1vmin, 0.5rem);
}

.qr-ring {
  position: absolute;
  inset: -20px;
  border: 3px solid transparent;
  border-top-color: #06b6d4;
  border-right-color: #8b5cf6;
  border-radius: 50%;
  animation: spinRing 3s linear infinite;
  z-index: 0;
}

@keyframes spinRing {
  to { transform: rotate(360deg); }
}

.qr-inner {
  position: relative;
  z-index: 1;
  background: white;
  padding: clamp(0.35rem, 1.2vmin, 0.65rem);
  border-radius: clamp(10px, 2vmin, 20px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.qr-image {
  /* Fit inside short viewports — cap by vh so footer + steps stay visible */
  width: min(28vh, 42vmin, 88vw, 260px);
  max-width: 100%;
  height: auto;
  aspect-ratio: 1;
  display: block;
  border-radius: 12px;
}

.qr-placeholder {
  width: min(28vh, 42vmin, 88vw, 260px);
  height: min(28vh, 42vmin, 88vw, 260px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(6, 182, 212, 0.2);
  border-top-color: #06b6d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.qr-label {
  font-size: clamp(0.75rem, 2vmin, 1.1rem);
  margin: 0;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

/* Instructions Section */
.instructions-section {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(0.35rem, 1.5vmin, 1rem);
  margin: 0;
  max-width: 1200px;
  width: 100%;
  flex-shrink: 1;
  min-height: 0;
}

.instruction-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: clamp(10px, 2vmin, 20px);
  padding: clamp(0.4rem, 1.5vmin, 1rem);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
  min-height: 0;
}

.instruction-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(6, 182, 212, 0.2);
}

.instruction-icon {
  width: clamp(36px, 7vmin, 56px);
  height: clamp(36px, 7vmin, 56px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: clamp(0.25rem, 1vmin, 0.65rem);
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid;
}

.instruction-icon svg {
  width: clamp(18px, 3.5vmin, 28px);
  height: clamp(18px, 3.5vmin, 28px);
}

.instruction-icon.step-1 {
  border-color: #06b6d4;
  color: #06b6d4;
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
}

.instruction-icon.step-2 {
  border-color: #8b5cf6;
  color: #8b5cf6;
  box-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
}

.instruction-icon.step-3 {
  border-color: #10b981;
  color: #10b981;
  box-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
}

.instruction-title {
  font-size: clamp(0.85rem, 2.2vmin, 1.2rem);
  font-weight: 700;
  margin: 0 0 0.2rem;
  color: white;
}

.instruction-text {
  font-size: clamp(0.65rem, 1.65vmin, 0.95rem);
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.35;
  margin: 0;
}

/* Countdown Section */
.countdown-section {
  margin: 0;
}

.countdown-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 12px;
  padding: clamp(0.35rem, 1.2vmin, 0.65rem) clamp(0.75rem, 2.5vmin, 1.25rem);
  display: inline-flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: clamp(0.35rem, 1.5vmin, 0.75rem);
}

.countdown-label {
  font-size: clamp(0.65rem, 1.6vmin, 0.9rem);
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.countdown-value {
  font-size: clamp(1rem, 3vmin, 1.5rem);
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #06b6d4;
  text-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
}

/* Status Section */
.status-section {
  margin: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: clamp(0.35rem, 1.5vmin, 0.75rem);
  justify-content: center;
}

.status-text {
  font-size: clamp(0.75rem, 2vmin, 1.05rem);
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.status-dots {
  display: flex;
  gap: 0.5rem;
}

.status-dots span {
  width: clamp(6px, 1.2vmin, 10px);
  height: clamp(6px, 1.2vmin, 10px);
  background: #06b6d4;
  border-radius: 50%;
  animation: dotPulse 1.4s ease-in-out infinite;
}

.status-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.status-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

/* Status Message */
.status-message {
  flex: 1 1 100%;
  padding: clamp(0.35rem, 1vmin, 0.65rem) clamp(0.5rem, 2vmin, 1rem);
  border-radius: 10px;
  font-size: clamp(0.7rem, 1.8vmin, 0.95rem);
  text-align: center;
  max-width: min(600px, 100%);
  margin: 0;
}

.status-message-info {
  background: rgba(6, 182, 212, 0.2);
  border: 1px solid rgba(6, 182, 212, 0.5);
  color: #06b6d4;
}

.status-message-success {
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid rgba(16, 185, 129, 0.5);
  color: #10b981;
}

.status-message-error {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  color: #ef4444;
}

/* Error State */
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 0;
  overflow: auto;
}

.error-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto 2rem;
  color: #ef4444;
  animation: pulse 2s ease-in-out infinite;
}

.error-icon svg {
  width: 100%;
  height: 100%;
}

.error-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: white;
}

.error-message {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 2rem;
}

.retry-button {
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  color: white;
  border: none;
  padding: 1rem 3rem;
  font-size: 1.25rem;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  box-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);
}

.retry-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 40px rgba(6, 182, 212, 0.5);
}

/* Success State with Welcome Animation */
.success-state {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  overflow: hidden;
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
  box-sizing: border-box;
}

.welcome-animation {
  text-align: center;
  position: relative;
}

.welcome-circle {
  width: 200px;
  height: 200px;
  border: 4px solid #10b981;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: circleExpand 1s ease-out forwards;
}

@keyframes circleExpand {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    width: 400px;
    height: 400px;
    opacity: 0;
  }
}

.welcome-check {
  width: 120px;
  height: 120px;
  background: #10b981;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2rem;
  color: white;
  animation: checkPop 0.6s ease-out 0.3s both;
  box-shadow: 0 20px 60px rgba(16, 185, 129, 0.5);
}

.welcome-check svg {
  width: 60px;
  height: 60px;
}

@keyframes checkPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.welcome-title {
  font-size: 4rem;
  font-weight: 800;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: fadeInUp 0.6s ease-out 0.5s both;
}

.welcome-subtitle {
  font-size: 2rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 1rem;
  animation: fadeInUp 0.6s ease-out 0.7s both;
}

.welcome-message {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.6);
  animation: fadeInUp 0.6s ease-out 0.9s both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Large displays — stay within viewport (no oversized blocks that force scroll) */
@media (min-width: 1920px) {
  .qr-image {
    width: min(32vh, 44vmin, 320px);
  }
}

/* Narrow phones — keep 3 columns but tighter; avoid a tall single column */
@media (max-width: 768px) {
  .instructions-section {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: clamp(0.2rem, 1vmin, 0.5rem);
  }

  .instruction-card {
    padding: clamp(0.3rem, 1vmin, 0.65rem);
  }

  .code-container {
    gap: clamp(0.2rem, 1vmin, 0.45rem);
  }
}

/* Very short viewports — shrink QR further */
@media (max-height: 520px) {
  .qr-image,
  .qr-placeholder {
    width: min(22vh, 38vw, 200px);
    height: auto;
  }

  .qr-placeholder {
    height: min(22vh, 38vw, 200px);
  }

  .main-title {
    font-size: clamp(1rem, 2.8vmin, 1.35rem);
  }
}
</style>
