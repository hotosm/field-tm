<script lang="ts">
	import '$styles/page.css';

	type taskStatusesType = { status: string; color: string };
	type Props = {
		isOpen: boolean;
	};
	const { isOpen }: Props = $props();

	const taskStatuses: taskStatusesType[] = [
		{ status: 'Ready', color: '#9c9a9a' },
		{ status: 'Opened in ODK', color: '#fae15f' },
		{ status: 'Survey Submitted', color: '#71bf86' },
		{ status: 'Marked Bad', color: '#fa1100' },
	];
</script>

<div class={`${isOpen ? 'flex' : 'hidden'} flex-col gap-2`}>
	<p class="font-semibold leading-0 text-lg mb-3">Legend (Features)</p>
	{#each taskStatuses as taskStatus}
		<div class="flex items-center gap-2">
			<div
				style="background-color: {taskStatus.color};"
				class="w-5 h-5 opacity-40 border-solid border-[1px] border-[#D0D0D0]"
			></div>
			<p class="font-regular text-[#494949] text-nowrap leading-0">{taskStatus?.status}</p>
		</div>
	{/each}
</div>
