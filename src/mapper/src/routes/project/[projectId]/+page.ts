import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { online } from 'svelte/reactivity/window';
import { DbProject } from '$lib/db/projects.ts';
import type { DbProjectType } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	const { dbPromise } = await parent();
	// Here we make a tradeoff: we need the PGLite db to query the local db for the project
	// but this blocks the rendering of layout.svelte loading spinner.
	// If the user visits the home page, they see the spinner when PGLite is loading.
	// But if they go straight to a project detail page, they will see a white screen
	// until all content is loaded (due to `await dbPromise`).
	// The good thing is, if they have visited the site at least once (even the home page),
	// then the load should be reasonable quick using cached content.
	const db = await dbPromise;

	const { projectId } = params;
	let project: DbProjectType | undefined;

	if (!online.current) {
		project = await DbProject.one(db, projectId);

		if (!project) {
			throw error(404, `Project with ID (${projectId}) not found in local storage`);
		}
	} else {
		const res = await fetch(`${API_URL}/projects/${projectId}/minimal`, {
			credentials: 'include',
		});

		if (res.status === 401) throw error(401, 'You must log in first');
		if (res.status === 403) throw error(403, `Access denied to project ${projectId}`);
		if (res.status === 404) throw error(404, `Project ${projectId} not found`);
		if (res.status === 400) throw error(400, `Invalid project ID ${projectId}`);
		if (res.status >= 300) throw error(400, `Unknown error retrieving project ${projectId}`);

		project = await res.json();

		if (!project) return;
		// Ensure the local database has the extra metadata needed
		await DbProject.upsert(db, project);
	}

	return {
		project,
		projectId: parseInt(projectId),
		db,
	};
};
