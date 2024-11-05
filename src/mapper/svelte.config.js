import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto for a list.
		// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
		// See https://kit.svelte.dev/docs/adapters for more information about adapters.
		adapter: adapter({
			// default options are shown. On some platforms
			// these options are set automatically — see below
			pages: 'build',
			assets: 'build',
			// This fallback is required to compile as SPA
			// as we don't have any server side rendering here
			fallback: 'index.html',
			precompress: false,
			strict: true,
		}),
		// Works in conjunction with reverse proxy to serve under /mapnow prefix
		paths: {
			base: '/mapnow',
		},
	},

	alias: {
		$lib: 'src/lib',
		$components: 'src/components',
		$static: 'static',
		$store: 'src/store',
		$routes: 'src/routes',
		$styles: 'styles',
		$assets: 'assets',
	},
};

export default config;
