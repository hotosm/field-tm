<script lang="ts">
	import { clickOutside } from '$lib/utils/clickOutside.ts';
	import LockImg from '$assets/images/black-lock.png';
	import '$styles/page.css';

	type taskStatusesType = { status: string; color?: string; icon?: string };

	let isOpen = false;

	const taskStatuses: taskStatusesType[] = [
		{ status: 'Ready', color: '#ffffff' },
		{ status: 'Locked For Mapping', color: '#008099' },
		{ status: 'Ready For Validation', color: '#ade6ef' },
		{ status: 'Locked For Validation', color: '#fceca4' },
		{ status: 'Validated', color: '#40ac8c' },
		{ status: 'More Mapping Needed', color: '#d73f3e' },
		{ status: 'Locked', icon: LockImg },
	];
</script>

<div use:clickOutside on:click_outside={() => (isOpen = false)} class="relative">
	<div class="group absolute bottom-0 right-0 text-nowrap cursor-pointer" on:click={() => (isOpen = !isOpen)}>
		<hot-icon
			style="border: 1px solid #D7D7D7;"
			name="legend-toggle"
			class={`!text-[1.7rem] text-[#333333] bg-white p-2 rounded-full group-hover:text-red-600 duration-200 ${isOpen && 'text-red-600'}`}
		></hot-icon>
	</div>
	<div
		class={`absolute bottom-0 right-14 bg-white rounded-md p-4 duration-200 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'} overflow-hidden flex flex-col gap-2`}
	>
		<p class="font-barlow-semibold leading-0 text-xl">Legend</p>
		{#each taskStatuses as taskStatus}
			<div class="flex items-center gap-2">
				{#if !taskStatus.color}
					<div class="w-5 h-5 flex justify-center">
						<img src={taskStatus.icon} class="w-4" />
					</div>
				{:else}
					<div style="background-color: {taskStatus.color}; border: 1px solid #D0D0D0;" class={`w-5 h-5 opacity-40`} />
				{/if}
				<p class="font-barlow-regular text-[#494949] text-nowrap leading-0">{taskStatus?.status}</p>
			</div>
		{/each}
	</div>
</div>

<style></style>
