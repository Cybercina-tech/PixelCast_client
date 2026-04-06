<template>
<div v-if="!te.rightPanelCollapsed" class="flex-1 min-h-0 overflow-y-auto custom-scrollbar scroll-container p-4">
<div class="mb-4 grid grid-cols-2 editor-inspector-tabs">
  <button
    @click="te.rightPanelTab = 'properties'"
    :class="te.rightPanelTab === 'properties' ? 'bg-accent-color text-white' : 'text-muted hover:text-primary'"
    class="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
  >
    Properties
  </button>
  <button
    @click="te.rightPanelTab = 'layers'"
    :class="te.rightPanelTab === 'layers' ? 'bg-accent-color text-white' : 'text-muted hover:text-primary'"
    class="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
  >
    Layers
  </button>
</div>

<div v-if="te.rightPanelTab === 'properties' && te.selectedWidget" class="space-y-6">
  <!-- Common Properties -->
  <div>
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Position & Size</h3>
    <div class="space-y-3">
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">X (px)</label>
          <input
            :value="Math.round(te.selectedWidget.x)"
            type="number"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetProperty('x', $event.target.value)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Y (px)</label>
          <input
            :value="Math.round(te.selectedWidget.y)"
            type="number"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetProperty('y', $event.target.value)"
          />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Width (px)</label>
          <input
            :value="Math.round(te.selectedWidget.width)"
            type="number"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetProperty('width', $event.target.value)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Height (px)</label>
          <input
            :value="Math.round(te.selectedWidget.height)"
            type="number"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetProperty('height', $event.target.value)"
          />
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Rotation (°)</label>
        <input
          v-model.number="te.selectedWidget.rotation"
          type="number"
          step="1"
          class="input-base w-full px-3 py-2 text-sm"
          @input="te.updateWidgetProperty('rotation', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Z-Index</label>
        <input
          v-model.number="te.selectedWidget.zIndex"
          type="number"
          class="input-base w-full px-3 py-2 text-sm"
          @input="te.updateWidgetProperty('zIndex', $event.target.value)"
        />
      </div>
    </div>
  </div>

  <!-- Text Widget Properties -->
  <div v-if="te.selectedWidget.type === 'text'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Text Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Content</label>
        <textarea
          v-model="te.selectedWidget.content"
          rows="3"
          class="textarea-base w-full px-3 py-2 text-sm"
          @input="te.updateWidgetProperty('content', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Font Family</label>
        <select
          v-model="te.selectedWidget.style.fontFamily"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('fontFamily', $event.target.value)"
        >
          <option v-for="font in WIDGET_FONT_OPTIONS" :key="font.value" :value="font.value">
            {{ font.label }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Font Size (px)</label>
        <div class="grid grid-cols-[1fr_auto] gap-2 items-center">
          <input
            type="range"
            min="8"
            max="240"
            step="1"
            :value="te.getFontSizeNumber(te.selectedWidget.style?.fontSize, 24)"
            class="w-full"
            @input="te.updateWidgetStyle('fontSize', `${$event.target.value}px`)"
          />
          <input
            type="number"
            min="8"
            max="240"
            :value="te.getFontSizeNumber(te.selectedWidget.style?.fontSize, 24)"
            class="input-base w-20 px-2 py-1 text-sm"
            @input="te.updateWidgetStyle('fontSize', `${$event.target.value || 24}px`)"
          />
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Color</label>
        <input
          v-model="te.selectedWidget.style.color"
          type="color"
          class="editor-color-input"
          @input="te.updateWidgetStyle('color', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Background Color</label>
        <input
          :value="te.getBackgroundHex(te.selectedWidget.style?.backgroundColor, '#000000')"
          type="color"
          class="editor-color-input"
          :disabled="te.selectedWidget.style?.transparentBackground === true"
          @input="te.updateWidgetStyle('backgroundColor', $event.target.value)"
        />
        <label class="editor-switch-row mt-2">
          <span class="text-sm text-primary">Transparent background</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="te.selectedWidget.style?.transparentBackground === true"
              @change="te.updateWidgetStyle('transparentBackground', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Text Align</label>
        <select
          v-model="te.selectedWidget.style.textAlign"
          class="editor-select"
          @change="te.updateWidgetStyle('textAlign', $event.target.value)"
        >
          <option value="left">Left</option>
          <option value="center">Center</option>
          <option value="right">Right</option>
          <option value="justify">Justify</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Marquee Widget Properties -->
  <div v-if="te.selectedWidget.type === 'marquee'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Marquee Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Content</label>
        <textarea
          v-model="te.selectedWidget.content"
          rows="3"
          class="textarea-base w-full px-3 py-2 text-sm"
          @input="te.updateWidgetProperty('content', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Built-in Style</label>
        <select
          :value="te.selectedWidget.style?.preset || 'breakingNews'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.applyMarqueePreset($event.target.value)"
        >
          <option
            v-for="preset in te.marqueePresets"
            :key="preset.id"
            :value="preset.id"
          >
            {{ preset.label }}
          </option>
        </select>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Mode</label>
          <select
            :value="te.selectedWidget.style?.mode || 'continuous'"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.updateWidgetStyle('mode', $event.target.value)"
          >
            <option value="continuous">Continuous</option>
            <option value="step">Step</option>
            <option value="bounce">Bounce</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Direction</label>
          <select
            :value="te.selectedWidget.style?.direction || 'left'"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.updateWidgetStyle('direction', $event.target.value)"
          >
            <option value="left">Left</option>
            <option value="right">Right</option>
            <option value="up">Up</option>
            <option value="down">Down</option>
          </select>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Speed (px/s)</label>
          <input
            type="number"
            min="20"
            max="800"
            :value="te.normalizeRange(te.selectedWidget.style?.speed, 120, 20, 800)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('speed', te.normalizeRange($event.target.value, 120, 20, 800))"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Gap (px)</label>
          <input
            type="number"
            min="16"
            max="500"
            :value="te.normalizeRange(te.selectedWidget.style?.gap, 80, 16, 500)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('gap', te.normalizeRange($event.target.value, 80, 16, 500))"
          />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Step Hold (s)</label>
          <input
            type="number"
            min="0.2"
            max="12"
            step="0.1"
            :value="te.normalizeRange(te.selectedWidget.style?.stepHold, 1.5, 0.2, 12)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('stepHold', te.normalizeRange($event.target.value, 1.5, 0.2, 12))"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Bounce Hold (s)</label>
          <input
            type="number"
            min="0"
            max="5"
            step="0.1"
            :value="te.normalizeRange(te.selectedWidget.style?.bounceHold, 0.8, 0, 5)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('bounceHold', te.normalizeRange($event.target.value, 0.8, 0, 5))"
          />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <label class="editor-switch-row">
          <span class="text-sm text-primary">Loop</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="te.selectedWidget.style?.loop !== false"
              @change="te.updateWidgetStyle('loop', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
        <label class="editor-switch-row">
          <span class="text-sm text-primary">Fade Edge</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="te.selectedWidget.style?.fadeEdge !== false"
              @change="te.updateWidgetStyle('fadeEdge', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
        <label class="editor-switch-row">
          <span class="text-sm text-primary">Uppercase</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="te.selectedWidget.style?.uppercase === true"
              @change="te.updateWidgetStyle('uppercase', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
        <label class="editor-switch-row">
          <span class="text-sm text-primary">Reverse</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="te.selectedWidget.style?.reverse === true"
              @change="te.updateWidgetStyle('reverse', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Separator</label>
        <input
          :value="te.selectedWidget.style?.separator || ' • '"
          type="text"
          class="input-base w-full px-3 py-2 text-sm"
          @input="te.updateWidgetStyle('separator', $event.target.value || ' • ')"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Font Size (px)</label>
          <input
            type="number"
            min="12"
            max="220"
            :value="te.getFontSizeNumber(te.selectedWidget.style?.fontSize, 42)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('fontSize', `${te.normalizeRange($event.target.value, 42, 12, 220)}px`)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Font Weight</label>
          <select
            :value="te.selectedWidget.style?.fontWeight || '700'"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.updateWidgetStyle('fontWeight', $event.target.value)"
          >
            <option value="400">Regular</option>
            <option value="500">Medium</option>
            <option value="600">Semibold</option>
            <option value="700">Bold</option>
            <option value="800">Extra Bold</option>
          </select>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Text Color</label>
          <input
            :value="te.selectedWidget.style?.color || '#ffffff'"
            type="color"
            class="editor-color-input"
            @input="te.updateWidgetStyle('color', $event.target.value)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Background</label>
          <input
            :value="te.getBackgroundHex(te.selectedWidget.style?.backgroundColor, '#111111')"
            type="color"
            class="editor-color-input"
            :disabled="te.selectedWidget.style?.transparentBackground === true"
            @input="te.updateWidgetStyle('backgroundColor', $event.target.value)"
          />
        </div>
      </div>
      <label class="editor-switch-row">
        <span class="text-sm text-primary">Transparent background</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="te.selectedWidget.style?.transparentBackground === true"
            @change="te.updateWidgetStyle('transparentBackground', $event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
    </div>
  </div>

  <!-- Weather Widget Properties -->
  <div v-if="te.selectedWidget.type === 'weather'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Weather Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Location (City or City,CountryCode)</label>
        <input
          :value="te.selectedWidget.style?.location || te.selectedWidget.content || ''"
          type="text"
          class="input-base w-full px-3 py-2 text-sm"
          placeholder="e.g. Tehran,IR"
          @input="te.updateWidgetStyle('location', $event.target.value); te.updateWidgetProperty('content', $event.target.value)"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Units</label>
          <select
            :value="te.selectedWidget.style?.units || 'celsius'"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.updateWidgetStyle('units', $event.target.value)"
          >
            <option value="celsius">Celsius (C)</option>
            <option value="fahrenheit">Fahrenheit (F)</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Layout</label>
          <select
            :value="te.selectedWidget.style?.layout || 'compact'"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.updateWidgetStyle('layout', $event.target.value)"
          >
            <option value="compact">Compact</option>
            <option value="extended">Extended</option>
          </select>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Forecast Days</label>
          <input
            type="number"
            min="3"
            max="5"
            :value="te.normalizeRange(te.selectedWidget.style?.forecastDays, 3, 3, 5)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('forecastDays', te.normalizeRange($event.target.value, 3, 3, 5))"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Hide After Stale (h)</label>
          <input
            type="number"
            min="1"
            max="24"
            :value="te.normalizeRange(te.selectedWidget.style?.hideAfterHours, 6, 1, 24)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('hideAfterHours', te.normalizeRange($event.target.value, 6, 1, 24))"
          />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Text Color</label>
          <input
            :value="te.selectedWidget.style?.color || '#ffffff'"
            type="color"
            class="editor-color-input"
            @input="te.updateWidgetStyle('color', $event.target.value)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Background</label>
          <input
            :value="te.getBackgroundHex(te.selectedWidget.style?.backgroundColor, '#0f172a')"
            type="color"
            class="editor-color-input"
            :disabled="te.selectedWidget.style?.transparentBackground === true"
            @input="te.updateWidgetStyle('backgroundColor', $event.target.value)"
          />
        </div>
      </div>
      <label class="editor-switch-row">
        <span class="text-sm text-primary">Transparent background</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="te.selectedWidget.style?.transparentBackground === true"
            @change="te.updateWidgetStyle('transparentBackground', $event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
    </div>
  </div>

  <div v-if="te.selectedWidget.type === 'qr_action'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">QR Action Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">CTA Text</label>
        <input
          :value="te.selectedWidget.style?.ctaText || ''"
          type="text"
          class="input-base w-full px-3 py-2 text-sm"
          placeholder="Scan for discount"
          @input="te.updateWidgetStyle('ctaText', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Campaign ID</label>
        <input
          :value="te.selectedWidget.style?.campaignId || ''"
          type="text"
          class="input-base w-full px-3 py-2 text-sm"
          placeholder="branch-x-morning"
          @input="te.updateWidgetStyle('campaignId', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Default URL</label>
        <input
          :value="te.selectedWidget.style?.defaultUrl || te.selectedWidget.content || ''"
          type="url"
          class="input-base w-full px-3 py-2 text-sm"
          placeholder="https://example.com/menu"
          @input="te.updateWidgetStyle('defaultUrl', $event.target.value); te.updateWidgetProperty('content', $event.target.value)"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Foreground</label>
          <input
            :value="te.selectedWidget.style?.foregroundColor || '#000000'"
            type="color"
            class="editor-color-input"
            @input="te.updateWidgetStyle('foregroundColor', $event.target.value)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Background</label>
          <input
            :value="te.selectedWidget.style?.backgroundColor || '#ffffff'"
            type="color"
            class="editor-color-input"
            :disabled="te.selectedWidget.style?.transparentBackground === true"
            @input="te.updateWidgetStyle('backgroundColor', $event.target.value)"
          />
        </div>
      </div>
      <label class="editor-switch-row">
        <span class="text-sm text-primary">Transparent background</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="te.selectedWidget.style?.transparentBackground === true"
            @change="te.updateWidgetStyle('transparentBackground', $event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Quiet Zone (modules)</label>
          <input
            type="number"
            min="4"
            max="12"
            :value="te.normalizeRange(te.selectedWidget.style?.quietZone, 4, 4, 12)"
            class="input-base w-full px-3 py-2 text-sm"
            @input="te.updateWidgetStyle('quietZone', te.normalizeRange($event.target.value, 4, 4, 12))"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Error Correction</label>
          <select
            :value="te.selectedWidget.style?.errorCorrectionLevel || 'H'"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.updateWidgetStyle('errorCorrectionLevel', $event.target.value)"
          >
            <option value="H">High (H)</option>
            <option value="Q">Quartile (Q)</option>
            <option value="M">Medium (M)</option>
            <option value="L">Low (L)</option>
          </select>
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Center Logo URL (optional)</label>
        <input
          :value="te.selectedWidget.style?.logoUrl || ''"
          type="url"
          class="input-base w-full px-3 py-2 text-sm"
          placeholder="https://example.com/logo.png"
          @input="te.updateWidgetStyle('logoUrl', $event.target.value)"
        />
      </div>
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-xs font-medium text-muted">Rules</label>
          <button
            type="button"
            class="btn-outline px-2 py-1 rounded text-xs"
            @click="te.addQrRule()"
          >
            + Add Rule
          </button>
        </div>
        <div class="space-y-2">
          <div
            v-for="(rule, ruleIndex) in te.currentQrRules"
            :key="`qr-rule-${ruleIndex}`"
            class="editor-panel-inset p-2.5 space-y-2"
          >
            <div class="grid grid-cols-[1fr_auto] gap-2 items-center">
              <input
                :value="rule.name || ''"
                type="text"
                class="input-base w-full px-2 py-1.5 text-xs"
                placeholder="Rule name"
                @input="te.updateQrRule(ruleIndex, 'name', $event.target.value)"
              />
              <button
                type="button"
                class="px-2 py-1 text-[11px] rounded border border-red-200 dark:border-red-500/60 text-red-600 dark:text-red-300 hover:bg-red-500/10"
                @click="te.removeQrRule(ruleIndex)"
              >
                Remove
              </button>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-muted mb-1">Priority</label>
                <input
                  :value="rule.priority ?? ruleIndex + 1"
                  type="number"
                  min="1"
                  class="input-base w-full px-2 py-1.5 text-xs"
                  @input="te.updateQrRule(ruleIndex, 'priority', Math.max(1, Number.parseInt($event.target.value || '1', 10) || 1))"
                />
              </div>
              <label class="editor-switch-row editor-switch-row--compact">
                <span class="text-[11px] text-primary">Active</span>
                <span class="editor-switch">
                  <input
                    type="checkbox"
                    class="sr-only peer"
                    :checked="rule.isActive !== false"
                    @change="te.updateQrRule(ruleIndex, 'isActive', $event.target.checked)"
                  />
                  <span class="editor-switch-track">
                    <span class="editor-switch-thumb"></span>
                  </span>
                </span>
              </label>
            </div>
            <div>
              <label class="block text-[11px] text-muted mb-1">Target URL</label>
              <input
                :value="rule.targetUrl || ''"
                type="url"
                class="input-base w-full px-2 py-1.5 text-xs"
                placeholder="https://example.com/landing"
                @input="te.updateQrRule(ruleIndex, 'targetUrl', $event.target.value)"
              />
            </div>
            <div>
              <label class="block text-[11px] text-muted mb-1">Time Window</label>
              <div class="grid grid-cols-2 gap-2 mb-2">
                <label class="flex items-center gap-1.5 text-[11px] text-primary">
                  <input
                    type="radio"
                    :name="`rule-time-mode-${ruleIndex}`"
                    :checked="te.isQrRuleAllDay(rule)"
                    @change="te.setQrRuleTimeMode(ruleIndex, 'all_day')"
                  />
                  All Day
                </label>
                <label class="flex items-center gap-1.5 text-[11px] text-primary">
                  <input
                    type="radio"
                    :name="`rule-time-mode-${ruleIndex}`"
                    :checked="!te.isQrRuleAllDay(rule)"
                    @change="te.setQrRuleTimeMode(ruleIndex, 'custom')"
                  />
                  Custom Range
                </label>
              </div>
              <div v-if="!te.isQrRuleAllDay(rule)" class="grid grid-cols-2 gap-2">
                <select
                  :value="rule.startHour ?? 8"
                  class="select-base w-full px-2 py-1.5 text-xs"
                  @change="te.updateQrRule(ruleIndex, 'startHour', Number.parseInt($event.target.value, 10))"
                >
                  <option v-for="hour in te.qrHourOptions" :key="`start-${ruleIndex}-${hour.value}`" :value="hour.value">
                    {{ hour.label }}
                  </option>
                </select>
                <select
                  :value="rule.endHour ?? 18"
                  class="select-base w-full px-2 py-1.5 text-xs"
                  @change="te.updateQrRule(ruleIndex, 'endHour', Number.parseInt($event.target.value, 10))"
                >
                  <option v-for="hour in te.qrHourOptions" :key="`end-${ruleIndex}-${hour.value}`" :value="hour.value">
                    {{ hour.label }}
                  </option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-[11px] text-muted mb-1">Days of Week</label>
              <div class="grid grid-cols-7 gap-1">
                <button
                  v-for="day in te.qrWeekdayOptions"
                  :key="`day-${ruleIndex}-${day.value}`"
                  type="button"
                  class="px-0 py-1 rounded text-[10px] border transition-colors"
                  :class="(rule.daysOfWeek || []).includes(day.value) ? 'bg-emerald-500/20 border-emerald-400/80 text-emerald-200' : 'border-border-color text-muted hover:text-primary'"
                  @click="te.toggleQrRuleDay(ruleIndex, day.value)"
                >
                  {{ day.label }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="text-xs" :class="te.qrReadabilityOk(te.selectedWidget) ? 'text-emerald-400' : 'text-amber-400'">
        {{ te.qrReadabilityMessage(te.selectedWidget) }}
      </div>
    </div>
  </div>

  <!-- Image/Video Widget Properties -->
  <div v-if="te.selectedWidget.type === 'image' || te.selectedWidget.type === 'video'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">{{ te.selectedWidget.type === 'image' ? 'Image' : 'Video' }} Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Media Source</label>
        <div class="flex gap-2">
          <button
            @click="te.openMediaLibrary(te.selectedWidget.type)"
            class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-lg text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Select from Library
          </button>
        </div>
        <div v-if="te.selectedWidget.content" class="mt-2">
          <label class="block text-xs font-medium text-muted mb-1.5">Current URL</label>
          <div class="flex gap-2">
            <input
              v-model="te.selectedWidget.content"
              type="text"
              placeholder="Enter image/video URL"
              class="editor-select flex-1 placeholder:text-muted"
              @input="te.updateWidgetProperty('content', $event.target.value)"
            />
            <button
              @click="te.selectedWidget.content = ''; te.updateWidgetProperty('content', '')"
              class="px-3 py-2 bg-red-600/50 hover:bg-red-600 text-white rounded-lg text-sm transition-colors duration-200"
              title="Clear URL"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <!-- Preview -->
          <div v-if="te.selectedWidget.content" class="mt-2 rounded-lg overflow-hidden border border-border-color bg-surface-inset dark:bg-slate-800/30">
            <img
              v-if="te.selectedWidget.type === 'image'"
              :src="te.selectedWidget.content"
              alt="Preview"
              class="w-full h-32 object-cover"
              @error="te.handlePreviewError"
            />
            <video
              v-else-if="te.selectedWidget.type === 'video'"
              :src="te.selectedWidget.content"
              class="w-full h-32 object-cover"
              muted
              preload="metadata"
            />
          </div>
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Object Fit</label>
        <select
          v-model="te.selectedWidget.style.objectFit"
          class="editor-select"
          @change="te.updateWidgetStyle('objectFit', $event.target.value)"
        >
          <option value="contain">Contain</option>
          <option value="cover">Cover</option>
          <option value="fill">Fill</option>
          <option value="none">None</option>
        </select>
      </div>
    </div>
  </div>

  <div v-if="te.selectedWidget.type === 'album'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Album Playlist Properties</h3>
    <div class="space-y-3">
      <div class="flex gap-2">
        <button
          @click="te.openMediaLibrary('album')"
          class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-lg text-sm font-medium transition-all duration-200"
        >
          Add Media to Queue
        </button>
        <button
          @click="te.clearAlbumQueue()"
          class="px-3 py-2 bg-red-600/50 hover:bg-red-600 text-white rounded-lg text-sm transition-colors duration-200"
        >
          Clear
        </button>
      </div>

      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Transition</label>
        <select
          :value="te.selectedWidget.style?.transition || 'fade'"
          class="editor-select"
          @change="te.updateWidgetStyle('transition', $event.target.value)"
        >
          <option value="fade">Fade</option>
          <option value="slideLeft">Slide Left</option>
          <option value="slideRight">Slide Right</option>
          <option value="none">None</option>
        </select>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Default Duration (s)</label>
          <input
            type="number"
            min="1"
            max="300"
            :value="te.selectedWidget.style?.defaultDurationSec || 10"
            class="editor-select"
            @input="te.updateWidgetStyle('defaultDurationSec', te.normalizeRange($event.target.value, 10, 1, 300))"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Transition Duration (ms)</label>
          <input
            type="number"
            min="0"
            max="5000"
            :value="te.selectedWidget.style?.transitionDurationMs || 450"
            class="editor-select"
            @input="te.updateWidgetStyle('transitionDurationMs', te.normalizeRange($event.target.value, 450, 0, 5000))"
          />
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Object Fit</label>
        <select
          :value="te.selectedWidget.style?.objectFit || 'contain'"
          class="editor-select"
          @change="te.updateWidgetStyle('objectFit', $event.target.value)"
        >
          <option value="contain">Contain</option>
          <option value="cover">Cover</option>
        </select>
      </div>

      <div class="editor-panel-inset p-3">
        <div class="text-xs text-muted mb-2">Queue Items</div>
        <div v-if="!te.albumQueueItems.length" class="text-xs text-muted">
          No media selected yet.
        </div>
        <div v-for="(item, idx) in te.albumQueueItems" :key="item.content_id" class="grid grid-cols-[1fr_auto_auto_auto] gap-2 items-center py-1">
          <div class="text-xs text-primary truncate" :title="item.name || item.content_id">
            {{ idx + 1 }}. {{ item.name || item.content_id }}
          </div>
          <input
            type="number"
            min="1"
            max="300"
            :value="item.durationSec || 10"
            class="input-base w-20 px-2 py-1 text-xs"
            @input="te.updateAlbumItemDuration(item.content_id, $event.target.value)"
          />
          <button type="button" class="px-2 py-1 text-xs rounded border border-border-color bg-surface-2 hover:bg-surface-inset text-primary" @click="te.moveAlbumItem(item.content_id, -1)">Up</button>
          <button class="px-2 py-1 text-xs bg-red-700/70 hover:bg-red-600 rounded" @click="te.removeAlbumItem(item.content_id)">Del</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Clock/Date Widget Properties -->
  <div v-if="te.selectedWidget.type === 'clock' || te.selectedWidget.type === 'date' || te.selectedWidget.type === 'weekday'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">{{ te.selectedWidget.type === 'clock' ? 'Clock' : te.selectedWidget.type === 'date' ? 'Date' : 'Weekday' }} Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Style Preset</label>
        <div class="grid grid-cols-[1fr_auto] gap-2">
          <select
            :value="te.selectedWidget.style?.preset || (te.selectedWidget.type === 'clock' ? 'digitalBoard' : te.selectedWidget.type === 'date' ? 'calendarCard' : 'weekdayBold')"
            class="select-base w-full px-3 py-2 text-sm"
            @change="te.applyTemporalPreset(te.selectedWidget.type, $event.target.value)"
          >
            <option
              v-for="preset in te.selectedWidget.type === 'clock' ? te.clockStylePresets : te.selectedWidget.type === 'date' ? te.dateStylePresets : te.weekdayStylePresets"
              :key="preset.id"
              :value="preset.id"
            >
              {{ preset.label }}
            </option>
          </select>
          <button
            class="btn-outline px-3 py-2 rounded text-xs"
            @click="te.applyTemporalPreset(te.selectedWidget.type, te.selectedWidget.style?.preset || (te.selectedWidget.type === 'clock' ? 'digitalBoard' : te.selectedWidget.type === 'date' ? 'calendarCard' : 'weekdayBold'))"
          >
            Apply
          </button>
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Format</label>
        <input
          v-model="te.selectedWidget.content"
          type="text"
          :placeholder="te.selectedWidget.type === 'clock' ? 'HH:mm:ss' : te.selectedWidget.type === 'date' ? 'YYYY-MM-DD' : 'dddd'"
          class="editor-select placeholder:text-muted"
          @input="te.updateWidgetProperty('content', $event.target.value); te.updateWidgetStyle('format', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Language / Locale</label>
        <select
          :value="te.selectedWidget.style?.locale || 'en-US'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('locale', $event.target.value)"
        >
          <option v-for="locale in te.supportedLocales" :key="locale.value" :value="locale.value">
            {{ locale.label }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Time Zone</label>
        <select
          :value="te.selectedWidget.style?.timeZone || te.defaultTimeZone"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('timeZone', $event.target.value)"
        >
          <option
            v-for="zone in te.worldTimeZones"
            :key="zone.value"
            :value="zone.value"
          >
            {{ zone.label }}
          </option>
        </select>
      </div>
      <label
        class="editor-switch-row"
        :class="{ 'editor-switch-row--disabled': te.selectedWidget.type === 'weekday' }"
      >
        <span class="text-sm text-primary">Show Weekday</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="te.selectedWidget.type === 'weekday' ? true : te.selectedWidget.style?.showWeekday === true"
            :disabled="te.selectedWidget.type === 'weekday'"
            @change="te.updateWidgetStyle('showWeekday', $event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
      <div v-if="te.selectedWidget.type !== 'clock' || te.selectedWidget.style?.showWeekday === true || te.selectedWidget.type === 'weekday'">
        <label class="block text-xs font-medium text-muted mb-1.5">Weekday Style</label>
        <select
          :value="te.selectedWidget.style?.weekdayStyle || 'long'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('weekdayStyle', $event.target.value)"
        >
          <option value="long">Long</option>
          <option value="short">Short</option>
          <option value="narrow">Narrow</option>
        </select>
      </div>
      <div v-if="te.selectedWidget.type === 'clock'">
        <label class="block text-xs font-medium text-muted mb-1.5">Clock Display Mode</label>
        <select
          :value="te.selectedWidget.style?.displayMode || 'timeOnly'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('displayMode', $event.target.value)"
        >
          <option value="timeOnly">Time Only</option>
          <option value="timePlusWeekday">Time + Weekday (Inline)</option>
          <option value="stacked">Stacked</option>
        </select>
      </div>
      <div v-if="te.selectedWidget.type === 'date'">
        <label class="block text-xs font-medium text-muted mb-1.5">Date Display Mode</label>
        <select
          :value="te.normalizeDateDisplayModeForEditor(te.selectedWidget.style)"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.onDateDisplayModeChange($event.target.value)"
        >
          <option value="dateOnly">Date Only</option>
          <option value="datePlusWeekday">Date + Weekday (Inline)</option>
          <option value="stacked">Stacked</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Font Size (px)</label>
        <div class="grid grid-cols-[1fr_auto] gap-2 items-center">
          <input
            type="range"
            min="12"
            max="220"
            step="1"
            :value="te.getFontSizeNumber(te.selectedWidget.style?.fontSize, te.selectedWidget.type === 'clock' ? 56 : te.selectedWidget.type === 'date' ? 40 : 42)"
            class="w-full"
            @input="te.updateWidgetStyle('fontSize', `${$event.target.value}px`)"
          />
          <input
            type="number"
            min="12"
            max="220"
            :value="te.getFontSizeNumber(te.selectedWidget.style?.fontSize, te.selectedWidget.type === 'clock' ? 56 : te.selectedWidget.type === 'date' ? 40 : 42)"
            class="input-base w-20 px-2 py-1 text-sm"
            @input="te.updateWidgetStyle('fontSize', `${$event.target.value || (te.selectedWidget.type === 'clock' ? 56 : te.selectedWidget.type === 'date' ? 40 : 42)}px`)"
          />
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Text Color</label>
        <input
          :value="te.selectedWidget.style?.color || '#ffffff'"
          type="color"
          class="editor-color-input"
          @input="te.updateWidgetStyle('color', $event.target.value)"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Background Color</label>
        <input
          :value="te.getBackgroundHex(te.selectedWidget.style?.backgroundColor, '#000000')"
          type="color"
          class="editor-color-input"
          :disabled="te.selectedWidget.style?.transparentBackground === true"
          @input="te.updateWidgetStyle('backgroundColor', $event.target.value)"
        />
        <label class="editor-switch-row mt-2">
          <span class="text-sm text-primary">Transparent background</span>
          <span class="editor-switch">
            <input
              type="checkbox"
              class="sr-only peer"
              :checked="te.selectedWidget.style?.transparentBackground === true"
              @change="te.updateWidgetStyle('transparentBackground', $event.target.checked)"
            />
            <span class="editor-switch-track">
              <span class="editor-switch-thumb"></span>
            </span>
          </span>
        </label>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Font Family</label>
        <select
          :value="te.selectedWidget.style?.fontFamily || 'Arial, sans-serif'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('fontFamily', $event.target.value)"
        >
          <option v-for="font in WIDGET_FONT_OPTIONS" :key="font.value" :value="font.value">
            {{ font.label }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Text Align</label>
        <select
          :value="te.selectedWidget.style?.textAlign || 'center'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('textAlign', $event.target.value)"
        >
          <option value="left">Left</option>
          <option value="center">Center</option>
          <option value="right">Right</option>
        </select>
      </div>
    </div>
  </div>

  <div v-if="te.selectedWidget.type === 'countdown'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Countdown</h3>
    <div class="space-y-3">
      <div class="rounded-lg border border-border-color/80 bg-card/30 p-3 space-y-3">
        <p class="text-[11px] font-semibold text-muted uppercase tracking-wide">
          Names
        </p>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Title above countdown</label>
          <input
            :value="te.selectedWidget.content || ''"
            type="text"
            class="input-base w-full px-3 py-2 text-sm"
            placeholder="Spring Festival"
            @input="te.updateWidgetProperty('content', $event.target.value)"
          />
          <p class="text-[10px] text-muted mt-1">
            Shown on screen above the timer (player & preview).
          </p>
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Widget name (editor list)</label>
          <input
            :value="te.selectedWidget.name || ''"
            type="text"
            class="input-base w-full px-3 py-2 text-sm"
            placeholder="Countdown — Lobby"
            @input="te.updateWidgetProperty('name', $event.target.value)"
          />
          <p class="text-[10px] text-muted mt-1">
            Label in the layers list only; not drawn on the canvas.
          </p>
        </div>
      </div>
      <div class="space-y-2">
        <div class="min-w-0">
          <label class="block text-xs font-medium text-muted mb-1.5">Progress start (optional)</label>
          <input
            :value="te.countdownStartLocal"
            type="datetime-local"
            class="input-base w-full min-w-0 px-3 py-2 text-sm"
            @input="te.onCountdownStartAtInput($event.target.value)"
          />
          <p class="text-[10px] text-muted mt-1 leading-snug">
            Bar only — empty uses first display.
          </p>
        </div>
        <div class="min-w-0">
          <label class="block text-xs font-medium text-muted mb-1.5">Target date and time (local)</label>
          <input
            :value="te.countdownTargetLocal"
            type="datetime-local"
            class="input-base w-full min-w-0 px-3 py-2 text-sm"
            @input="te.onCountdownTargetAtInput($event.target.value)"
          />
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Appearance theme</label>
        <select
          :value="te.selectedWidget.style?.theme || COUNTDOWN_THEME_DEFAULT_ID"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.applyCountdownTheme($event.target.value)"
        >
          <option
            v-for="opt in COUNTDOWN_THEMES"
            :key="opt.id"
            :value="opt.id"
            :title="opt.hint || opt.label"
          >
            {{ opt.label }}
          </option>
        </select>
        <p class="text-[11px] text-muted mt-1">
          {{ te.countdownThemeHint }}
        </p>
      </div>
      <div
        v-if="te.countdownIsCustomTheme"
        class="grid grid-cols-2 gap-3 rounded-lg border border-border-color/80 bg-card/40 p-3"
      >
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Text color</label>
          <input
            :value="te.selectedWidget.style?.color || '#fecaca'"
            type="color"
            class="editor-color-input"
            @input="te.updateWidgetStyle('color', $event.target.value)"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Background (solid)</label>
          <input
            :value="te.getBackgroundHex(te.selectedWidget.style?.backgroundColor, '#450a0a')"
            type="color"
            class="editor-color-input"
            :disabled="te.selectedWidget.style?.transparentBackground === true"
            @input="te.updateWidgetStyle('backgroundColor', $event.target.value)"
          />
        </div>
      </div>
      <p
        v-else
        class="text-[11px] text-muted rounded-md bg-card/30 px-2 py-1.5 border border-border-color/60"
      >
        Colors and background for this theme are preset. Choose <strong class="text-primary">Custom</strong> to set your own solid colors or gradients in JSON if needed.
      </p>
      <label class="editor-switch-row">
        <span class="text-sm text-primary">Transparent background</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="te.selectedWidget.style?.transparentBackground === true"
            @change="te.updateWidgetStyle('transparentBackground', $event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">Font size (px)</label>
        <input
          type="number"
          min="12"
          max="220"
          :value="te.getFontSizeNumber(te.selectedWidget.style?.fontSize, 36)"
          class="input-base w-full px-3 py-2 text-sm"
          @input="te.updateWidgetStyle('fontSize', `${te.normalizeRange($event.target.value, 36, 12, 220)}px`)"
        />
      </div>
      <label class="editor-switch-row">
        <span class="text-sm text-primary">Show progress bar</span>
        <span class="editor-switch">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="te.selectedWidget.style?.showProgress === true"
            @change="te.updateWidgetStyle('showProgress', $event.target.checked)"
          />
          <span class="editor-switch-track">
            <span class="editor-switch-thumb"></span>
          </span>
        </span>
      </label>
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">When timer hits zero</label>
        <select
          :value="te.selectedWidget.style?.zeroStateMode || 'showMessage'"
          class="select-base w-full px-3 py-2 text-sm"
          @change="te.updateWidgetStyle('zeroStateMode', $event.target.value)"
        >
          <option value="showMessage">Show message</option>
          <option value="hideWidget">Hide widget</option>
        </select>
      </div>
      <div v-if="(te.selectedWidget.style?.zeroStateMode || 'showMessage') === 'showMessage'">
        <label class="block text-xs font-medium text-muted mb-1.5">Message at zero</label>
        <textarea
          :value="te.selectedWidget.style?.zeroStateMessage || ''"
          rows="2"
          class="input-base w-full px-3 py-2 text-sm"
          placeholder="The event has started!"
          @input="te.updateWidgetStyle('zeroStateMessage', $event.target.value)"
        />
      </div>
      <details class="rounded-lg border border-border-color/70 bg-card/20 p-2">
        <summary class="text-xs font-medium text-muted cursor-pointer select-none">
          Unit labels (translation)
        </summary>
        <div class="grid grid-cols-2 gap-2 mt-3">
          <div>
            <label class="block text-[11px] text-muted mb-1">Days</label>
            <input
              :value="te.selectedWidget.style?.labels?.days ?? 'Days'"
              type="text"
              class="input-base w-full px-2 py-1.5 text-sm"
              @input="te.updateCountdownLabel('days', $event.target.value)"
            />
          </div>
          <div>
            <label class="block text-[11px] text-muted mb-1">Hours</label>
            <input
              :value="te.selectedWidget.style?.labels?.hours ?? 'Hours'"
              type="text"
              class="input-base w-full px-2 py-1.5 text-sm"
              @input="te.updateCountdownLabel('hours', $event.target.value)"
            />
          </div>
          <div>
            <label class="block text-[11px] text-muted mb-1">Minutes</label>
            <input
              :value="te.selectedWidget.style?.labels?.minutes ?? 'Minutes'"
              type="text"
              class="input-base w-full px-2 py-1.5 text-sm"
              @input="te.updateCountdownLabel('minutes', $event.target.value)"
            />
          </div>
          <div>
            <label class="block text-[11px] text-muted mb-1">Seconds</label>
            <input
              :value="te.selectedWidget.style?.labels?.seconds ?? 'Seconds'"
              type="text"
              class="input-base w-full px-2 py-1.5 text-sm"
              @input="te.updateCountdownLabel('seconds', $event.target.value)"
            />
          </div>
        </div>
      </details>
    </div>
  </div>

  <div v-if="te.selectedWidget.type === 'webview'">
    <h3 class="text-sm font-semibold mb-3 text-muted uppercase">Webview Properties</h3>
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-muted mb-1.5">URL</label>
        <input
          v-model="te.webviewUrlDraft"
          type="url"
          placeholder="https://example.com"
          class="editor-select placeholder:text-muted"
          @keydown.enter.prevent="te.applyWebviewUrl"
        />
        <button
          type="button"
          class="btn-primary mt-2 w-full px-3 py-2 rounded-lg text-sm font-medium"
          @click="te.applyWebviewUrl"
        >
          Apply URL
        </button>
        <p class="text-[11px] text-muted mt-2">Loads the address in the widget when you click Apply (or press Enter).</p>
      </div>
    </div>
  </div>

  <div v-if="te.selectedWidget.type === 'chart'">
    <ChartEditorPanel
      :widget="te.selectedWidget"
      @update="te.handleChartWidgetUpdate"
    />
  </div>
</div>

<div v-else-if="te.rightPanelTab === 'properties'" class="text-center py-12">
  <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-inset dark:bg-slate-700/50 mb-4">
    <svg class="w-8 h-8 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  </div>
  <h3 class="text-sm font-medium text-primary mb-2">No widget selected</h3>
  <p class="text-xs text-muted">Select a widget from the canvas to edit its properties</p>
</div>

<div v-if="te.rightPanelTab === 'layers'">
  <h3 class="text-sm font-semibold mb-3 text-muted uppercase tracking-wide">Layers ({{ te.widgets.length }})</h3>
  <div v-if="te.widgets.length === 0" class="text-center py-8">
    <svg class="w-12 h-12 mx-auto text-muted mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
    <p class="text-sm text-muted">No widgets yet</p>
    <p class="text-xs text-muted mt-1">Add widgets to get started</p>
  </div>
  <div v-else class="space-y-2">
    <div
      v-for="widget in te.sortedWidgetsByZIndex"
      :key="widget.id"
      :draggable="true"
      @dragstart="te.handleDragStart($event, widget.id)"
      @dragover.prevent="te.handleDragOver($event)"
      @drop="te.handleDrop($event, widget.id)"
      @dragenter.prevent
      @click="te.selectWidget(widget.id)"
      :class="[
        'px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200 text-sm border',
        te.selectedWidgetId === widget.id ? 'bg-accent-color text-white border-accent-color shadow-lg' : 'bg-card hover:bg-card border-border-color text-primary',
        te.draggingWidgetId === widget.id ? 'opacity-50' : '',
        te.dragOverWidgetId === widget.id ? 'ring-2 ring-blue-400' : ''
      ]"
    >
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1 flex-1 min-w-0">
          <button
            @click.stop="te.toggleWidgetVisibility(widget.id)"
            :class="[
              'transition-colors duration-200 flex-shrink-0',
              widget.visible !== false ? 'text-muted hover:text-primary' : 'text-muted opacity-50'
            ]"
            :title="widget.visible !== false ? 'Hide Widget' : 'Show Widget'"
          >
            <svg v-if="widget.visible !== false" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.29 3.29m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.736m-7.101 2.101l-3.29-3.29" />
            </svg>
          </button>
          <span v-if="te.editingWidgetId !== widget.id" @dblclick.stop="te.startEditingWidgetName(widget.id)" class="font-medium truncate cursor-text">{{ widget.name }}</span>
          <input
            v-else
            v-model="te.editingWidgetName"
            @blur="te.finishEditingWidgetName(widget.id)"
            @keyup.enter="te.finishEditingWidgetName(widget.id)"
            @keyup.esc="te.cancelEditingWidgetName"
            class="font-medium bg-surface-inset dark:bg-gray-800 border border-blue-500 rounded px-1 py-0.5 text-sm flex-1 min-w-0 text-primary"
            @click.stop
            :ref="(el) => { if (te.widgetNameInput) te.widgetNameInput.value = el }"
          />
          <span class="text-xs text-muted flex-shrink-0 ml-auto">Z:{{ widget.zIndex }}</span>
        </div>
        <div class="flex items-center gap-0.5 flex-shrink-0" @click.stop>
          <button
            type="button"
            class="px-1.5 py-1 rounded text-[10px] font-medium bg-surface-inset dark:bg-slate-700/80 text-muted hover:text-primary border border-border-color/60"
            title="Send backward"
            @click="te.moveLayerOrder(widget.id, 'back')"
          >
            ↓
          </button>
          <button
            type="button"
            class="px-1.5 py-1 rounded text-[10px] font-medium bg-surface-inset dark:bg-slate-700/80 text-muted hover:text-primary border border-border-color/60"
            title="Bring forward"
            @click="te.moveLayerOrder(widget.id, 'forward')"
          >
            ↑
          </button>
          <button
            type="button"
            class="px-1.5 py-1 rounded text-[10px] font-medium bg-surface-inset dark:bg-slate-700/80 text-muted hover:text-primary border border-border-color/60"
            title="Send to back"
            @click="te.sendLayerToBack(widget.id)"
          >
            ⤓
          </button>
          <button
            type="button"
            class="px-1.5 py-1 rounded text-[10px] font-medium bg-surface-inset dark:bg-slate-700/80 text-muted hover:text-primary border border-border-color/60"
            title="Bring to front"
            @click="te.bringLayerToFront(widget.id)"
          >
            ⤒
          </button>
        </div>
        <button @click.stop="te.deleteWidget(widget.id)" class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 active:scale-95 transition-all duration-200 flex-shrink-0 ml-2" title="Delete Widget">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      <div class="text-xs text-muted mt-1.5 flex items-center gap-2">
        <span class="px-1.5 py-0.5 bg-surface-inset dark:bg-gray-600/50 rounded text-[10px] uppercase text-muted">{{ widget.type }}</span>
        <span class="text-muted">{{ Math.round(widget.width) }}×{{ Math.round(widget.height) }}</span>
      </div>
    </div>
  </div>
</div>
</div>
</template>

<script setup>
import { inject } from 'vue'
import ChartEditorPanel from './chart/ChartEditorPanel.vue'
import { WIDGET_FONT_OPTIONS } from '@/constants/widgetFonts'
import { COUNTDOWN_THEMES, COUNTDOWN_THEME_DEFAULT_ID } from '@/constants/countdownThemes'
import { TEMPLATE_EDITOR_INJECTION_KEY } from '../templateEditorInjectionKey'

const te = inject(TEMPLATE_EDITOR_INJECTION_KEY)
</script>
