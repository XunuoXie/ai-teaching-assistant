import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(__dirname, '..')

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, projectRoot, '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      port: parseInt(env.VITE_DEV_PORT || '3000'),
      allowedHosts: ['418f357a.r11.cpolar.top'],
      proxy: {
        '/api': {
          target: env.VITE_API_TARGET || 'http://localhost:5000',
          changeOrigin: true
        },
        '/xuetang-entry': {
          target: env.VITE_API_TARGET || 'http://localhost:5001',
          changeOrigin: true
        },
        '/static': {
          target: env.VITE_API_TARGET || 'http://localhost:5001',
          changeOrigin: true
        }
      }
    }
  }
})
