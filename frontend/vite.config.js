import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/data': 'http://localhost:8000',
      '/indicator': 'http://localhost:8000',
      '/backtest': 'http://localhost:8000',
      '/strategies': 'http://localhost:8000',
      '/symbols': 'http://localhost:8000',
      '/fetch': 'http://localhost:8000',
    },
  },
})
