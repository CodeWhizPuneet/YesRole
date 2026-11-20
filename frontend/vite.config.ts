import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { loadEnv } from 'vite'

export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  server: {
    strictPort: true,
    proxy: { '/api': loadEnv(mode, '.', 'YESROLE_').YESROLE_API_PROXY_TARGET || 'http://127.0.0.1:8000' },
  },
  test: { environment: 'jsdom' },
}))
