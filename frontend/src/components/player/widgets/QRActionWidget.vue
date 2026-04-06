<template>
  <div class="qr-action-widget" :style="containerStyle">
    <div v-if="ctaText" class="qr-cta">{{ ctaText }}</div>
    <div class="qr-shell">
      <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR Action Code" class="qr-image" />
      <div v-else class="qr-loading">Generating QR...</div>
      <div v-if="logoUrl" class="qr-logo-shell">
        <img :src="logoUrl" alt="Brand logo" class="qr-logo" />
      </div>
    </div>
    <div v-if="displayUrl" class="qr-url">{{ displayUrl }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch, ref } from 'vue'
import * as QRCode from 'qrcode'
import { resolveWidgetBackgroundColor } from '@/utils/widgetBackground'

const props = defineProps({
  widget: {
    type: Object,
    required: true,
  },
})

const qrDataUrl = ref('')
const styleJson = computed(() => props.widget?.content_json || {})
const ctaText = computed(() => styleJson.value?.ctaText || 'Scan to continue')
const logoUrl = computed(() => styleJson.value?.logoUrl || '')
const redirectPath = computed(() => styleJson.value?.redirectPath || styleJson.value?.shortUrl || '')
const displayUrl = computed(() => styleJson.value?.displayUrl || redirectPath.value || '')
const quietZone = computed(() => {
  const raw = Number(styleJson.value?.quietZone)
  if (!Number.isFinite(raw)) return 4
  return Math.max(4, Math.min(12, Math.round(raw)))
})

const qrTargetUrl = computed(() => {
  if (redirectPath.value && redirectPath.value.startsWith('http')) return redirectPath.value
  const base = window.location.origin
  if (redirectPath.value) return `${base}${redirectPath.value.startsWith('/') ? '' : '/'}${redirectPath.value}`
  return styleJson.value?.defaultUrl || 'https://example.com'
})

const containerStyle = computed(() => ({
  background: resolveWidgetBackgroundColor(styleJson.value, '#ffffff'),
  color: styleJson.value?.foregroundColor || '#000000',
}))

const generateQr = async () => {
  try {
    const lightColor = styleJson.value?.transparentBackground
      ? '#00000000'
      : (styleJson.value?.backgroundColor || '#ffffff')
    const dataUrl = await QRCode.toDataURL(qrTargetUrl.value, {
      width: 512,
      margin: quietZone.value,
      errorCorrectionLevel: styleJson.value?.errorCorrectionLevel || 'H',
      color: {
        dark: styleJson.value?.foregroundColor || '#000000',
        light: lightColor,
      },
    })
    qrDataUrl.value = dataUrl
  } catch (error) {
    console.error('[QRActionWidget] QR generation failed', error)
    qrDataUrl.value = ''
  }
}

watch(() => ({ ...styleJson.value, target: qrTargetUrl.value }), () => {
  generateQr()
}, { deep: true })

onMounted(() => {
  generateQr()
})
</script>

<style scoped>
.qr-action-widget {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px;
  box-sizing: border-box;
  gap: 8px;
}

.qr-cta {
  font-size: clamp(12px, 1.5vw, 28px);
  font-weight: 700;
  text-align: center;
}

.qr-shell {
  position: relative;
  width: min(100%, 86%);
  aspect-ratio: 1 / 1;
  display: grid;
  place-items: center;
}

.qr-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  image-rendering: crisp-edges;
}

.qr-loading {
  font-size: 12px;
  opacity: 0.75;
}

.qr-logo-shell {
  position: absolute;
  width: 22%;
  height: 22%;
  background: #ffffff;
  border-radius: 10px;
  display: grid;
  place-items: center;
  padding: 4px;
  box-sizing: border-box;
}

.qr-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.qr-url {
  font-size: 10px;
  opacity: 0.8;
  text-align: center;
  word-break: break-all;
}
</style>
