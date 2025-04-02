<script lang="ts">
	import '$styles/page.css';
	import { m } from "$translations/messages.js";

	type taskStatusesType = { status: string; color: string };
	type Props = {
		isOpen: boolean;
	};
	const { isOpen }: Props = $props();

	const taskStatuses: taskStatusesType[] = [
		{ status: m['entity_states.READY'](), color: '#9c9a9a' },
		{ status: m['entity_states.OPENED_IN_ODK'](), color: '#fae15f' },
		{ status: m['entity_states.SURVEY_SUBMITTED'](), color: '#71bf86' },
		{ status: m['entity_states.MARKED_BAD'](), color: '#fa1100' },
	];
</script>

<div class={`${isOpen ? 'flex' : 'hidden'} flex-col gap-2`}>
	<p class="font-semibold leading-0 text-lg mb-3">{m['legend.features']()}</p>
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
