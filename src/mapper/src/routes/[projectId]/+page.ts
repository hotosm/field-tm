import { error } from '@sveltejs/kit';
import type { PageLoad } from '../$types';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	// const { db } = await parent();

	const userResponse = await fetch(`${API_URL}/auth/refresh`, { credentials: 'include' });
	if (userResponse.status === 401) {
		// TODO redirect to different error page to handle login
		throw error(401, { message: `You must log in first` });
	}
	const userObj = await userResponse.json();

	const { projectId } = params;
	const projectResponse = await fetch(`${API_URL}/projects/${projectId}`, { credentials: 'include' });
	if (projectResponse.status === 401) {
		// TODO redirect to different error page to handle login
		throw error(401, { message: `You must log in first` });
	}
	if (projectResponse.status === 404) {
		throw error(404, { message: `Project with ID (${projectId}) not found` });
	}

	return {
		project: await projectResponse.json(),
		projectId: parseInt(projectId),
		userId: userObj.id,
		// db: db,
	};
};
