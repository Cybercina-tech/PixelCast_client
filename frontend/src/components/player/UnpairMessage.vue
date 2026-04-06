<template>
  <div class="unpair-screen">
    <div class="unpair-message">
      <div class="unpair-icon">
        <svg
          class="w-16 h-16 text-red-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h2 class="unpair-title">Device Unpaired</h2>
      <p class="unpair-detail">This device has been unpaired from your account.</p>
      <p class="unpair-detail">Connection has been disconnected.</p>
      <p class="unpair-countdown">Redirecting to pairing page in {{ countdown }}s...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['return-to-pairing'])
const countdown = ref(30)

let countdownInterval = null

onMounted(() => {
  countdownInterval = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownInterval)
      emit('return-to-pairing')
    }
  }, 1000)
})

onUnmounted(() => {
  if (countdownInterval) clearInterval(countdownInterval)
})
</script>

<style scoped>
.unpair-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #000000;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.unpair-message {
  text-align: center;
  color: #ffffff;
  padding: 2rem;
  max-width: 600px;
}

.unpair-icon {
  margin: 0 auto 2rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.unpair-title {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
  color: #ef4444;
}

.unpair-detail {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: #e5e7eb;
}

.unpair-countdown {
  font-size: 1rem;
  margin-top: 2rem;
  color: #9ca3af;
  font-weight: 500;
}

@media (max-width: 640px) {
  .unpair-title {
    font-size: 2rem;
  }
  
  .unpair-detail {
    font-size: 1rem;
  }
}
</style>

