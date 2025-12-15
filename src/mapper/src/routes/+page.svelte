<script lang="ts">
	import '$styles/page.css';
	import { onMount } from 'svelte';
	import type { SlInputEvent } from '@shoelace-style/shoelace';

	import { goto } from '$app/navigation';
	import { m } from '$translations/messages.js';
	import { getProjectStore } from '$store/projects.svelte';
	import Pagination from '$lib/components/pagination.svelte';
	import ProjectCard from '$lib/components/project-summary/project-card.svelte';
	import ProjectCardSkeleton from '$lib/components/project-summary/project-card-skeleton.svelte';

	const projectStore = getProjectStore();

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

	function getPaginatedProjects() {
		projectStore.fetchProjectsFromAPI(paginationPage, debouncedSearch);
	}

	onMount(async () => {
		// if requestedPath set, redirect to the desired path (in our case we have requestedPath set to invite url)
		const requestedPath = sessionStorage.getItem('requestedPath');
		if (requestedPath) {
			goto(requestedPath);
			sessionStorage.removeItem('requestedPath');
		}
		// Get the project summaries on load
		getPaginatedProjects();
	});
</script>

<div class=" h-full overflow-y-hidden bg-[#f5f5f5]">
	<div class="px-4 h-[calc(100%-85px)] sm:h-[calc(100%-60px)] flex flex-col">
		<div class="flex items-center justify-between my-2">
			<h5 class="m-0">{m['common.projects']()}</h5>
			<sl-input
				placeholder="Search"
				size="small"
				onsl-input={(e: SlInputEvent) => {
					search = e?.target?.value;
				}}><sl-icon name="search" slot="prefix"></sl-icon></sl-input
			>
		</div>
		<div
			class="overflow-y-scroll grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:fmtm-grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3 pb-2"
		>
			{#if projectStore.projectListLoading}
				{#each Array.from({ length: 12 }) as itr}
					<ProjectCardSkeleton />
				{/each}
			{:else if projectStore.projectList?.length === 0}
				<div>No projects found</div>
			{:else}
				{#each projectStore.projectList as project}
					<ProjectCard {project} />
				{/each}
			{/if}
		</div>
	</div>
	<Pagination
		showing={projectStore.projectList?.length}
		totalCount={projectStore.projectPagination?.total || 0}
		currentPage={projectStore.projectPagination?.page || 0}
		isLoading={projectStore.projectListLoading}
		pageSize={projectStore.projectPagination?.per_page}
		handlePageChange={(page) => {
			paginationPage = page;
			getPaginatedProjects();
		}}
		className="fixed left-0 w-full shadow-2xl"
	/>
</div>
