/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#07090e',
          900: '#0d111a',
          850: '#131926',
          800: '#182030',
          700: '#222d42',
          600: '#2e3c57',
        },
        terminal: {
          green: '#10b981',
          red: '#f43f5e',
          amber: '#f59e0b',
          blue: '#3b82f6',
          cyan: '#06b6d4',
          purple: '#a855f7'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
