/// <reference types="vitest" />
import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { configDefaults } from 'vitest/config';
import { VitePWA } from 'vite-plugin-pwa';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  return {
    plugins: [
      react(),
      // VitePWA({
      //   registerType: 'autoUpdate',
      //   devOptions: {
      //     enabled: true,
      //   },
      //   selfDestroying: false,
      // }),
    ],
    server: {
      port: 7051,
      host: '0.0.0.0',
      watch: {
        usePolling: false,
      },
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
      environment: 'jsdom',
      setupFiles: './setupTests.ts',
      exclude: [...configDefaults.exclude, 'e2e', 'playwright-tests-examples'],
    },
  };
});
