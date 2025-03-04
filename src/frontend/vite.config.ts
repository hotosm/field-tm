/// <reference types="vitest" />
import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { configDefaults } from 'vitest/config';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  return {
    plugins: [react()],
    server: {
      port: 7051,
      host: '0.0.0.0',
    },
    build: {
      minify: mode === 'development' ? false : 'esbuild',
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    test: {
      globals: true,
      exclude: [...configDefaults.exclude, 'e2e', 'playwright-tests-examples'],
    },
  };
});
