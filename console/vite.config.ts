import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'node:path';
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8765', changeOrigin: false } } },
  build: {
    rollupOptions: {
      input: {
        app: resolve(__dirname, 'index.html'),
        recorded: resolve(__dirname, 'recorded-runs.html'),
        reference: resolve(__dirname, 'ux-reference.html'),
      },
    },
  },
});
