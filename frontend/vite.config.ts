import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8080'

  return {
    plugins: [react()],
    server: {
      port: 3000,
      host: 'localhost',
      strictPort: false,
      // HMR: 브라우저에서 열 때는 ws://localhost:3000 사용.
      // 'refresh.js → ws://localhost:8081' 오류는 Cursor 내장 미리보기 등에서 나올 수 있으며, 일반 브라우저에서 http://localhost:3000 으로 열면 발생하지 않음.
      hmr: {
        host: 'localhost',
        port: 3000,
        clientPort: 3000,
        protocol: 'ws'
      },
      watch: {
        usePolling: false
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true
        },
        '/health': {
          target: apiTarget,
          changeOrigin: true
        }
      }
    }
  }
})
