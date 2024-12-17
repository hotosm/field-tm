<script lang="ts">
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
	<div class="flex justify-center !w-[100vw] absolute bottom-[4rem] left-0 pointer-events-none z-50">
		<div
			class="bg-white w-full font-barlow-regular md:max-w-[580px] pointer-events-auto px-4 py-3 sm:py-4 rounded-t-3xl"
		>
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
				<p class="text-[#333] text-xl font-barlow-semibold">Task #{taskStore.selectedTaskIndex}</p>
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
					<p class="uppercase text-[0.813rem] text-red-600 group-hover:text-red-700">map new feature</p>
				</div>
			</div>

			{#if taskStore.selectedTaskState === 'UNLOCKED_TO_MAP'}
				<p class="my-4 sm:my-6">Do you want to start mapping task #{taskStore.selectedTaskIndex}?</p>
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
						<span class="font-barlow-medium text-sm">CANCEL</span>
					</sl-button>
					<sl-button
						variant="default"
						size="small"
						class="primary"
						onclick={() => mapTask(projectData?.id, taskStore.selectedTaskId)}
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								mapTask(projectData?.id, taskStore.selectedTaskId);
							}
						}}
						role="button"
						tabindex="0"
					>
						<hot-icon slot="prefix" name="location" class="!text-[1rem] text-white cursor-pointer duration-200"
						></hot-icon>
						<span class="font-barlow-medium text-sm">START MAPPING</span>
					</sl-button>
				</div>
			{:else if taskStore.selectedTaskState === 'LOCKED_FOR_MAPPING'}
				<p class="my-4 sm:my-6">Task #{taskStore.selectedTaskIndex} has been locked. Is the task completely mapped?</p>
				<div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
					<sl-button
						onclick={() => resetTask(projectData?.id, taskStore.selectedTaskId)}
						variant="default"
						outline
						size="small"
						class="secondary"
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								resetTask(projectData?.id, taskStore.selectedTaskId);
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
						<span class="font-barlow-medium text-sm">CANCEL MAPPING</span>
					</sl-button>
					<sl-button
						onclick={() => finishTask(projectData?.id, taskStore.selectedTaskId)}
						variant="default"
						size="small"
						class="green"
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								finishTask(projectData?.id, taskStore.selectedTaskId);
							}
						}}
						role="button"
						tabindex="0"
					>
						<hot-icon slot="prefix" name="check" class="!text-[1rem] text-white cursor-pointer duration-200"></hot-icon>
						<span class="font-barlow-medium text-sm">COMPLETE MAPPING</span>
					</sl-button>
					<sl-button variant="default" size="small" class="primary col-span-2 sm:col-span-1">
						<span class="font-barlow-medium text-sm">GO TO ODK</span>
					</sl-button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style></style>
