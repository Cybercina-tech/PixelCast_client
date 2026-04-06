<template>
  <div class="widget-preview w-full h-full">
    <TextWidget v-if="widget.type === 'text'" :widget="playerWidget" />
    <MarqueeWidget v-else-if="widget.type === 'marquee'" :widget="playerWidget" />
    <WeatherWidget v-else-if="widget.type === 'weather'" :widget="playerWidget" />
    <ImageWidget v-else-if="widget.type === 'image'" :widget="playerWidget" />
    <VideoWidget v-else-if="widget.type === 'video'" :widget="playerWidget" />
    <AlbumWidget v-else-if="widget.type === 'album'" :widget="playerWidget" />
    <ClockWidget v-else-if="widget.type === 'clock'" :widget="playerWidget" />
    <DateWidget v-else-if="widget.type === 'date'" :widget="playerWidget" />
    <WeekdayWidget v-else-if="widget.type === 'weekday'" :widget="playerWidget" />
    <div v-else-if="widget.type === 'webview'" class="w-full h-full bg-slate-900 text-slate-200 border border-slate-700 rounded p-3 flex flex-col justify-center">
      <div class="text-xs uppercase tracking-wide text-slate-400 mb-2">Webview Preview</div>
      <div class="text-sm break-all">{{ webviewPreviewUrl || 'No URL set' }}</div>
      <div class="text-[11px] text-slate-500 mt-2">Live iframe is disabled in editor preview to avoid browser cross-origin focus warnings.</div>
    </div>
    <ChartWidget v-else-if="widget.type === 'chart'" :widget="playerWidget" />
    <QRActionWidget v-else-if="widget.type === 'qr_action'" :widget="playerWidget" />
    <CountdownWidget v-else-if="widget.type === 'countdown'" :widget="playerWidget" />
    <div v-else class="default-widget-preview flex items-center justify-center w-full h-full bg-gray-300 text-gray-600 text-sm">
      {{ widget.type }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TextWidget from '@/components/player/widgets/TextWidget.vue'
import MarqueeWidget from '@/components/player/widgets/MarqueeWidget.vue'
import WeatherWidget from '@/components/player/widgets/WeatherWidget.vue'
import ImageWidget from '@/components/player/widgets/ImageWidget.vue'
import VideoWidget from '@/components/player/widgets/VideoWidget.vue'
import AlbumWidget from '@/components/player/widgets/AlbumWidget.vue'
import ClockWidget from '@/components/player/widgets/ClockWidget.vue'
import DateWidget from '@/components/player/widgets/DateWidget.vue'
import WeekdayWidget from '@/components/player/widgets/WeekdayWidget.vue'
import ChartWidget from '@/components/player/widgets/ChartWidget.vue'
import QRActionWidget from '@/components/player/widgets/QRActionWidget.vue'
import CountdownWidget from '@/components/player/widgets/CountdownWidget.vue'
import { fromWidgetChartPayload } from '@/utils/chartConfig'

const props = defineProps({
  widget: {
    type: Object,
    required: true
  }
})

const getPreviewText = (widget, style) => {
  if (widget.type !== 'text' && widget.type !== 'marquee') return ''
  const raw = widget.content || style.text || ''
  return typeof raw === 'string' ? raw : ''
}

// Convert editor widget format to player widget format
const playerWidget = computed(() => {
  const widget = props.widget
  const style = widget.style || {}
  const normalizedChart = widget.type === 'chart' ? fromWidgetChartPayload(widget) : null
  const previewText = getPreviewText(widget, style)
  const weatherPreviewData = widget.type === 'weather'
    ? {
        updated_at: new Date().toISOString(),
        location: { label: style.location || widget.content || 'Weather' },
        current: { temp: 24, temp_min: 19, temp_max: 28, icon: '02d' },
        forecast: [
          { date: new Date().toISOString().split('T')[0], temp_min: 18, temp_max: 27, icon: '02d' },
          { date: new Date(Date.now() + 86400000).toISOString().split('T')[0], temp_min: 17, temp_max: 25, icon: '03d' },
          { date: new Date(Date.now() + 172800000).toISOString().split('T')[0], temp_min: 16, temp_max: 24, icon: '10d' },
        ],
      }
    : null
  const qrStyle = widget.type === 'qr_action'
    ? {
        ...style,
        redirectPath: style.redirectPath || '/qr/preview-link',
        displayUrl: style.displayUrl || 'https://example.com/menu',
      }
    : null
  const albumContents = widget.type === 'album'
    ? (Array.isArray(style.playlist) ? style.playlist : [])
        .map((item, idx) => ({
          id: item.content_id || `album-item-${idx}`,
          name: item.name || `Album Item ${idx + 1}`,
          is_active: true,
          order: idx,
          duration: Number(item.durationSec || style.defaultDurationSec || 10),
          secure_url: item.url || '',
          content_json: {
            durationSec: Number(item.durationSec || style.defaultDurationSec || 10),
            transition: item.transition || style.transition || 'fade',
          },
          type: item.mediaType || 'image',
        }))
        .filter(item => !!item.secure_url)
    : []
  
  // Create a player-compatible widget object
  // Player widgets expect: widget.content_json (for styles) and widget.contents[] (for content data)
  const playerFormat = {
    id: widget.id,
    type: widget.type,
    name: widget.name,
    ...(widget.type === 'countdown'
      ? {
          content: typeof widget.content === 'string' ? widget.content : '',
          content_url: typeof widget.content === 'string' ? widget.content : '',
        }
      : {}),
    // content_json contains widget-level style/configuration
    content_json: {
      // Text widget style properties
      color: style.color,
      fontSize: style.fontSize,
      fontFamily: style.fontFamily,
      textAlign: style.textAlign,
      backgroundColor: style.backgroundColor,
      fontWeight: style.fontWeight,
      lineHeight: style.lineHeight,
      // Image/Video widget style properties
      objectFit: style.objectFit,
      // Chart config is passed to player chart renderer
      chart: normalizedChart,
      weatherData: weatherPreviewData,
      weatherMeta: widget.type === 'weather' ? { source: 'preview', stale: false } : undefined,
      ...(widget.type === 'qr_action' ? qrStyle : {}),
      // Ensure marquee settings are fully forwarded.
      ...style,
    },
    // contents array contains the actual content items
    contents: widget.type === 'album'
      ? albumContents
      : (previewText || (widget.type !== 'text' && widget.type !== 'marquee' && widget.content)) ? [{
      id: `preview-content-${widget.id}`,
      name: widget.name || 'Preview Content',
      is_active: true,
      order: 0,
      // Text content
      text_content: (widget.type === 'text' || widget.type === 'marquee') ? previewText : undefined,
      // Image/Video content URL
      secure_url: (widget.type === 'image' || widget.type === 'video') ? widget.content : undefined,
      // Webview URL
      file_url: widget.type === 'webview' ? widget.content : undefined,
      // Content-level JSON (can override widget-level styles)
      content_json: {
        ...style,
        chart: normalizedChart
      }
    }] : []
  }
  
  return playerFormat
})

const webviewPreviewUrl = computed(() => {
  if (props.widget.type !== 'webview') return ''
  return props.widget.content || ''
})

</script>

<style scoped>
.widget-preview {
  pointer-events: none;
  width: 100%;
  height: 100%;
}
</style>

