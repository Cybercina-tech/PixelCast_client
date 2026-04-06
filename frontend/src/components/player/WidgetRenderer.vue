<template>
  <div
    class="widget"
    :style="widgetStyle"
  >
    <ImageWidget
      v-if="widget.type === 'image'"
      :widget="widget"
    />
    <TextWidget
      v-else-if="widget.type === 'text'"
      :widget="widget"
    />
    <MarqueeWidget
      v-else-if="widget.type === 'marquee'"
      :widget="widget"
    />
    <WeatherWidget
      v-else-if="widget.type === 'weather'"
      :widget="widget"
    />
    <VideoWidget
      v-else-if="widget.type === 'video'"
      :widget="widget"
    />
    <AlbumWidget
      v-else-if="widget.type === 'album'"
      :widget="widget"
    />
    <ClockWidget
      v-else-if="widget.type === 'clock'"
      :widget="widget"
    />
    <DateWidget
      v-else-if="widget.type === 'date'"
      :widget="widget"
    />
    <WeekdayWidget
      v-else-if="widget.type === 'weekday'"
      :widget="widget"
    />
    <WebviewWidget
      v-else-if="widget.type === 'webview'"
      :widget="widget"
    />
    <ChartWidget
      v-else-if="widget.type === 'chart'"
      :widget="widget"
    />
    <QRActionWidget
      v-else-if="widget.type === 'qr_action'"
      :widget="widget"
    />
    <CountdownWidget
      v-else-if="widget.type === 'countdown'"
      :widget="widget"
    />
    <div
      v-else
      class="widget-error"
    >
      Unknown widget type: {{ widget.type }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import ImageWidget from './widgets/ImageWidget.vue'
import TextWidget from './widgets/TextWidget.vue'
import MarqueeWidget from './widgets/MarqueeWidget.vue'
import WeatherWidget from './widgets/WeatherWidget.vue'
import VideoWidget from './widgets/VideoWidget.vue'
import AlbumWidget from './widgets/AlbumWidget.vue'
import ClockWidget from './widgets/ClockWidget.vue'
import DateWidget from './widgets/DateWidget.vue'
import WeekdayWidget from './widgets/WeekdayWidget.vue'
import WebviewWidget from './widgets/WebviewWidget.vue'
import ChartWidget from './widgets/ChartWidget.vue'
import QRActionWidget from './widgets/QRActionWidget.vue'
import CountdownWidget from './widgets/CountdownWidget.vue'

const props = defineProps({
  widget: {
    type: Object,
    required: true
  },
  templateWidth: {
    type: Number,
    default: 1920
  },
  templateHeight: {
    type: Number,
    default: 1080
  }
})

onMounted(() => {
  if (!import.meta.env.DEV) return
  console.log(`[WidgetRenderer] Widget ${props.widget.id} (${props.widget.name}) mounted`, {
    type: props.widget.type,
    x: props.widget.x,
    y: props.widget.y,
    width: props.widget.width,
    height: props.widget.height,
    contentsCount: props.widget.contents?.length || 0,
    contents: props.widget.contents?.map(c => ({
      id: c.id,
      name: c.name,
      type: c.type,
      is_active: c.is_active,
      secure_url: c.secure_url ? `${c.secure_url.substring(0, 50)}...` : null
    }))
  })
})

const widgetStyle = computed(() => {
  const {
    x = 0,
    y = 0,
    width = 100,
    height = 100,
    z_index = 0,
    content_json = {},
  } = props.widget
  const rotation = Number(content_json.rotation || content_json.rotate || 0) || 0

  return {
    position: 'absolute',
    left: `${Number(x) || 0}px`,
    top: `${Number(y) || 0}px`,
    width: `${Math.max(1, Number(width) || 1)}px`,
    height: `${Math.max(1, Number(height) || 1)}px`,
    zIndex: z_index,
    transform: rotation ? `rotate(${rotation}deg)` : undefined,
    transformOrigin: 'center center',
    overflow: 'hidden',
    visibility: 'visible',
    opacity: 1,
    display: 'block',
  }
})
</script>

<style scoped>
.widget {
  position: absolute;
  box-sizing: border-box;
  will-change: transform;
  backface-visibility: hidden;
  overflow: hidden;
}

.widget-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 0, 0, 0.3);
  color: white;
  font-size: 12px;
}
</style>
