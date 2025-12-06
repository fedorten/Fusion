import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'paerser2.ru',
      'www.paerser2.ru',
      'localhost',
      '127.0.0.1'
    ]
    // Убираем proxy - теперь этим занимается nginx
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
