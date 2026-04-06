/**
 * Bundled TV catalog for Data Center when the API is unavailable
 * (e.g. DB migrations not applied yet). Shape matches GET /api/core/tv-brands/.
 */

function slugify(name) {
  return String(name)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

const PLATFORM_DISPLAY = {
  android_tv: 'Android TV',
  google_tv: 'Google TV',
  tizen: 'Tizen',
  webos: 'webOS',
  android_soc: 'Android SoC',
  other: 'Other',
}

const OPERATION_DISPLAY = {
  '16_7': '16/7',
  '18_7': '18/7',
  '24_7': '24/7',
}

const BRIGHTNESS_DISPLAY = {
  indoor: 'Indoor (300-350 nits)',
  high_bright: 'High Bright (500-700 nits)',
  window: 'Window Facing (2500+ nits)',
}

/** Same entries as app/core/management/commands/seed_tv_catalog.py CATALOG */
const RAW_CATALOG = [
  {
    name: 'Sony BRAVIA Professional Displays',
    logo_text: 'SONY',
    description: 'Android TV and Google TV commercial displays with strong SoC performance.',
    sort_order: 10,
    models: [
      { name: 'BZ40 Series', series: 'BZ', platform: 'android_tv', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Premium commercial lineup with strong 24/7 reliability.' },
      { name: 'BZ30 Series', series: 'BZ', platform: 'android_tv', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Balanced cost-performance option for signage networks.' },
    ],
  },
  {
    name: 'Samsung Smart Signage',
    logo_text: 'SAMSUNG',
    description: 'Tizen-based enterprise signage with broad market adoption.',
    sort_order: 20,
    models: [
      { name: 'QMB Series', series: 'QMB', platform: 'tizen', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: '500 nits class for bright indoor spaces.' },
      { name: 'QBB Series', series: 'QBB', platform: 'tizen', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Cost-aware lineup for business-hour usage.' },
      { name: 'OMN Window Display', series: 'OMN', platform: 'tizen', operation_time: '24_7', brightness_class: 'window', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Ultra-high brightness for window-facing deployments.' },
    ],
  },
  {
    name: 'LG Digital Signage',
    logo_text: 'LG',
    description: 'webOS signage displays with wide IPS viewing angles.',
    sort_order: 30,
    models: [
      { name: 'UH Series', series: 'UH', platform: 'webos', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Commercial-grade for continuous operation.' },
      { name: 'UL Series', series: 'UL', platform: 'webos', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Economic series for standard indoor signage.' },
    ],
  },
  {
    name: 'Philips Professional Displays',
    logo_text: 'PHILIPS',
    description: 'Competitive Android SoC signage options for budget-conscious projects.',
    sort_order: 40,
    models: [
      { name: 'D-Line', series: 'D-Line', platform: 'android_soc', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Good 24/7 option with direct Android app deployment potential.' },
      { name: 'Q-Line', series: 'Q-Line', platform: 'android_soc', operation_time: '18_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Lower-cost model family for long daily usage.' },
    ],
  },
  {
    name: 'Hisense Commercial Display',
    logo_text: 'HISENSE',
    description: 'Commercial displays with both Android and proprietary options depending on series.',
    sort_order: 50,
    models: [
      { name: 'DM Series', series: 'DM', platform: 'android_soc', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Enterprise lineup often selected for value/performance.' },
      { name: 'BM Series', series: 'BM', platform: 'other', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Entry-level series for controlled indoor environments.' },
    ],
  },
  {
    name: 'TCL Commercial',
    logo_text: 'TCL',
    description: 'Commercial Android-based panels with competitive pricing.',
    sort_order: 60,
    models: [
      { name: 'P60 Series', series: 'P60', platform: 'android_soc', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Cost-effective standard brightness option.' },
      { name: 'C Series Signage', series: 'C', platform: 'android_soc', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Commercial lineup suitable for heavier duty cycles.' },
    ],
  },
  {
    name: 'Sharp/NEC',
    logo_text: 'SHARP NEC',
    description: 'Enterprise-grade signage for control rooms and mission-critical deployment.',
    sort_order: 70,
    models: [
      { name: 'ME Series', series: 'ME', platform: 'other', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Widely used commercial display family.' },
      { name: 'M Series', series: 'M', platform: 'other', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C'], notes: 'Strong reliability and industrial control support.' },
    ],
  },
  {
    name: 'ViewSonic Commercial Display',
    logo_text: 'VIEWSONIC',
    description: 'Digital signage lineup focused on value and deployability.',
    sort_order: 80,
    models: [
      { name: 'CDE30 Series', series: 'CDE', platform: 'android_soc', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'General-purpose digital signage displays.' },
      { name: 'EP Series', series: 'EP', platform: 'android_soc', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C'], notes: 'Higher reliability variant for persistent usage.' },
    ],
  },
  {
    name: 'BenQ Smart Signage',
    logo_text: 'BENQ',
    description: 'Cloud-friendly signage displays with robust device controls.',
    sort_order: 90,
    models: [
      { name: 'SL Series', series: 'SL', platform: 'android_soc', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Commercial class signage for full-day operations.' },
      { name: 'ST Series', series: 'ST', platform: 'android_soc', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Entry category for cost-sensitive installs.' },
    ],
  },
  {
    name: 'Panasonic Connect',
    logo_text: 'PANASONIC',
    description: 'High-reliability professional displays with strong device management options.',
    sort_order: 100,
    models: [
      { name: 'SQE2 Series', series: 'SQE2', platform: 'other', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C', 'HDMI-CEC'], notes: 'Built for demanding enterprise signage workloads.' },
      { name: 'CQE2 Series', series: 'CQE2', platform: 'other', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Balanced model family for standard deployments.' },
    ],
  },
  {
    name: 'iiyama Professional',
    logo_text: 'IIYAMA',
    description: 'Commercial displays common in retail and transport environments.',
    sort_order: 110,
    models: [
      { name: 'LH60 Series', series: 'LH60', platform: 'android_soc', operation_time: '24_7', brightness_class: 'high_bright', control_ports: ['LAN', 'RS-232C'], notes: '24/7 signage class with high availability focus.' },
      { name: 'LE50 Series', series: 'LE50', platform: 'android_soc', operation_time: '16_7', brightness_class: 'indoor', control_ports: ['LAN', 'HDMI-CEC'], notes: 'Value-focused signage for normal business schedules.' },
    ],
  },
]

export function getTvCatalogFallback() {
  return RAW_CATALOG.map((brand, bi) => {
    const slug = slugify(brand.name)
    const brandId = `fallback-brand-${bi}-${slug}`
    const models = brand.models.map((m, mi) => {
      const mid = `fallback-model-${bi}-${mi}-${slugify(m.name)}`
      const platform = m.platform || 'other'
      const operation_time = m.operation_time || '16_7'
      const brightness_class = m.brightness_class || 'indoor'
      return {
        id: mid,
        name: m.name,
        model_code: m.model_code || '',
        series: m.series || '',
        platform,
        platform_display: PLATFORM_DISPLAY[platform] || platform,
        operation_time,
        operation_time_display: OPERATION_DISPLAY[operation_time] || operation_time,
        brightness_class,
        brightness_class_display: BRIGHTNESS_DISPLAY[brightness_class] || brightness_class,
        control_ports: m.control_ports || [],
        notes: m.notes || '',
        is_download_enabled: false,
        download_url: null,
        download_available: false,
        sort_order: (mi + 1) * 10,
      }
    })
    return {
      id: brandId,
      name: brand.name,
      slug,
      logo_text: brand.logo_text || 'TV',
      logo_url: '',
      description: brand.description || '',
      sort_order: brand.sort_order ?? (bi + 1) * 10,
      models_count: models.length,
      models,
    }
  })
}
