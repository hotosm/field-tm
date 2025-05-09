import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	const { db } = await parent();
	const { projectId } = params;

	/*
	Project details
	*/
	const projectResponse = await fetch(`${API_URL}/projects/${projectId}/minimal`, { credentials: 'include' });
	if (projectResponse.status === 401) {
		// TODO redirect to different error page to handle login
		throw error(401, { message: `You must log in first` });
	} else if (projectResponse.status === 403) {
		throw error(403, { message: `You do not have access to project with ID (${projectId})` });
	} else if (projectResponse.status === 404) {
		throw error(404, { message: `Project with ID (${projectId}) not found` });
	} else if (projectResponse.status === 400) {
		throw error(400, { message: `Invalid project ID (${projectId}). It must be numeric` });
	} else if (projectResponse.status >= 300) {
		throw error(400, { message: `Unknown error for project (${projectId})` });
	}

	return {
		project: await projectResponse.json(),
		projectId: parseInt(projectId),
		db: db,
	};
};
