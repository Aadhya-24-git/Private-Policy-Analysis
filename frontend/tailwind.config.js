/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
          950: '#022c22',
        },
        dark: {
          950: '#04070e',
          900: '#080c14',
          850: '#0b111e',
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
        },
        // Dedicated ChatGPT-style conversational palette (ready for Phase 9)
        chat: {
          sidebar: '#171717',
          main: '#212121',
          userBubble: '#2f2f2f',
          assistantBubble: '#212121',
          input: '#2f2f2f',
          border: '#3c3c3c',
          accent: '#10a37f',
          accentHover: '#1a7f64',
        },
      },
      fontFamily: {
        sans: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-emerald': '0 0 20px rgba(16, 185, 129, 0.25)',
        'glow-cyan': '0 0 20px rgba(6, 182, 212, 0.25)',
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.25)',
      },
    },
  },
  plugins: [],
};
