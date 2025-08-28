<script lang="ts">
	import '$styles/activities.css';
	import type { TaskEventType } from '$lib/types';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { m } from '$translations/messages.js';

	interface Props {
		taskEvents: TaskEventType[];
		zoomToTask: (taskId: number) => void;
	}

	let { taskEvents, zoomToTask }: Props = $props();

	const taskStore = getTaskStore();
	const taskIdIndexMap: Record<number, number> = taskStore.taskIdIndexMap;
</script>

<div class="activities">
	{#if taskEvents?.length === 0}
		<div class="header">
			<p>
				{taskStore?.selectedTaskIndex
					? `${m['activities.no_activities_on_task_yet']()} ${taskStore?.selectedTaskIndex}`
					: m['activities.no_activities_yet']()}
			</p>
		</div>
	{:else}
		{#each taskEvents as event (event?.event_id)}
			<div class="event">
				<div class="event-content">
					<sl-icon name="person-fill" style="border: 1px solid" class="icon"></sl-icon>
					<div class="detail">
						<p class="username">{event?.username}</p>
						<div class="meta">
							<p class="task-id">#{taskIdIndexMap[event?.task_id]}</p>
							<div class="history">
								<sl-icon name="clock-history" class="icon"></sl-icon>
								<p class="created-at">
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
				<div class="event-more">
					<p class="username">
						<span class="capitalize">{event?.username}</span>
						{m['activities.update_status_to']()} <span>{event?.state}</span>
					</p>
					<sl-icon
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
						class="icon"
					></sl-icon>
				</div>
			</div>
		{/each}
	{/if}
</div>
