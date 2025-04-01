<script lang="ts">
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
	class={`hover:bg-[#FFEDED] hover:shadow-xl duration-500 rounded-lg bg-white p-4 cursor-pointer`}
>
	<div class="flex flex-col justify-between h-full">
		<div>
			{#if !project.organisation_logo}
				<img src={project.organisation_logo} class="h-7 max-h-7" alt="organization logo" />
			{:else}
				<img src={OsmLogo} class="h-7 max-h-7" alt="default organization logo" />
			{/if}
			<div class="my-3">
				<p class="text-[0.75rem] leading-[0.9rem] font-semibold text-[#706E6E] mb-1">
					ID: #{project.id}
				</p>
				<p
					class="capitalize text-[0.75rem] leading-normal font-normal line-clamp-1 text-[#7A7676]"
					title={project?.location_str}
				>
					{project?.location_str || '-'}
				</p>
			</div>

			<div>
				<p
					class="text-[0.875rem] leading-normal font-semibold text-[#090909] line-clamp-1 capitalize mb-1"
					title={project.name}
				>
					{project.name}
				</p>
				<p
					class="text-[0.875rem] leading-normal font-normal capitalize line-clamp-3 text-[#2B2B2B] min-h-[3.2rem]"
					title={project.short_description}
				>
					{project.short_description}
				</p>
			</div>
		</div>
	</div>
</div>
