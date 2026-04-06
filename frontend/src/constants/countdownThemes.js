/**
 * Countdown widget appearance presets (TemplateEditor + WebPlayer).
 * `preset` fields map to widget `style` / content_json (non-custom themes).
 */
export const COUNTDOWN_THEMES = [
  {
    id: 'urgency',
    label: 'Urgency',
    hint: 'Deep red — deadlines & alerts',
    preset: {
      color: '#fecdd3',
      backgroundColor:
        'linear-gradient(155deg, #3f0a12 0%, #7f1d1d 42%, #450a0a 100%)',
      fontWeight: '800',
      textShadow: '0 0 28px rgba(248, 113, 113, 0.45)',
      borderRadius: '16px',
    },
  },
  {
    id: 'celebration',
    label: 'Celebration',
    hint: 'Gold — launches & parties',
    preset: {
      color: '#fffbeb',
      backgroundColor:
        'linear-gradient(160deg, #422006 0%, #78350f 45%, #451a03 100%)',
      fontWeight: '800',
      textShadow: '0 0 20px rgba(251, 191, 36, 0.5)',
      borderRadius: '16px',
    },
  },
  {
    id: 'midnight',
    label: 'Midnight',
    hint: 'Indigo glass — premium UI',
    preset: {
      color: '#e0e7ff',
      backgroundColor:
        'linear-gradient(145deg, #0f172a 0%, #1e1b4b 50%, #172554 100%)',
      fontWeight: '800',
      textShadow: '0 2px 18px rgba(129, 140, 248, 0.35)',
      borderRadius: '18px',
    },
  },
  {
    id: 'neon',
    label: 'Neon',
    hint: 'Cyber cyan & magenta',
    preset: {
      color: '#ecfeff',
      backgroundColor: '#0c0a1a',
      fontWeight: '800',
      textShadow:
        '0 0 12px rgba(34, 211, 238, 0.9), 0 0 28px rgba(217, 70, 239, 0.45)',
      borderRadius: '12px',
    },
  },
  {
    id: 'minimal',
    label: 'Minimal',
    hint: 'Soft cards on charcoal',
    preset: {
      color: '#f1f5f9',
      backgroundColor: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
      fontWeight: '700',
      textShadow: 'none',
      borderRadius: '14px',
    },
  },
  {
    id: 'corporate',
    label: 'Corporate',
    hint: 'Navy & trustworthy',
    preset: {
      color: '#f8fafc',
      backgroundColor:
        'linear-gradient(135deg, #0c4a6e 0%, #0f172a 55%, #082f49 100%)',
      fontWeight: '700',
      textShadow: '0 1px 2px rgba(0, 0, 0, 0.35)',
      borderRadius: '10px',
    },
  },
  {
    id: 'sport',
    label: 'Sport',
    hint: 'Bold racing yellow',
    preset: {
      color: '#fef08a',
      backgroundColor: 'linear-gradient(90deg, #0a0a0a 0%, #171717 50%, #0a0a0a 100%)',
      fontWeight: '900',
      textShadow: '2px 2px 0 rgba(0,0,0,0.85)',
      borderRadius: '8px',
    },
  },
  {
    id: 'forest',
    label: 'Forest',
    hint: 'Natural green calm',
    preset: {
      color: '#ecfccb',
      backgroundColor:
        'linear-gradient(165deg, #052e16 0%, #14532d 48%, #064e3b 100%)',
      fontWeight: '800',
      textShadow: '0 2px 16px rgba(74, 222, 128, 0.25)',
      borderRadius: '16px',
    },
  },
  {
    id: 'sunset',
    label: 'Sunset',
    hint: 'Warm coral & rose',
    preset: {
      color: '#fff1f2',
      backgroundColor:
        'linear-gradient(135deg, #4c0519 0%, #9f1239 40%, #7c2d12 100%)',
      fontWeight: '800',
      textShadow: '0 0 22px rgba(251, 113, 133, 0.4)',
      borderRadius: '20px',
    },
  },
  {
    id: 'ice',
    label: 'Ice',
    hint: 'Frosted cool blue',
    preset: {
      color: '#f0f9ff',
      backgroundColor:
        'linear-gradient(180deg, #0c4a6e 0%, #082f49 50%, #0c2d48 100%)',
      fontWeight: '700',
      textShadow: '0 2px 12px rgba(125, 211, 252, 0.35)',
      borderRadius: '18px',
    },
  },
  {
    id: 'luxury',
    label: 'Luxury',
    hint: 'Black & gold elegant',
    preset: {
      color: '#fde68a',
      backgroundColor: 'linear-gradient(145deg, #0a0a0a 0%, #1c1917 40%, #292524 100%)',
      fontWeight: '700',
      textShadow: '0 0 1px rgba(253, 230, 138, 0.8)',
      borderRadius: '8px',
    },
  },
  {
    id: 'retro',
    label: 'Retro',
    hint: 'Terminal green CRT',
    preset: {
      color: '#4ade80',
      backgroundColor: '#052e16',
      fontWeight: '700',
      textShadow: '0 0 8px rgba(74, 222, 128, 0.65)',
      borderRadius: '4px',
    },
  },
  {
    id: 'ocean',
    label: 'Ocean',
    hint: 'Deep teal aqua',
    preset: {
      color: '#ccfbf1',
      backgroundColor:
        'linear-gradient(160deg, #042f2e 0%, #115e59 45%, #134e4a 100%)',
      fontWeight: '800',
      textShadow: '0 2px 14px rgba(45, 212, 191, 0.35)',
      borderRadius: '16px',
    },
  },
  {
    id: 'aurora',
    label: 'Aurora',
    hint: 'Northern lights shimmer',
    preset: {
      color: '#ecfdf5',
      backgroundColor:
        'linear-gradient(125deg, #022c22 0%, #134e4a 35%, #312e81 70%, #1e1b4b 100%)',
      fontWeight: '800',
      textShadow: '0 0 20px rgba(52, 211, 153, 0.4)',
      borderRadius: '22px',
    },
  },
  {
    id: 'custom',
    label: 'Custom',
    hint: 'Your own colors below',
    preset: null,
  },
]

export const COUNTDOWN_THEME_IDS = COUNTDOWN_THEMES.map((t) => t.id)

export const COUNTDOWN_THEME_DEFAULT_ID = 'urgency'

export function getCountdownThemePreset(themeId) {
  const entry = COUNTDOWN_THEMES.find((t) => t.id === themeId)
  if (!entry || !entry.preset) {
    return { theme: themeId === 'custom' ? 'custom' : COUNTDOWN_THEME_DEFAULT_ID }
  }
  return { ...entry.preset, theme: entry.id }
}
