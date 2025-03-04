import { error } from '@sveltejs/kit';
import type { PageLoad } from '../$types';
import { getLoginStore } from '$store/login.svelte.ts';
import { refreshCookies, getUserDetailsFromApi } from '$lib/utils/login';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	// const { db } = await parent();
	const { projectId } = params;
	const loginStore = getLoginStore();

	/*
	Login + user details
	*/
	let apiUser = await refreshCookies(fetch);
	if (apiUser?.username !== 'svcfmtm') {
		// Call /auth/me to populate the user details in the header
		apiUser = await getUserDetailsFromApi(fetch);
		if (!apiUser) {
			loginStore.signOut();
			throw error(401, { message: `You must log in first` });
		} else {
			loginStore.setAuthDetails(apiUser);
		}
	}

	/*
	Project details
	*/
	const projectResponse = await fetch(`${API_URL}/projects/${projectId}/minimal`, { credentials: 'include' });
	if (projectResponse.status === 401) {
		// TODO redirect to different error page to handle login
		throw error(401, { message: `You must log in first` });
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
		userId: apiUser.id,
		// db: db,
	};
};
