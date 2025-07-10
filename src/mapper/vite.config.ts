import path from 'path';
import { defineConfig } from 'vitest/config';
import type { VitePWAOptions } from 'vite-plugin-pwa';
import type { RouteMatchCallbackOptions } from 'workbox-core';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { sveltekit } from '@sveltejs/kit/vite';
import { paraglideVitePlugin } from '@inlang/paraglide-js';
import UnoCSS from 'unocss/vite';
import extractorSvelte from '@unocss/extractor-svelte';

const pwaOptions: Partial<VitePWAOptions> = {
	// This ensures that caches are invalidated when the app is updated
	registerType: 'autoUpdate',
	injectRegister: 'auto',
	strategies: 'generateSW',

	// Important to ensure the PWA runs on the **entire** website
	// For example, it's possible to have `scope: '/project'` for a PWA
	// on only part of the website
	scope: '/',

	// Allow testing the PWA during local development
	devOptions: {
		enabled: true,
		// // Don't fallback on document based (e.g. `/some-page`) requests
		// We need this to include /project/ID as well as home page for direct load when offline
		navigateFallbackAllowlist: [/^\/$/, /^\/project\/.+$/],
		// Enable this to disable runtime caching for easier debugging
		// disableRuntimeConfig: true,
	},

	// // Cache all the imports, including favicon
	workbox: {
		// Don't fallback on document based (e.g. `/some-page`) requests
		// Even though this says `null` by default, I had to set this specifically to `null` to make it work
		// We can do this because we are explicitly handling all navigation routes via runtimeCaching
		navigateFallback: null,

		// Cache all imports
		// globPatterns: ["**/*"],
		globPatterns: ['**/*.{js,css,html,wasm,ico,svg,png,jpg,jpeg,gif,webmanifest}'],

		// This is where the magic happens: routes to cache key to cache to
		runtimeCaching: [
			// Handle SPA navigations (e.g., /, /project/123)
			{
				urlPattern: ({ request }: RouteMatchCallbackOptions) => request.mode === 'navigate',
				// Try to get fresh version; fallback when offline
				handler: 'NetworkFirst',
				// // NOTE the below doesn't work yet, so we use NetworkFirst above
				// // This will load the cached version instantly, then update the cache in the
				// // background. On next refresh, the updated app will be loaded.
				// // This is a good tradeoff, as slightly outdated content is only shown temporarily.
				// handler: 'StaleWhileRevalidate',
				options: {
					cacheName: 'field-tm-html-pages',
					networkTimeoutSeconds: 5, // Setting only valid for NetworkFirst, else errors
					expiration: {
						maxEntries: 50,
						maxAgeSeconds: 60 * 60 * 24 * 7, // 7 days
					},
				},
			},
			// Static assets (e.g., JS, CSS, icons, fonts)
			{
				urlPattern: ({ url }: RouteMatchCallbackOptions) => url.origin === self.location.origin,
				// Serve fast from cache; change infrequently
				handler: 'CacheFirst',
				options: {
					cacheName: 'field-tm-static-assets',
					expiration: {
						maxEntries: 300,
						maxAgeSeconds: 60 * 60 * 24 * 14, // 14 days
					},
				},
			},
		],

		// We need to cache files up to 15MB to allow for PGLite to be cached
		maximumFileSizeToCacheInBytes: 15 * 1024 * 1024,
	},

	// Cache all the static assets in the static folder
	includeAssets: ['**/*', 'icons/*.svg'],

	manifest: {
		id: 'com.hotosm.field-tm',
		name: 'Field-TM',
		short_name: 'Field-TM',
		description: 'Coordinated field mapping for Open Mapping campaigns.',
		categories: ['mapping', 'humanitarian', 'hotosm', 'field', 'odk'],
		scope: '/',
		start_url: '/',
		orientation: 'portrait',
		dir: 'auto',
		display: 'standalone',
		launch_handler: {
			client_mode: 'auto',
		},
		theme_color: '#d63f3f',
		background_color: '#d63f3f',
		icons: [
			{
				src: 'pwa-64x64.png',
				sizes: '64x64',
				type: 'image/png',
				purpose: 'any',
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
		screenshots: [
			{
				src: 'screenshot-mapper.jpeg',
				sizes: '1280x720',
				type: 'image/jpeg',
				form_factor: 'wide',
				label: 'Mapper App',
			},
		],
		related_applications: [
			{
				platform: 'web',
				url: 'https://fmtm.hotosm.org',
			},
		],
	},
};

export default defineConfig({
	// Ensure the base is not '/project/xxx', but always '/', else
	// registration of sw and manifest can fail under /project
	base: '/',
	plugins: [
		sveltekit(),
		SvelteKitPWA(pwaOptions),
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './src/translations',
		}),
		UnoCSS({
			extractors: [extractorSvelte()],
		}),
	],
	server: {
		host: true,
		port: 7057,
	},
	preview: {
		port: 7057,
	},
	resolve: {
		alias: {
			$lib: path.resolve('./src/lib'),
			$components: path.resolve('./src/components'),
			$store: path.resolve('./src/store'),
			$routes: path.resolve('./src/routes'),
			$constants: path.resolve('./src/constants'),
			$static: path.resolve('./static'),
			$styles: path.resolve('./src/styles'),
			$assets: path.resolve('./src/assets'),
			$translations: path.resolve('./src/translations'),
			$migrations: path.resolve('/migrations'),
		},
	},
	test: {
		include: ['./tests/**/*.{test,spec}.{js,ts}'],
		// Required to use browser APIs in testing
		environment: 'jsdom',
		setupFiles: ['./tests/setup.ts'],
	},
	// assetsInclude: ['**/*.tar.gz'],
	optimizeDeps: {
		exclude: ['@electric-sql/pglite'],
	},
});
