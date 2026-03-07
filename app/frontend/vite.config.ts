import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
  base: '/',
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
