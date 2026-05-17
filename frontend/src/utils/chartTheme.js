/** Resolve design tokens for Chart.js (CSS variables are not read by Chart.js). */

function readCssVar(name, fallback = '') {
  if (typeof document === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

function hexToRgb(hex) {
  const normalized = hex.replace('#', '').trim()
  if (normalized.length === 3) {
    const r = parseInt(normalized[0] + normalized[0], 16)
    const g = parseInt(normalized[1] + normalized[1], 16)
    const b = parseInt(normalized[2] + normalized[2], 16)
    return { r, g, b }
  }
  if (normalized.length !== 6) return null
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  }
}

export function colorWithAlpha(color, alpha) {
  const value = (color || '').trim()
  if (!value) return `rgba(100, 116, 139, ${alpha})`
  if (value.startsWith('rgba(') || value.startsWith('rgb(')) {
    return value.replace(/rgba?\(([^)]+)\)/, (_, inner) => {
      const parts = inner.split(',').map((p) => p.trim())
      if (parts.length >= 3) {
        return `rgba(${parts[0]}, ${parts[1]}, ${parts[2]}, ${alpha})`
      }
      return value
    })
  }
  const rgb = hexToRgb(value)
  if (!rgb) return value
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`
}

export function getChartUiTheme() {
  const online = readCssVar('--forest-green', '#166534')
  const offline = readCssVar('--dusty-red', '#B91C1C')
  const cardBg = readCssVar('--surface-3', readCssVar('--card-bg', '#ffffff'))

  return {
    online,
    offline,
    track: readCssVar('--border-color', '#e2e8f0'),
    tooltip: {
      backgroundColor: cardBg,
      titleColor: readCssVar('--text-heading', '#0f172a'),
      bodyColor: readCssVar('--text-body', '#1e293b'),
      borderColor: readCssVar('--border-color', 'rgba(15, 23, 42, 0.12)'),
    },
  }
}

export function buildDoughnutTooltipOptions(theme = getChartUiTheme()) {
  return {
    backgroundColor: theme.tooltip.backgroundColor,
    titleColor: theme.tooltip.titleColor,
    bodyColor: theme.tooltip.bodyColor,
    borderColor: theme.tooltip.borderColor,
    borderWidth: 1,
    padding: 10,
    displayColors: true,
    boxPadding: 4,
  }
}
