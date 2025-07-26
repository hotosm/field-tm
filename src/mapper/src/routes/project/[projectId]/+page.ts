import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { online } from 'svelte/reactivity/window';
import type { Collection } from '@tanstack/svelte-db';
import type { DbProjectType } from '$lib/types';
import { getEntitiesCollection, getTaskEventsCollection } from '$store/collections';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	const { projectId } = params;
	let project: DbProjectType;
	let eventsCollection: Collection;
	let entitiesCollection: Collection;

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
		entitiesCollection = await getEntitiesCollection(projectId);
		entitiesCollection.preload();
		eventsCollection = await getTaskEventsCollection(projectId);
		eventsCollection.preload();
	} else {
		throw error(500, `You must be online to fetch project data`);
	}

	return {
		projectId: parseInt(projectId),
		project,
		entitiesCollection,
		eventsCollection,
	};
};
