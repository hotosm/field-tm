<script lang="ts">
	import type { ProjectData } from '$lib/types';
	import '$styles/offline.css';
	import { m } from '$translations/messages.js';
	import Basemaps from './basemaps.svelte';
	import FgbExtract from './fgb-extract.svelte';
	import OfflineData from './offline-data.svelte';

	type stackType = '' | 'basemaps' | 'fgb-extract' | 'offline-data';

	type stackGroupType = {
		id: stackType;
		title: string;
	};

	interface Props {
		projectId: number;
		project: ProjectData;
	}

	const stackGroup: stackGroupType[] = [
		{ id: 'basemaps', title: m['offline.basemaps']() },
		{ id: 'fgb-extract', title: m['offline.features']() },
		{ id: 'offline-data', title: m['offline.data']() },
	];

	const { projectId, project }: Props = $props();

	let activeStack: stackType = $state('');
	let activeStackTitle: string = $state('');
</script>

<div class="offline">
	<!-- header -->
	{#if activeStack !== ''}
		<div class="active-stack-header">
			<hot-icon
				name="chevron-left"
				class="icon"
				onclick={() => {
					activeStack = '';
					activeStackTitle = '';
				}}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						activeStack = '';
						activeStackTitle = '';
					}
				}}
				tabindex="0"
				role="button"
			></hot-icon>
			<p class="title">{activeStackTitle}</p>
		</div>
	{/if}

	<!-- stacks -->
	{#if activeStack === ''}
		{#each stackGroup as stack}
			<div
				class="stack"
				onclick={() => {
					activeStack = stack.id;
					activeStackTitle = stack.title;
				}}
				onkeydown={(e) => {
					if (e.key === 'Enter') {
						activeStack = stack.id;
						activeStackTitle = stack.title;
					}
				}}
				tabindex="0"
				role="button"
			>
				<div class="icon-title">
					<p>{stack.title}</p>
				</div>
				<hot-icon name="chevron-right" class="icon-next"></hot-icon>
			</div>
		{/each}
	{:else if activeStack === 'basemaps'}
		<Basemaps projectId={projectId}></Basemaps>
	{:else if activeStack === 'fgb-extract'}
		<FgbExtract {projectId} extract_url={project.data_extract_url} />
	{:else if activeStack === 'offline-data'}
		<OfflineData />
	{/if}
</div>
