<script lang="ts">
	import type { ProjectData } from '$lib/types';
	import '$styles/offline.css';
	import { m } from '$translations/messages.js';
	import Basemaps from './basemaps.svelte';
	import FgbExtract from './fgb-extract.svelte';

	type stackType = '' | 'basemaps' | 'fgb-extract';

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
	];

	const { projectId, project }: Props = $props();

	let activeStack: stackType = $state('');
	let activeStackTitle: string = $state('');
</script>

<div class="offline">
	<!-- header -->
	{#if activeStack !== ''}
		<div class="active-stack-header">
			<sl-icon
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
			></sl-icon>
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
				<sl-icon name="chevron-right" class="icon-next"></sl-icon>
			</div>
		{/each}
	{:else if activeStack === 'basemaps'}
		<Basemaps {projectId}></Basemaps>
	{:else if activeStack === 'fgb-extract'}
		<FgbExtract {projectId} extract_url={project.data_extract_url} />
	{/if}
</div>
