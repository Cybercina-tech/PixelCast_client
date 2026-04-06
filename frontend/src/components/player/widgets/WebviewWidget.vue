<template>
  <div class="webview-widget">
    <iframe
      v-if="safeUrl"
      :src="safeUrl"
      class="webview-frame"
      sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-modals allow-downloads"
      referrerpolicy="no-referrer"
      loading="lazy"
    />
    <div v-else class="webview-error">
      <p>Webview URL is invalid.</p>
      <p class="error-hint">Use a full URL like https://example.com</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  widget: {
    type: Object,
    required: true
  }
})

const rawUrl = computed(() => {
  const firstContent = props.widget?.contents?.[0]
  return (
    firstContent?.secure_url ||
    firstContent?.file_url ||
    props.widget?.content_url ||
    props.widget?.content_json?.url ||
    props.widget?.content ||
    ''
  )
})

function normalizeWebviewUrl(value) {
  const input = String(value || '').trim()
  if (!input) return null
  const withProtocol = /^https?:\/\//i.test(input) ? input : `https://${input}`
  const parsed = new URL(withProtocol)
  if (!['http:', 'https:'].includes(parsed.protocol)) return null
  return parsed.toString()
}

const safeUrl = computed(() => {
  if (!rawUrl.value) return null
  try {
    return normalizeWebviewUrl(rawUrl.value)
  } catch {
    return null
  }
})
</script>

<style scoped>
.webview-widget {
  width: 100%;
  height: 100%;
  background: #111827;
}

.webview-frame {
  width: 100%;
  height: 100%;
  border: 0;
}

.webview-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  flex-direction: column;
  gap: 6px;
  text-align: center;
  padding: 12px;
}

.error-hint {
  opacity: 0.75;
  font-size: 12px;
}
</style>
