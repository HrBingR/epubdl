import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
     resolve: {
       alias: {
         '/webfonts': '/public/webfonts',
       },
     },
  server: {
    proxy: {
      // Proxy /api and /download requests to the Flask backend.
      '/api': {
        target: 'http://127.0.0.1:5000', // Flask dev server
        changeOrigin: true,
      },
      '/download': {
        target: 'http://127.0.0.1:5000', // Flask dev server
        changeOrigin: true,
      },
    },
  },
});