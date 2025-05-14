import { PGlite } from '@electric-sql/pglite';
import { online } from 'svelte/reactivity/window';

import type { projectType, paginationType } from '$lib/types';
import { getAlertStore } from '$store/common.svelte';
import { applyDataToTableWithCsvCopy } from '$lib/db/helpers';
import { m } from '$translations/messages.js';

const API_URL = import.meta.env.VITE_API_URL;

const alertStore = getAlertStore();

let projectList = $state<projectType[]>([]);
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
	async function fetchProjectsFromAPI(db: PGlite, page: number, search: string) {
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
			const projectResponse = (await response.json()) as { results: projectType[]; pagination: paginationType };
			projectList = projectResponse.results;
			projectPagination = projectResponse.pagination;
			await createLocalProjectSummaries(db, projectResponse.results);
		} catch (error: any) {
			alertStore.setAlert({ message: error || 'Unable to fetch projects', variant: 'danger' });
		} finally {
			projectListLoading = false;
		}
	}

	function _parseProjectList(projects: projectType[]): projectType[] {
		return projects.map((project) => ({
			id: project.id,
			name: project.name,
			short_description: project.short_description,
			organisation_logo: project.organisation_logo,
			priority: project.priority,
			location_str: project.location_str,
			hashtags: project.hashtags,
		}));
	}

	async function createLocalProjectSummaries(db: PGlite, apiProject: projectType[]): Promise<void> {
		if (!db) return;

		// We only actually need a minimal number of fields for the project summaries
		// (the project details are updated when a specific project is loaded via API)
		const dataObj = _parseProjectList(apiProject);

		// Clear local db table and populate with latest search results
		await db.query(`DELETE FROM projects;`);
		await applyDataToTableWithCsvCopy(db, 'projects', dataObj);
	}

	async function fetchProjectsFromLocalDB(db: PGlite): Promise<void> {
		if (!db) return;

		const localProjects = await db.query(`SELECT * FROM projects;`);
		projectList = _parseProjectList(localProjects?.rows);
	}

	return {
		fetchProjectsFromAPI,
		fetchProjectsFromLocalDB,
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
