import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent }) => {
	const { dbPromise } = await parent();
	// Here we make a tradeoff: we need the PGLite db to query the local db for the project
	// but this blocks the rendering of layout.svelte loading spinner.
	// If the user visits the home page, they see the spinner when PGLite is loading.
	// But if they go straight to a project detail page, they will see a white screen
	// until all content is loaded (due to `await dbPromise`).
	// The good thing is, if they have visited the site at least once,
	// then the load should be reasonable quick using cached content.
	const db = await dbPromise;
	return { db };
};
