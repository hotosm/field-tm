
<script lang="ts">
	import '$styles/project-info.css';
	import { m } from "$translations/messages.js";

	type descriptionType = {
		key: string;
		value: string;
	};

	const { projectData } = $props();

	const descriptionList: descriptionType[] = [
		{ key: m['project_info.project_id'](), value: projectData?.id },
		{ key: m['project_info.total_tasks'](), value: projectData?.tasks?.length },
		{ key: m['project_info.organization_name'](), value: projectData?.organisation_name },
	];
</script>

<h5 class="project-info-name">{projectData?.name}</h5>
<div class="project-info">
	<h5 class="description-title">{m['project_info.description']()}</h5>
	<p class="description">{projectData?.description}</p>
	<div class="description-list">
		{#each descriptionList as description}
			<div class="description-item">
				<p class="description-key">{description.key}</p>
				<p class="description-value">
					<span>:</span>
					{description?.value || '-'}
				</p>
			</div>
		{/each}
	</div>
</div>
