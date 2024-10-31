<script>
	import ActivitiesSkeleton from '$lib/components/more/skeleton/activities.svelte';
</script>

<div class="overflow-y-scroll overflow-x-hidden flex flex-col gap-2 pb-2">
	{#if false}
		{#each Array.from({ length: 5 }) as _, index}
			<ActivitiesSkeleton />
		{/each}
	{:else}
		{#each Array.from({ length: 5 }) as _, index}
			<div class="flex flex-col gap-2 py-3 bg-[#F6F5F5] rounded-md mr-1">
				<div class="flex gap-4 px-3">
					<hot-icon
						name="person-fill"
						style="border: 1px solid"
						class="!text-[1.7rem] text-red-600 cursor-pointer duration-200 rounded-full p-[2px] bg-white"
					></hot-icon>
					<div class="flex flex-col gap-1 flex-1">
						<p class="font-semibold">Localadmin</p>
						<div class="flex items-center justify-between">
							<p class="text-[#484848] text-sm">#2</p>
							<div class="flex items-center gap-2">
								<hot-icon name="clock-history" class="!text-[1rem] text-red-600 cursor-pointer duration-200"></hot-icon>
								<p class="text-[#484848] text-sm">2024-10-21 11:42</p>
							</div>
						</div>
					</div>
				</div>
				<div class="px-3 flex items-center fmtm-justify-between gap-2">
					<p class="font-normal text-[#484848] flex-1">
						<span class="">svcfmtm</span> updated status to <span>MAPPED</span>
					</p>
					<hot-icon name="map" class="!text-[1rem] text-[#484848] hover:text-red-600 cursor-pointer duration-200"
					></hot-icon>
				</div>
			</div>
		{/each}
	{/if}
</div>

<style></style>
