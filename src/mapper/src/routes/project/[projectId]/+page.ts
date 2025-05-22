import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { online } from 'svelte/reactivity/window';
import type { DbProjectType } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	const { dbPromise } = await parent();
	const { projectId } = params;
	let project: DbProjectType | undefined;

	if (online.current) {
		const res = await fetch(`${API_URL}/projects/${projectId}/minimal`, {
			credentials: 'include',
		});

		if (res.status === 401) throw error(401, 'You must log in first');
		if (res.status === 403) throw error(403, `Access denied to project ${projectId}`);
		if (res.status === 404) throw error(404, `Project ${projectId} not found`);
		if (res.status === 400) throw error(400, `Invalid project ID ${projectId}`);
		if (res.status >= 300) throw error(400, `Unknown error retrieving project ${projectId}`);

		project = await res.json();
	}

	return {
		project,
		projectId: parseInt(projectId),
		dbPromise,
	};
};
