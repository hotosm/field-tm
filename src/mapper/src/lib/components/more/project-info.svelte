<script lang="ts">
	type descriptionType = {
		key: string;
		value: string;
	};

	const { projectData } = $props();

	const descriptionList: descriptionType[] = [
		{ key: 'Project ID', value: projectData?.id },
		{ key: 'Total Tasks', value: projectData?.tasks?.length },
		{ key: 'Organization Name', value: projectData?.organisation_name },
	];
</script>

<h5 class="text-lg text-[#333333] font-barlow-semibold mb-6 mt-3">{projectData?.name}</h5>
<div class="flex flex-col gap-3">
	<h5 class="text-base text-[#D73F3F] font-barlow-semibold">Description</h5>
	<p class="text-sm text-[#2B2B2B] font-barlow-regular">{projectData?.description}</p>
	<div class="flex flex-col gap-2">
		{#each descriptionList as description}
			<div class="grid grid-cols-2">
				<p class="text-sm text-[#2B2B2B] font-barlow-regular">{description.key}</p>
				<p class="text-sm text-[#161616] font-barlow-semibold">
					<span class="px-2">:</span>
					{description?.value || '-'}
				</p>
			</div>
		{/each}
	</div>
</div>
