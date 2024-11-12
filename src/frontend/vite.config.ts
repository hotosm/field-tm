/// <reference types="vitest" />
import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { configDefaults } from 'vitest/config';
import { VitePWA } from 'vite-plugin-pwa';
import type { VitePWAOptions } from 'vite-plugin-pwa';

const pwaOptions: Partial<VitePWAOptions> = {
  // this is temporary to remove the existing service worker
  // prior to complete PWA removal
  selfDestroying: true,
  manifest: {
    name: 'Field Mapping Tasking Manager',
    short_name: 'FMTM',
    description: 'Coordinated field mapping for Open Mapping campaigns.',
    display: 'standalone',
    theme_color: '#d63f3f',
    background_color: '#d63f3f',
    icons: [
      {
        src: 'pwa-64x64.png',
        sizes: '64x64',
        type: 'image/png',
      },
      {
        src: 'pwa-192x192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: 'pwa-512x512.png',
        sizes: '512x512',
        type: 'image/png',
      },
      {
        src: 'maskable-icon-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  },
};

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  return {
    plugins: [react(), VitePWA(pwaOptions)],
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
