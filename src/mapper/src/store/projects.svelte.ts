import { online } from 'svelte/reactivity/window';

import type { DbProjectType, APIProject, paginationType } from '$lib/types';
import { getAlertStore } from '$store/common.svelte';
import { m } from '$translations/messages.js';

const API_URL = import.meta.env.VITE_API_URL;

const alertStore = getAlertStore();

let projectList = $state<DbProjectType[] | null>([]);
let projectPagination = $state<paginationType>({
	has_next: false,
	has_prev: false,
	next_num: null,
	page: null,
	pages: null,
	prev_num: null,
	per_page: 12,
	total: null,
});
let projectListLoading = $state(false);

function getProjectStore() {
	async function fetchProjectsFromAPI(page: number, search: string) {
		if (!online.current) {
			alertStore.setAlert({ message: m['offline.fetch_projects_offline'](), variant: 'danger' });
			return;
		}

		try {
			projectListLoading = true;
			const response = await fetch(
				`${API_URL}/projects/summaries?page=${page}&search=${search}&results_per_page=12&minimal=true`,
				{ credentials: 'include' },
			);
			const projectResponse = (await response.json()) as { results: APIProject[]; pagination: paginationType };
			// We only actually need a minimal number of fields for the project summaries
			// (the project details are updated when a specific project is loaded via API)
			const dataObj = _parseProjectList(projectResponse.results);
			projectList = dataObj;
			projectPagination = projectResponse.pagination;
		} catch (error: any) {
			alertStore.setAlert({ message: error || 'Unable to fetch projects', variant: 'danger' });
		} finally {
			projectListLoading = false;
		}
	}

	function _parseProjectList(projects: DbProjectType[] | APIProject[]): Partial<DbProjectType>[] {
		return projects.map((project) => ({
			id: project.id,
			name: project.name,
			short_description: project.short_description,
			organisation_logo: project.organisation_logo,
			priority: project.priority,
			location_str: project.location_str,
			hashtags: project.hashtags,
			status: project.status,
		}));
	}

	return {
		fetchProjectsFromAPI,
		get projectList() {
			return projectList;
		},
		get projectPagination() {
			return projectPagination;
		},
		get projectListLoading() {
			return projectListLoading;
		},
	};
}

export { getProjectStore };
