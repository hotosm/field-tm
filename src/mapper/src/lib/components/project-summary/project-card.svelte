<script lang="ts">
	import '$styles/project-summary.css';
	import type { DbProjectType } from '$lib/types';
	import OsmLogo from '$assets/images/osm-logo.png';
	import { goto } from '$app/navigation';
	import { m } from '$translations/messages.js';
	import { projectStatus } from '$constants/enums';

	type propType = {
		project: DbProjectType;
	};

	const { project }: propType = $props();
</script>

<div
	onclick={() => goto(`/project/${project.id}`)}
	onkeydown={(e: KeyboardEvent) => {
		if (e.key === 'Enter') goto(`/project/${project.id}`);
	}}
	role="button"
	tabindex="0"
	class="project-card"
>
	<div class="content">
		<div>
			<div class="meta0">
				{#if project.organisation_logo}
					<img src={project.organisation_logo} class="logo" alt="organization logo" />
				{:else}
					<img src={OsmLogo} class="logo" alt="default organization logo" />
				{/if}
				{#if projectStatus.COMPLETED === project.status}
					<span class={`project-status ${project.status}`}>{m[`project_states.${project.status}`]()}</span>
				{/if}
			</div>
			<div class="meta1">
				<p class="project-id">
					ID: #{project.id}
				</p>
				<p class="project-location" title={project?.location_str}>
					{project?.location_str || '-'}
				</p>
			</div>

			<div class="meta2">
				<p class="project-name" title={project.name}>
					{project.name}
				</p>
				<p class="project-short-desc" title={project.short_description}>
					{project.short_description}
				</p>
			</div>
		</div>
	</div>
</div>
