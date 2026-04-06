/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  // کلاس‌هایی که ممکن است به‌صورت داینامیک یا کم‌استفاده باشند تا در Purge حذف نشوند
  safelist: [
    'bg-card',
    'bg-surface-1',
    'bg-surface-2',
    'bg-surface-3',
    'bg-editor-workspace',
    'bg-editor-matte',
    'border',
    'border-border-color',
  ],
  theme: {
    // Keep all custom tokens under `extend` — do not set `theme.colors` at the top level
    // or Tailwind's default palette (white, black, slate, …) will be replaced.
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        // Surfaces — must stay in sync with style.css :root / .dark (single source: CSS variables)
        base: {
          DEFAULT: 'var(--bg-color-solid)',
        },
        card: {
          DEFAULT: 'var(--card-bg)',
        },
        // Elevation (levels 1–3 + nested inset). bg-card remains the main panel utility.
        surface: {
          1: 'var(--surface-1)',
          2: 'var(--surface-2)',
          3: 'var(--surface-3)',
          inset: 'var(--surface-inset)',
        },
        /* Template editor shell — sync with style.css Antler tokens */
        editor: {
          workspace: 'var(--editor-workspace-bg)',
          matte: 'var(--editor-matte-bg)',
        },
        // Border tokens — هم به‌صورت utility اختصاصی و هم نام عمومی
        border: 'var(--border-color)',
        'border-color': {
          DEFAULT: 'var(--border-color)',
        },
        // Semantic text — required for @apply in Vue SFC styles (maps to CSS variables on html)
        primary: 'var(--text-heading)',
        secondary: 'var(--text-main)',
        muted: 'var(--text-muted)',
        // Brand (emerald) — use `brand` so `text-primary` can remain semantic (custom CSS) for headings
        brand: {
          DEFAULT: 'var(--brand-primary)',
          hover: 'var(--brand-primary-hover)',
          active: 'var(--brand-primary-active)',
        },
        success: {
          DEFAULT: '#16A34A',
        },
        warning: {
          DEFAULT: '#D97706',
        },
        error: {
          DEFAULT: '#DC2626',
        },
        info: {
          DEFAULT: '#2563EB',
        },
        // Legacy colors (kept for backward compatibility)
        orange: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
          950: '#431407',
        },
        neutral: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e5e5e5',
          300: '#d4d4d4',
          400: '#a3a3a3',
          500: '#737373',
          600: '#525252',
          700: '#404040',
          800: '#262626',
          900: '#171717',
          950: '#0a0a0a',
        },
        zinc: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b',
        }
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 15s ease infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        },
      },
      boxShadow: {
        'card-dark': '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
        soft: 'var(--shadow-soft)',
      },
    },
  },
  plugins: [],
}
