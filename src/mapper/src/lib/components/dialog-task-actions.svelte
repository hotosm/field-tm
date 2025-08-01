<script lang="ts">
	import '$styles/dialog-task-actions.css';
	import { m } from '$translations/messages.js';
	import { mapTask, finishTask, resetTask } from '$lib/db/events';
	import type { APIProject } from '$lib/types';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte';
	import { unicodeBold } from '$lib/utils/text.ts';
	import { projectStatus, taskStatus } from '$constants/enums';

	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: APIProject;
		clickMapNewFeature: () => void;
	};

	const taskStore = getTaskStore();
	const entitiesStore = getEntitiesStatusStore();

	let { isTaskActionModalOpen, toggleTaskActionModal, selectedTab, projectData, clickMapNewFeature }: Props = $props();

	const taskSubmissionInfo = $derived(entitiesStore.taskSubmissionInfo);
	const taskSubmission = $derived(
		taskSubmissionInfo?.find((taskSubmission) => taskSubmission?.task_id === taskStore?.selectedTaskIndex),
	);
	let dialogRef;
	let toggleTaskCompleteConfirmation: boolean = $state(false);
</script>

{#if taskStore.selectedTaskId && selectedTab === 'map' && isTaskActionModalOpen}
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
				{#if projectData.status === projectStatus.PUBLISHED && (taskStore.selectedTaskState === taskStatus.UNLOCKED_TO_MAP || taskStore.selectedTaskState === taskStatus.LOCKED_FOR_MAPPING)}
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
						<hot-icon name="new-window"></hot-icon>
						<p class="action">{m['popup.map_new_feature']()}</p>
					</div>
				{/if}
			</div>

			{#if projectData.status === projectStatus.PUBLISHED}
				{#if taskStore.selectedTaskState === 'UNLOCKED_TO_MAP'}
					<p class="unlock-selected">{m['popup.start_mapping_task']({ taskId: taskStore.selectedTaskIndex })}</p>
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
							<hot-icon slot="prefix" name="location"></hot-icon>
							<span>{m['popup.start_mapping']()}</span>
						</sl-button>
					</div>
				{:else if taskStore.selectedTaskState === 'LOCKED_FOR_MAPPING'}
					<p class="lock-selected">
						{m['dialog_task_actions.task']()} #{taskStore.selectedTaskIndex}
						{m['dialog_task_actions.locked_is_complete']()}
					</p>
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
							<hot-icon slot="prefix" name="close"></hot-icon>
							<span>{m['popup.cancel_mapping']()}</span>
						</sl-button>
						<!-- keep button disabled until the entity statuses are fetched -->
						<sl-button
							disabled={entitiesStore.syncEntityStatusManuallyLoading}
							onclick={() => {
								toggleTaskCompleteConfirmation = true;
							}}
							variant="primary"
							size="small"
							class="green"
							onkeydown={(e: KeyboardEvent) => {
								if (e.key === 'Enter') {
									toggleTaskCompleteConfirmation = true;
								}
							}}
							role="button"
							tabindex="0"
						>
							<hot-icon slot="prefix" name="check"></hot-icon>
							<span>{m['dialog_task_actions.complete_mapping']()}</span>
						</sl-button>
					</div>
				{:else}
					<div>
						This task was marked as fully mapped. If you wish to unlock it and continue mapping, please contact the
						project manager.
					</div>
				{/if}
			{/if}
		</div>
	</div>
{/if}

<hot-dialog
	bind:this={dialogRef}
	class="task-action-dialog"
	open={toggleTaskCompleteConfirmation}
	onsl-hide={() => {
		toggleTaskCompleteConfirmation = false;
	}}
	noHeader
>
	<h5 class="dialog-text">
		{#if taskSubmission}
			<!-- Subtle difference to include 'only' in the text here -->
			{#if taskSubmission?.submission_count < taskSubmission?.feature_count}
				{m['popup.task_complete_only_total_mapped']({
					totalMapped: unicodeBold(`${taskSubmission?.submission_count}/${taskSubmission?.feature_count}`),
				})}
				<br />
			{:else}
				{m['popup.task_complete_total_mapped']({
					totalMapped: unicodeBold(`${taskSubmission?.submission_count}/${taskSubmission?.feature_count}`),
				})}
				<br />
			{/if}
		{/if}
		<!--  The confirmation dialog is always displayed -->
		{m['popup.task_complete_confirm']()}
	</h5>
	<div class="button-wrapper">
		<sl-button
			onclick={() => {
				toggleTaskCompleteConfirmation = false;
			}}
			variant="default"
			size="small"
			class="green"
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') {
					toggleTaskCompleteConfirmation = false;
				}
			}}
			role="button"
			tabindex="0"
		>
			<span>{m['dialog_task_actions.continue_mapping']()}</span>
		</sl-button>
		<sl-button
			onclick={() => {
				if (!taskStore.selectedTaskId) return;
				finishTask(projectData?.id, taskStore.selectedTaskId);
				toggleTaskCompleteConfirmation = false;
			}}
			variant="primary"
			size="small"
			class="green"
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') {
					if (!taskStore.selectedTaskId) return;
					finishTask(projectData?.id, taskStore.selectedTaskId);
					toggleTaskCompleteConfirmation = false;
				}
			}}
			role="button"
			tabindex="0"
		>
			<span>{m['dialog_task_actions.complete_mapping']()}</span>
		</sl-button>
	</div>
</hot-dialog>
