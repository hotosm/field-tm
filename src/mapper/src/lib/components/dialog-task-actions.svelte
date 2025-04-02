<script lang="ts">
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
	<div class="flex justify-center !w-[100vw] absolute bottom-[4rem] left-0 pointer-events-none z-50 font-barlow">
		<div class="bg-white w-full font-regular md:max-w-[580px] pointer-events-auto px-4 py-3 sm:py-4 rounded-t-3xl">
			<div class="flex justify-end">
				<hot-icon
					name="close"
					class="!text-[1.5rem] text-[#52525B] cursor-pointer hover:text-red-600 duration-200"
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
			<div class="flex justify-between items-center">
				<p class="text-[#333] text-xl font-semibold">{m['popup.task']()} #{taskStore.selectedTaskIndex}</p>
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
					class="flex items-center gap-1 cursor-pointer group"
				>
					<hot-icon
						name="new-window"
						class="!text-[1.25rem] duration-200 text-[#333333] font-light group-hover:text-black"
					></hot-icon>
					<p class="uppercase text-[0.813rem] text-red-600 group-hover:text-red-700">{m['popup.map_new_feature']()}</p>
				</div>
			</div>

			{#if taskStore.selectedTaskState === 'UNLOCKED_TO_MAP'}
				<p class="my-4 sm:my-6">{m['popup.start_mapping_task']({taskId: taskStore.selectedTaskIndex})}</p>
				<div class="flex justify-center gap-x-2">
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
						<span class="font-barlow font-medium text-sm">{m['popup.cancel']()}</span>
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
						<hot-icon slot="prefix" name="location" class="!text-[1rem] text-white cursor-pointer duration-200"
						></hot-icon>
						<span class="font-barlow font-medium text-sm">{m['popup.start_mapping']()}</span>
					</sl-button>
				</div>
			{:else if taskStore.selectedTaskState === 'LOCKED_FOR_MAPPING'}
				<p class="my-4 sm:my-6">{m['dialog_task_actions.task']} #{taskStore.selectedTaskIndex} {m['dialog_task_actions.locked_is_complete']} </p>
				<div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
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
							class="!text-[1rem] text-[#d73f37] cursor-pointer duration-200 hover:text-[#b91c1c]"
						></hot-icon>
						<span class="font-barlow font-medium text-sm">{m['popup.cancel_mapping']()}</span>
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
						<hot-icon slot="prefix" name="check" class="!text-[1rem] text-white cursor-pointer duration-200"></hot-icon>
						<span class="font-barlow font-medium text-sm">{m['dialog_entities_actions.complete_mapping']()}</span>
					</sl-button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style></style>
