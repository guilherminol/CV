import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // 127.0.0.1, NOT localhost — Node >= 17 may resolve localhost to ::1
      // while uvicorn binds 127.0.0.1 → ECONNREFUSED (Pitfall 4)
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
