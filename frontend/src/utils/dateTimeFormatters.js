const DEFAULT_LOCALE = 'en-US'

const safeTrim = (value, fallback = '') => {
  if (typeof value !== 'string') return fallback
  const out = value.trim()
  return out || fallback
}

export const normalizeLocale = (locale) => {
  const candidate = safeTrim(locale, DEFAULT_LOCALE)
  try {
    const supported = Intl.DateTimeFormat.supportedLocalesOf([candidate])
    return supported.length ? supported[0] : DEFAULT_LOCALE
  } catch {
    return DEFAULT_LOCALE
  }
}

export const normalizeTimeZone = (timeZone, fallback = 'UTC') => {
  const candidate = safeTrim(timeZone, fallback)
  try {
    new Intl.DateTimeFormat(DEFAULT_LOCALE, { timeZone: candidate }).format(new Date())
    return candidate
  } catch {
    return fallback
  }
}

const pad2 = (n) => String(n).padStart(2, '0')

export const formatLegacyPattern = (date, pattern = '') => {
  const value = safeTrim(pattern, '')
  if (!value) return ''
  const tokenMap = {
    YYYY: String(date.getFullYear()),
    MM: pad2(date.getMonth() + 1),
    DD: pad2(date.getDate()),
    HH: pad2(date.getHours()),
    mm: pad2(date.getMinutes()),
    ss: pad2(date.getSeconds())
  }
  let out = value
  Object.entries(tokenMap).forEach(([token, replacement]) => {
    out = out.replaceAll(token, replacement)
  })
  return out
}

const normalizeHourCycle = (value) => {
  const raw = safeTrim(value, '')
  return ['h11', 'h12', 'h23', 'h24'].includes(raw) ? raw : undefined
}

export const formatClockValue = (date, style = {}, fallbackPattern = 'HH:mm:ss') => {
  const formatPattern = safeTrim(style.format, '') || safeTrim(fallbackPattern, 'HH:mm:ss')
  const locale = normalizeLocale(style.locale || style.lang || DEFAULT_LOCALE)
  const timeZone = normalizeTimeZone(style.timeZone, 'UTC')
  const hourCycle = normalizeHourCycle(style.hourCycle)
  const showSeconds = style.showSeconds !== false
  const includeMeridiem = style.includeMeridiem === true

  try {
    return new Intl.DateTimeFormat(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: showSeconds ? '2-digit' : undefined,
      hour12: includeMeridiem,
      hourCycle,
      timeZone
    }).format(date)
  } catch {
    const legacy = formatLegacyPattern(date, formatPattern)
    return legacy || formatLegacyPattern(date, 'HH:mm:ss')
  }
}

export const formatDateValue = (date, style = {}, fallbackPattern = 'YYYY-MM-DD') => {
  const formatPattern = safeTrim(style.format, '') || safeTrim(fallbackPattern, 'YYYY-MM-DD')
  const locale = normalizeLocale(style.locale || style.lang || DEFAULT_LOCALE)
  const timeZone = normalizeTimeZone(style.timeZone || 'UTC', 'UTC')
  const dateStyle = safeTrim(style.dateStyle, 'medium')

  try {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: ['full', 'long', 'medium', 'short'].includes(dateStyle) ? dateStyle : 'medium',
      timeZone
    }).format(date)
  } catch {
    const legacy = formatLegacyPattern(date, formatPattern)
    return legacy || formatLegacyPattern(date, 'YYYY-MM-DD')
  }
}

export const formatWeekdayValue = (date, style = {}) => {
  const locale = normalizeLocale(style.locale || style.lang || DEFAULT_LOCALE)
  const timeZone = normalizeTimeZone(style.timeZone || 'UTC', 'UTC')
  const weekdayStyle = safeTrim(style.weekdayStyle, 'long')
  const weekday = ['long', 'short', 'narrow'].includes(weekdayStyle) ? weekdayStyle : 'long'

  try {
    return new Intl.DateTimeFormat(locale, {
      weekday,
      timeZone
    }).format(date)
  } catch {
    return new Intl.DateTimeFormat(DEFAULT_LOCALE, { weekday: 'long' }).format(date)
  }
}
