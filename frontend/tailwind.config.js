/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 工业风格配色
        industrial: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98',
          600: '#486581',
          700: '#334e68',
          800: '#243b53',
          900: '#102a43',
          950: '#0a1929',
        },
        // 信号色
        signal: {
          green: '#00ff88',
          red: '#ff3366',
          yellow: '#ffcc00',
          blue: '#00ccff',
        },
        // 面板色
        panel: {
          bg: '#1a2332',
          card: '#243447',
          border: '#3a4a5c',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Orbitron', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 204, 255, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 204, 255, 0.8)' },
        },
      },
    },
  },
  plugins: [],
}