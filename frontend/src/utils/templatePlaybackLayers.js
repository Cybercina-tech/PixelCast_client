/**
 * Build the same layer tree the Web Player uses: when `config_json.widgets` exists,
 * layout/positions come from the editor config merged with DB widget records (media URLs, contents).
 * Otherwise active DB layers are used unchanged.
 */

export function parseTemplateUnit(raw, total, fallback = 0) {
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw
  if (typeof raw === 'string') {
    const value = raw.trim()
    if (value.endsWith('%')) {
      const pct = Number.parseFloat(value.slice(0, -1))
      if (Number.isFinite(pct)) return (pct / 100) * total
    }
    const parsed = Number.parseFloat(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return fallback
}

/**
 * @param {object|null|undefined} template
 * @returns {Array} Layers for `LayerRenderer` (same order/semantics as WebPlayer `sortedLayers`)
 */
export function buildPlaybackLayers(template) {
  if (!template) return []

  const tplWidth = Number(template.width) || 1920
  const tplHeight = Number(template.height) || 1080
  const dbLayers = Array.isArray(template.layers) ? template.layers : []
  const activeDbLayers = dbLayers
    .filter((layer) => layer?.is_active !== false)
    .sort((a, b) => {
      const zA = a?.z_index || 0
      const zB = b?.z_index || 0
      if (zA !== zB) return zA - zB
      return (a?.name || '').localeCompare(b?.name || '')
    })

  const configWidgets = Array.isArray(template?.config_json?.widgets)
    ? template.config_json.widgets
    : []
  if (!configWidgets.length) return activeDbLayers

  const dbWidgetMap = new Map()
  activeDbLayers.forEach((layer) => {
    const widgets = Array.isArray(layer?.widgets) ? layer.widgets : []
    widgets.forEach((widget) => {
      if (widget?.id) dbWidgetMap.set(String(widget.id), widget)
    })
  })

  const mergedWidgets = configWidgets
    .map((configWidget, idx) => {
      const widgetId = String(configWidget?.id || '')
      const dbWidget = dbWidgetMap.get(widgetId) || {}
      const styleJson =
        configWidget?.style && typeof configWidget.style === 'object'
          ? configWidget.style
          : dbWidget?.content_json || {}
      return {
        ...dbWidget,
        id: dbWidget.id || configWidget.id || `cfg-${idx}`,
        name: configWidget?.name || dbWidget?.name || `Widget ${idx + 1}`,
        type: configWidget?.type || dbWidget?.type || 'text',
        x: parseTemplateUnit(configWidget?.x, tplWidth, Number(dbWidget?.x) || 0),
        y: parseTemplateUnit(configWidget?.y, tplHeight, Number(dbWidget?.y) || 0),
        width: Math.max(
          1,
          parseTemplateUnit(configWidget?.width, tplWidth, Number(dbWidget?.width) || 1)
        ),
        height: Math.max(
          1,
          parseTemplateUnit(configWidget?.height, tplHeight, Number(dbWidget?.height) || 1)
        ),
        z_index: configWidget?.zIndex ?? configWidget?.z_index ?? dbWidget?.z_index ?? idx,
        is_active: configWidget?.visible !== false && dbWidget?.is_active !== false,
        content_json: styleJson,
        content_url: configWidget?.content || dbWidget?.content_url || '',
        contents: Array.isArray(dbWidget?.contents) ? dbWidget.contents : [],
      }
    })
    .filter((widget) => widget.is_active !== false)
    .sort((a, b) => {
      const zA = a?.z_index || 0
      const zB = b?.z_index || 0
      if (zA !== zB) return zA - zB
      return (a?.name || '').localeCompare(b?.name || '')
    })

  return [
    {
      id: 'config-layout-layer',
      name: 'Config Layout Layer',
      x: 0,
      y: 0,
      width: tplWidth,
      height: tplHeight,
      z_index: 0,
      background_color: 'transparent',
      opacity: 1,
      animation_type: 'none',
      animation_duration: 0,
      is_active: true,
      widgets: mergedWidgets,
    },
  ]
}

/** True if the template would render at least one layer in the player (same as non-empty `buildPlaybackLayers`). */
export function templateHasRenderablePlayback(template) {
  return buildPlaybackLayers(template).length > 0
}
