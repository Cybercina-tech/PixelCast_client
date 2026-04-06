const SUPPORTED_CHART_TYPES = ['bar', 'line', 'pie', 'doughnut', 'radar', 'polarArea']
const CATEGORICAL_TYPES = ['pie', 'doughnut', 'polarArea']

const DEFAULT_COLORS = [
  '#3b82f6',
  '#14b8a6',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#10b981',
]

const deepClone = (value) => {
  try {
    return JSON.parse(JSON.stringify(value))
  } catch {
    return null
  }
}

const asNumber = (value) => {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? parsed : null
}

const defaultDataset = (index = 0) => ({
  label: `Series ${index + 1}`,
  data: [12, 19, 7],
  backgroundColor: DEFAULT_COLORS[index % DEFAULT_COLORS.length],
  borderColor: DEFAULT_COLORS[index % DEFAULT_COLORS.length],
  borderWidth: 2,
  fill: false,
  tension: 0.3,
})

const buildDefaultOptions = (type = 'bar') => {
  const isCategorical = CATEGORICAL_TYPES.includes(type)
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' },
      title: { display: false, text: '' },
    },
    scales: isCategorical
      ? {}
      : {
          x: {
            display: true,
            grid: { display: true },
            title: { display: false, text: '' },
          },
          y: {
            display: true,
            beginAtZero: true,
            grid: { display: true },
            title: { display: false, text: '' },
          },
        },
  }
}

export const createDefaultChartConfig = (type = 'bar') => {
  const safeType = SUPPORTED_CHART_TYPES.includes(type) ? type : 'bar'
  return {
    type: safeType,
    data: {
      labels: ['A', 'B', 'C'],
      datasets: [defaultDataset(0)],
    },
    options: buildDefaultOptions(safeType),
  }
}

const normalizeDataset = (dataset, index, labelsLength) => {
  const source = dataset && typeof dataset === 'object' ? dataset : {}
  const fallback = defaultDataset(index)
  const rawData = Array.isArray(source.data) ? source.data : []
  const targetLength = Math.max(0, labelsLength)
  const data = []

  for (let i = 0; i < targetLength; i += 1) {
    const v = asNumber(rawData[i])
    data.push(v ?? 0)
  }

  return {
    label: source.label || fallback.label,
    data,
    backgroundColor: source.backgroundColor || fallback.backgroundColor,
    borderColor: source.borderColor || fallback.borderColor,
    borderWidth: Number.isFinite(Number(source.borderWidth)) ? Number(source.borderWidth) : fallback.borderWidth,
    fill: Boolean(source.fill),
    tension: Number.isFinite(Number(source.tension)) ? Number(source.tension) : fallback.tension,
  }
}

export const normalizeChartConfig = (input) => {
  const fallback = createDefaultChartConfig('bar')
  const raw = input && typeof input === 'object' ? deepClone(input) : null
  if (!raw) return fallback

  const type = SUPPORTED_CHART_TYPES.includes(raw.type) ? raw.type : fallback.type
  const labels = Array.isArray(raw.data?.labels) && raw.data.labels.length
    ? raw.data.labels.map((label, index) => {
        const clean = String(label ?? '').trim()
        return clean || `Label ${index + 1}`
      })
    : fallback.data.labels

  const datasetsRaw = Array.isArray(raw.data?.datasets) && raw.data.datasets.length
    ? raw.data.datasets
    : fallback.data.datasets

  const datasets = datasetsRaw.map((dataset, index) => normalizeDataset(dataset, index, labels.length))
  const options = {
    ...buildDefaultOptions(type),
    ...(raw.options && typeof raw.options === 'object' ? raw.options : {}),
  }

  if (CATEGORICAL_TYPES.includes(type)) {
    options.scales = {}
  } else if (!options.scales || typeof options.scales !== 'object') {
    options.scales = buildDefaultOptions(type).scales
  }

  return {
    type,
    data: { labels, datasets },
    options,
  }
}

export const validateChartConfig = (input) => {
  const errors = []
  const config = normalizeChartConfig(input)
  const labels = config.data.labels || []
  const datasets = config.data.datasets || []

  if (!labels.length) {
    errors.push('At least one label is required.')
  }
  if (!datasets.length) {
    errors.push('At least one dataset is required.')
  }

  datasets.forEach((dataset, index) => {
    if (!dataset.label || !String(dataset.label).trim()) {
      errors.push(`Dataset ${index + 1} label is required.`)
    }
    if (!Array.isArray(dataset.data)) {
      errors.push(`Dataset ${index + 1} data must be an array.`)
      return
    }
    if (dataset.data.length !== labels.length) {
      errors.push(`Dataset ${index + 1} length must match labels length.`)
    }
    dataset.data.forEach((value, valueIndex) => {
      if (asNumber(value) === null) {
        errors.push(`Dataset ${index + 1}, item ${valueIndex + 1} must be numeric.`)
      }
    })
  })

  return {
    isValid: errors.length === 0,
    errors,
    normalized: config,
  }
}

export const fromWidgetChartPayload = (widget) => {
  if (!widget) return createDefaultChartConfig('bar')
  let parsed = null

  if (widget.content && typeof widget.content === 'string') {
    try {
      parsed = JSON.parse(widget.content)
    } catch {
      parsed = null
    }
  }

  if (!parsed && widget.style?.chart && typeof widget.style.chart === 'object') {
    parsed = widget.style.chart
  }

  return normalizeChartConfig(parsed)
}

export const toWidgetChartPayload = (config) => {
  const normalized = normalizeChartConfig(config)
  return {
    normalized,
    content: JSON.stringify(normalized),
    stylePatch: {
      chart: normalized,
    },
  }
}

export const chartPresets = [
  {
    id: 'sales',
    name: 'Sales Trend',
    config: {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
          {
            label: 'Sales',
            data: [120, 180, 140, 220, 260, 310],
            borderColor: '#3b82f6',
            backgroundColor: '#3b82f6',
            tension: 0.3,
            borderWidth: 3,
            fill: false,
          },
        ],
      },
    },
  },
  {
    id: 'traffic',
    name: 'Traffic Distribution',
    config: {
      type: 'doughnut',
      data: {
        labels: ['Organic', 'Ads', 'Social', 'Direct'],
        datasets: [
          {
            label: 'Traffic',
            data: [42, 25, 18, 15],
            backgroundColor: ['#3b82f6', '#14b8a6', '#f59e0b', '#ef4444'],
            borderWidth: 0,
          },
        ],
      },
    },
  },
  {
    id: 'comparison',
    name: 'Team Comparison',
    config: {
      type: 'bar',
      data: {
        labels: ['Team A', 'Team B', 'Team C', 'Team D'],
        datasets: [
          { label: 'Q1', data: [18, 22, 15, 27], backgroundColor: '#3b82f6', borderColor: '#3b82f6', borderWidth: 1 },
          { label: 'Q2', data: [24, 17, 20, 29], backgroundColor: '#8b5cf6', borderColor: '#8b5cf6', borderWidth: 1 },
        ],
      },
    },
  },
]

export const chartTypeOptions = SUPPORTED_CHART_TYPES
