/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0D0F10',
        surface: '#16181A',
        elevated: '#1E2124',
        border: '#2A2F33',
        primaryGreen: '#22C55E',
        textPrimary: '#F2F4F7',
        textSecondary: '#A1A7AE',
        textMuted: '#6B7280',
        warn: '#F59E0B',
        error: '#EF4444',
      },
      borderRadius: {
        card: '16px',
        metric: '12px',
        pill: '24px',
        row: '8px',
      },
      fontFamily: {
        sans: ['Segoe UI Variable', 'Segoe UI', 'sans-serif'],
        mono: ['Cascadia Mono', 'monospace'],
      },
      keyframes: {
        shine: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        }
      },
      animation: {
        shine: 'shine 3s infinite',
      }
    },
  },
  plugins: [],
}
