import path from 'path';
import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';
import UnoCSS from 'unocss/vite';
import extractorSvelte from '@unocss/extractor-svelte';

export default defineConfig({
	plugins: [
		sveltekit(),
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
			$static: path.resolve('./static'),
			$store: path.resolve('./src/store'),
			$routes: path.resolve('./src/routes'),
			$styles: path.resolve('./src/styles'),
			$assets: path.resolve('./src/assets'),
			$constants: path.resolve('./src/constants'),
		},
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
	},
	optimizeDeps: {
		exclude: ['@electric-sql/pglite'],
	},
});
