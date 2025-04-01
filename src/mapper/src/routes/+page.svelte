<script lang="ts">
	import '$styles/page.css';
	import { getAlertStore } from '$store/common.svelte';
	import Pagination from '$lib/components/pagination.svelte';
	import ProjectCard from '$lib/components/project-summary/project-card.svelte';
	import ProjectCardSkeleton from '$lib/components/project-summary/project-card-skeleton.svelte';
	import type { SlInputEvent } from '@shoelace-style/shoelace';
	import type { paginationType, projectType } from '$lib/types';

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
	let paginationPage = $state(1);
	let search = $state('');
	let debouncedSearch = $state('');

	$effect(() => {
		debouncedSearch;
		paginationPage = 1;
	});

	$effect(() => {
		search;
		const timeoutId = setTimeout(() => {
			debouncedSearch = search;
		}, 500);
		return () => clearTimeout(timeoutId);
	});

	const fetchProjects = async (page: number, search: string) => {
		try {
			projectListLoading = true;
			const response = await fetch(
				`${API_URL}/projects/summaries?page=${page}&search=${search}&results_per_page=12&minimal=true`,
			);
			const projectResponse = (await response.json()) as { results: projectType[]; pagination: paginationType };
			projectList = projectResponse.results;
			projectPagination = projectResponse.pagination;
		} catch (error: any) {
			alertStore.setAlert({ message: error || 'Unable to create entity', variant: 'danger' });
		} finally {
			projectListLoading = false;
		}
	};

	$effect(() => {
		fetchProjects(paginationPage, debouncedSearch);
	});
</script>

<div class="font-barlow h-full overflow-y-hidden bg-[#f5f5f5]">
	<div class="px-4 h-[calc(100%-85px)] sm:h-[calc(100%-60px)] flex flex-col">
		<div class="flex items-center justify-between">
			<h3>PROJECTS</h3>
			<hot-input
				placeholder="Search"
				size="small"
				onsl-input={(e: SlInputEvent) => {
					search = e?.target?.value;
				}}><sl-icon name="search" slot="prefix"></sl-icon></hot-input
			>
		</div>
		<div
			class="overflow-y-scroll grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:fmtm-grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3 pb-2"
		>
			{#if projectListLoading}
				{#each Array.from({ length: 12 }) as itr}
					<ProjectCardSkeleton />
				{/each}
			{:else if projectList?.length === 0}
				<div>No projects found</div>
			{:else}
				{#each projectList as project}
					<ProjectCard {project} />
				{/each}
			{/if}
		</div>
	</div>
	<Pagination
		showing={projectList?.length}
		totalCount={projectPagination?.total || 0}
		currentPage={projectPagination?.page || 0}
		isLoading={projectListLoading}
		pageSize={projectPagination?.per_page}
		handlePageChange={(page) => {
			paginationPage = page;
		}}
		className="fixed left-0 w-full shadow-2xl"
	/>
</div>
