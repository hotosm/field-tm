<script lang="ts">
	import '$styles/my-tasks.css';
	import { taskStatus } from '$constants/enums';
	import { getLoginStore } from '$store/login.svelte';
	import { getTaskStore } from '$store/tasks.svelte';
	import { m } from '$translations/messages';

	type Props = {
		zoomToTask: (taskId: number) => void;
	};

	const { zoomToTask }: Props = $props();

	const taskStore = getTaskStore();
	const loginStore = getLoginStore();

	const authDetails = $derived(loginStore.getAuthDetails);
	const latestTaskEvent = $derived(taskStore.latestTaskEvent);
	const myTasks = $derived(
		latestTaskEvent?.filter(
			(task) => task.actioned_by_uid === authDetails?.sub && task.state === taskStatus.LOCKED_FOR_MAPPING,
		),
	);
</script>

<div class="my-tasks">
	<h3>{m['stack_group.my_tasks']()}</h3>
	<div class="tasks">
		{#if myTasks?.length === 0}
			<p class="no-tasks">{m['my_tasks.no_tasks_assigned']()}</p>
		{/if}
		{#each myTasks as task}
			<div class="task-card">
				<div class="task-index">{m['popup.task']()} #{task.task_index}</div>
				<sl-button
					variant="default"
					size="small"
					onclick={() => zoomToTask(task.id)}
					onkeydown={() => zoomToTask(task.id)}
					role="button"
					tabindex="0">{m['common.zoom_to_task']()} <hot-icon slot="prefix" name="map"></hot-icon></sl-button
				>
			</div>
		{/each}
	</div>
</div>
