import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Bind 127.0.0.1 explicitly — Vite's default "localhost" resolved to ::1 on
    // this machine, leaving http://127.0.0.1:5173 (as documented in README)
    // unreachable (same IPv6/IPv4 class of problem as the proxy target below).
    host: '127.0.0.1',
    proxy: {
      // 127.0.0.1, NOT localhost — Node >= 17 may resolve localhost to ::1
      // while uvicorn binds 127.0.0.1 → ECONNREFUSED (Pitfall 4)
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
