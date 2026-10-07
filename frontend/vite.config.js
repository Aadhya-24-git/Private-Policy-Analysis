import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Resolves backend target for proxying API requests
// In Docker Compose, BACKEND_URL=http://backend:8000 connects across the Docker network.
// For local host development, fallback to http://127.0.0.1:8000.
const backendUrl = process.env.BACKEND_URL || process.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/health': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/analyze': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/documents': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/audit': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/compare': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/docs': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/openapi.json': {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
});
