import { error } from '@sveltejs/kit';
import type { PageLoad } from '../$types';

const API_URL = import.meta.env.VITE_API_URL;

export const load: PageLoad = async ({ parent, params, fetch }) => {
	// const { db } = await parent();

	const { projectId } = params;
	const project = await fetch(`${API_URL}/projects/${projectId}`);

	if (project.status == 404) {
		error(404, {
			message: `Project with ID (${projectId}) not found`,
		});
	}

	const user = await fetch(`${API_URL}/auth/refresh`, { credentials: 'include' });
	if (user.status != 200) {
		// TODO redirect to different error page to handle login
		error(401, {
			message: `You must log in first`,
		});
	}
	const userObj = await user.json();

	return {
		project: await project.json(),
		projectId: parseInt(projectId),
		userId: userObj.id,
		// db: db,
	};
};
