import path from 'path';
import { defineConfig } from 'vitest/config';
import type { VitePWAOptions } from 'vite-plugin-pwa';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { sveltekit } from '@sveltejs/kit/vite';
import { paraglide } from '@inlang/paraglide-vite';
import UnoCSS from 'unocss/vite';
import extractorSvelte from '@unocss/extractor-svelte';

const pwaOptions: Partial<VitePWAOptions> = {
	registerType: 'autoUpdate',
	devOptions: {
		enabled: true,
	},
	manifest: {
		name: 'FieldTM',
		short_name: 'FieldTM',
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

export default defineConfig({
	plugins: [
		sveltekit(),
		SvelteKitPWA(pwaOptions),
		paraglide({
			project: './project.inlang',
			outdir: './src/translations',
		}),
		UnoCSS({
			extractors: [extractorSvelte()],
		}),
	],
	server: {
		host: true,
		port: 7055,
	},
	preview: {
		port: 7055,
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
		},
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
	},
	optimizeDeps: {
		exclude: ['@electric-sql/pglite'],
	},
});
