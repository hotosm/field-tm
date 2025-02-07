import path from 'path';
import { defineConfig } from 'vitest/config';
import { VitePWA } from 'vite-plugin-pwa';
import { sveltekit } from '@sveltejs/kit/vite';
import { paraglide } from '@inlang/paraglide-vite';
import UnoCSS from 'unocss/vite';
import extractorSvelte from '@unocss/extractor-svelte';

export default defineConfig({
	plugins: [
		sveltekit(),
		paraglide({
			project: './project.inlang',
			outdir: './src/translations',
		}),
		UnoCSS({
			extractors: [extractorSvelte()],
		}),
		VitePWA({
			registerType: 'autoUpdate',
			devOptions: {
				enabled: true,
			},
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
