<script lang="ts">
	import '$styles/project-summary.css';
	import type { projectType } from '$lib/types';
	import OsmLogo from '$assets/images/osm-logo.png';
	import { goto } from '$app/navigation';

	type propType = {
		project: projectType;
	};

	const { project }: propType = $props();
</script>

<div
	onclick={() => goto(`/${project.id}`)}
	onkeydown={(e: KeyboardEvent) => {
		if (e.key === 'Enter') goto(`/${project.id}`);
	}}
	role="button"
	tabindex="0"
	class="project-card"
>
	<div class="content">
		<div>
			{#if !project.organisation_logo}
				<img src={project.organisation_logo} class="logo" alt="organization logo" />
			{:else}
				<img src={OsmLogo} class="logo" alt="default organization logo" />
			{/if}
			<div class="meta1">
				<p class="project-id">
					ID: #{project.id}
				</p>
				<p
					class="project-location"
					title={project?.location_str}
				>
					{project?.location_str || '-'}
				</p>
			</div>

			<div class="meta2">
				<p
					class="project-name"
					title={project.name}
				>
					{project.name}
				</p>
				<p
					class="project-short-desc"
					title={project.short_description}
				>
					{project.short_description}
				</p>
			</div>
		</div>
	</div>
</div>
