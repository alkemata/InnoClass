import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 9000,
    proxy: {
      '/api': 'http://0.0.0.0:9000'
  },
    allowedHosts: ['innoclass.alkemata.com'],
    host: true // allow external connections (e.g., for LAN/public access)
}})

