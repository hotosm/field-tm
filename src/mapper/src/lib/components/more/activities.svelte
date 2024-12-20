<script lang="ts">
	import ActivitiesSkeleton from '$lib/components/more/skeleton/activities.svelte';
	import type { TaskEventType } from '$lib/types';
	import { getTaskStore } from '$store/tasks.svelte.ts';

	interface Props {
		taskEvents: TaskEventType[];
		zoomToTask: (taskId: number) => void;
	}

	let { taskEvents, zoomToTask }: Props = $props();

	const taskStore = getTaskStore();
	const taskIdIndexMap: Record<number, number> = taskStore.taskIdIndexMap;
</script>

<div class="overflow-y-scroll overflow-x-hidden flex flex-col gap-2 pb-2">
	{#if false}
		{#each Array.from({ length: 5 }) as _, index}
			<ActivitiesSkeleton />
		{/each}
	{:else if taskEvents?.length === 0}
		<div class="flex justify-center mt-10">
			<p class="text-[#484848] text-base">
				{taskStore?.selectedTaskIndex
					? `No activities yet on task ${taskStore?.selectedTaskIndex}`
					: 'No activities yet'}
			</p>
		</div>
	{:else}
		{#each taskEvents as event}
			<div class="flex flex-col gap-2 py-3 bg-[#F6F5F5] rounded-md mr-1">
				<div class="flex gap-4 px-3">
					<hot-icon
						name="person-fill"
						style="border: 1px solid"
						class="!text-[1.7rem] text-red-600 cursor-pointer duration-200 rounded-full p-[2px] bg-white"
					></hot-icon>
					<div class="flex flex-col gap-1 flex-1">
						<p class="font-semibold capitalize">{event?.username}</p>
						<div class="flex items-center justify-between">
							<p class="text-[#484848] text-sm">#{taskIdIndexMap[event?.task_id]}</p>
							<div class="flex items-center gap-2">
								<hot-icon name="clock-history" class="!text-[1rem] text-red-600 cursor-pointer duration-200"></hot-icon>
								<p class="text-[#484848] text-sm">
									<span>
										{event?.created_at?.split(' ')[0]}
									</span>
									<span>
										{event?.created_at?.split(' ')[1]?.split('.')[0]}
									</span>
								</p>
							</div>
						</div>
					</div>
				</div>
				<div class="px-3 flex items-center fmtm-justify-between gap-2">
					<p class="font-normal text-[#484848] flex-1">
						<span class="capitalize">{event?.username}</span> updated status to <span>{event?.state}</span>
					</p>
					<hot-icon
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								zoomToTask(event?.task_id);
							}
						}}
						role="button"
						tabindex="0"
						onclick={() => {
							zoomToTask(event?.task_id);
						}}
						name="map"
						class="!text-[1rem] text-[#484848] hover:text-red-600 cursor-pointer duration-200"
					></hot-icon>
				</div>
			</div>
		{/each}
	{/if}
</div>
