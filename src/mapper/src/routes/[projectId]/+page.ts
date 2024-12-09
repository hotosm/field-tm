import { error } from '@sveltejs/kit';
import type { PageLoad } from '../$types';
import { getLoginStore } from '$store/login.svelte.ts';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	// const { db } = await parent();
	const { projectId } = params;
	const loginStore = getLoginStore();

	/*
	Login + user details
	*/
	const userResponse = await fetch(`${API_URL}/auth/refresh/mapper`, { credentials: 'include' });
	if (userResponse.status === 401) {
		// TODO redirect to different error page to handle login
		loginStore.signOut();
		throw error(401, { message: `You must log in first` });
	}
	const userObj = await userResponse.json();

	/*
	Project details
	*/
	const projectResponse = await fetch(`${API_URL}/projects/${projectId}`, { credentials: 'include' });
	if (projectResponse.status === 401) {
		// TODO redirect to different error page to handle login
		throw error(401, { message: `You must log in first` });
	}
	if (projectResponse.status === 404) {
		throw error(404, { message: `Project with ID (${projectId}) not found` });
	}
	const entityStatusResponse = await fetch(`${API_URL}/projects/${projectId}/entities/statuses`, {
		credentials: 'include',
	});

	/*
	Basemaps
	*/
	// Load existing OPFS PMTiles archive if present
	// TODO

	return {
		project: await projectResponse.json(),
		projectId: parseInt(projectId),
		userId: userObj.id,
		entityStatus: await entityStatusResponse.json(),
		// db: db,
	};
};
