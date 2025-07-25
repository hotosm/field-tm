import 'virtual:uno.css';
import type { LayoutLoad } from './$types';

import { clearAllDevCaches } from '$lib/utils/dev-reset';

// NOTE we can't prerender as we are using dynamic routing [projectId]
export const prerender = false;
export const ssr = false;

export const load: LayoutLoad = async ({ fetch }) => {
	let config;

	try {
		const s3Response = await fetch(`${import.meta.env.VITE_S3_URL}/fmtm-data/frontend/config.json`);
		if (s3Response.ok) {
			config = await s3Response.json();
		} else {
			throw new Error('S3 config fetch failed');
		}
	} catch (error) {
		console.warn('Falling back to local config:', error);
		const localResponse = await fetch('/config.json');
		config = await localResponse.json();
	}

	if (import.meta.env.DEV) {
		// We need this because we have pretty aggressive caching for offline mode
		await clearAllDevCaches();
	}

	return {
		config,
	};
};
