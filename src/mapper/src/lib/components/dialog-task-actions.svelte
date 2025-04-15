<script lang="ts">
	import '$styles/dialog-task-actions.css';
	import { m } from "$translations/messages.js";
	import { mapTask, finishTask, resetTask } from '$lib/db/events';
	import type { ProjectData } from '$lib/types';
	import { getTaskStore } from '$store/tasks.svelte.ts';

	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: ProjectData;
		clickMapNewFeature: () => void;
	};

	const taskStore = getTaskStore();
	let { isTaskActionModalOpen, toggleTaskActionModal, selectedTab, projectData, clickMapNewFeature }: Props = $props();
</script>

{#if taskStore.selectedTaskId && selectedTab === 'map' && isTaskActionModalOpen && (taskStore.selectedTaskState === 'UNLOCKED_TO_MAP' || taskStore.selectedTaskState === 'LOCKED_FOR_MAPPING')}
	<div class="dialog-task-actions">
		<div class="content">
			<div class="icon">
				<hot-icon
					name="close"
					onclick={() => toggleTaskActionModal(false)}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							toggleTaskActionModal(false);
						}
					}}
					role="button"
					tabindex="0"
				></hot-icon>
			</div>
			<div class="dialog-task-new-feature">
				<p class="task-index">{m['popup.task']()} #{taskStore.selectedTaskIndex}</p>
				<div
					onclick={() => {
						clickMapNewFeature();
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							clickMapNewFeature();
						}
					}}
					role="button"
					tabindex="0"
					class="icon"
				>
					<hot-icon
						name="new-window"
					></hot-icon>
					<p class="action">{m['popup.map_new_feature']()}</p>
				</div>
			</div>

			{#if taskStore.selectedTaskState === 'UNLOCKED_TO_MAP'}
				<p class="unlock-selected">{m['popup.start_mapping_task']({taskId: taskStore.selectedTaskIndex})}</p>
				<div class="unlock-actions">
					<sl-button
						size="small"
						variant="default"
						class="secondary"
						onclick={() => toggleTaskActionModal(false)}
						outline
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								toggleTaskActionModal(false);
							}
						}}
						role="button"
						tabindex="0"
					>
						<span>{m['popup.cancel']()}</span>
					</sl-button>
					<sl-button
						variant="primary"
						size="small"
						onclick={() => {
							if (taskStore.selectedTaskId) mapTask(projectData?.id, taskStore.selectedTaskId);
						}}
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								if (taskStore.selectedTaskId) mapTask(projectData?.id, taskStore.selectedTaskId);
							}
						}}
						role="button"
						tabindex="0"
					>
						<hot-icon slot="prefix" name="location"
						></hot-icon>
						<span>{m['popup.start_mapping']()}</span>
					</sl-button>
				</div>
			{:else if taskStore.selectedTaskState === 'LOCKED_FOR_MAPPING'}
				<p class="lock-selected">{m['dialog_task_actions.task']()} #{taskStore.selectedTaskIndex} {m['dialog_task_actions.locked_is_complete']()} </p>
				<div class="lock-actions">
					<sl-button
						onclick={() => {
							if (taskStore.selectedTaskId) resetTask(projectData?.id, taskStore.selectedTaskId);
						}}
						variant="default"
						outline
						size="small"
						class="secondary"
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								if (taskStore.selectedTaskId) resetTask(projectData?.id, taskStore.selectedTaskId);
							}
						}}
						role="button"
						tabindex="0"
					>
						<hot-icon
							slot="prefix"
							name="close"
						></hot-icon>
						<span>{m['popup.cancel_mapping']()}</span>
					</sl-button>
					<sl-button
						onclick={() => {
							if (taskStore.selectedTaskId) finishTask(projectData?.id, taskStore.selectedTaskId);
						}}
						variant="default"
						size="small"
						class="green"
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								if (taskStore.selectedTaskId) finishTask(projectData?.id, taskStore.selectedTaskId);
							}
						}}
						role="button"
						tabindex="0"
					>
						<hot-icon slot="prefix" name="check"></hot-icon>
						<span>{m['dialog_task_actions.complete_mapping']()}</span>
					</sl-button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style></style>
