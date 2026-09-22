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
        space: {
          950: '#04060a',
          900: '#07090e',
          850: '#0a0e16',
          800: '#0d121c',
          700: '#151c2c',
          600: '#1e293b',
        },
        orbit: {
          emerald: '#10b981',
          cyan: '#06b6d4',
          amber: '#f59e0b',
          crimson: '#ef4444',
          violet: '#8b5cf6',
        }
      },
      fontFamily: {
        heading: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.04em',
        widest: '0.2em',
      },
      backgroundImage: {
        'radial-vignette': 'radial-gradient(circle at 50% 30%, rgba(16, 185, 129, 0.08) 0%, rgba(7, 9, 14, 0.6) 60%, #07090e 100%)',
      }
    },
  },
  plugins: [],
};
