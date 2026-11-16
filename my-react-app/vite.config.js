import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// The FastAPI backend sends no CORS headers, so the dev server forwards API calls to it.
// Set BACKEND_URL in .env.local if the backend is not on its default address.
export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, '.', '').BACKEND_URL || 'http://127.0.0.1:8000'
  const proxy = Object.fromEntries(['/api', '/routes', '/health'].map((p) => [p, { target, changeOrigin: true }]))
  return {
    plugins: [react()],
    server: { allowedHosts: true, proxy },
    preview: { proxy },
  }
})
