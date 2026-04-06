/**
 * Resolve CSS background for text-like widgets (clock, date, text, marquee, …).
 * When `transparentBackground` is true, color pickers are ignored for the fill.
 *
 * @param {Record<string, unknown> | null | undefined} style - widget style / content_json
 * @param {string} fallback - when not transparent and no backgroundColor set
 */
export function resolveWidgetBackgroundColor(style, fallback = 'transparent') {
  if (!style || typeof style !== 'object') return fallback
  if (style.transparentBackground === true) return 'transparent'
  const bg = style.backgroundColor
  if (bg != null && String(bg).trim() !== '') return bg
  return fallback
}
