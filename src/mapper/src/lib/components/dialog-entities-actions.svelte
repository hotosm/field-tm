<script lang="ts">
	import { TaskStatusEnum, type ProjectData } from '$lib/types';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getAlertStore } from '$store/common.svelte.ts';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { mapTask } from '$lib/db/events';

	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: ProjectData;
	};

	let { isTaskActionModalOpen, toggleTaskActionModal, selectedTab, projectData }: Props = $props();

	const entitiesStore = getEntitiesStatusStore();
	const alertStore = getAlertStore();
	const taskStore = getTaskStore();

	const selectedEntityOsmId = $derived(entitiesStore.selectedEntity);
	const selectedEntity = $derived(
		entitiesStore.entitiesStatusList?.find((entity) => entity.osmid === selectedEntityOsmId),
	);
	const selectedEntityCoordinate = $derived(entitiesStore.selectedEntityCoordinate);
	const entityToNavigate = $derived(entitiesStore.entityToNavigate);

	const mapFeature = () => {
		const xformId = projectData?.odk_form_id;
		const entityUuid = selectedEntity?.entity_id;

		if (!xformId || !entityUuid) {
			return;
		}

		const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
		if (isMobile) {
			if (selectedEntity?.status === 'READY') {
				entitiesStore.updateEntityStatus(projectData.id, {
					entity_id: entityUuid,
					status: 1,
					label: `Task ${selectedEntity?.task_id} Feature ${selectedEntity?.osmid}`,
				});

				if (taskStore.selectedTaskId && taskStore.selectedTaskState === TaskStatusEnum['UNLOCKED_TO_MAP']) {
					mapTask(projectData?.id, taskStore.selectedTaskId);
				}
			}
			// Load entity in ODK Collect by intent
			document.location.href = `odkcollect://form/${xformId}?feature=${entityUuid}`;
		} else {
			alertStore.setAlert({ message: 'Requires a mobile phone with ODK Collect.', variant: 'warning' });
		}
	};

	const navigateToEntity = () => {
		if (!entitiesStore.toggleGeolocation) {
			alertStore.setAlert({ message: 'Please enable geolocation to navigate to the entity.', variant: 'warning' });
			return;
		}
		entitiesStore.setEntityToNavigate(selectedEntityCoordinate);
	};
</script>

{#if isTaskActionModalOpen && selectedTab === 'map' && selectedEntity}
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
			<div class="flex flex-col gap-4">
				<div class="flex items-center justify-between">
					<p class="text-[#333] text-xl font-barlow-semibold">Feature {selectedEntity?.osmid}</p>
					<sl-button
						onclick={async () => {
							await entitiesStore.syncEntityStatus(projectData?.id);
						}}
						onkeydown={(e: KeyboardEvent) => {
							e.key === 'Enter' && {};
						}}
						role="button"
						tabindex="0"
						size="small"
						class="link w-fit ml-auto"
						disabled={entitiesStore.syncEntityStatusLoading}
					>
						<hot-icon
							slot="prefix"
							name="arrow-repeat"
							class={`!text-[1rem] cursor-pointer duration-200 ${entitiesStore.syncEntityStatusLoading && 'animate-spin'}`}
						></hot-icon>
						<span class="font-barlow-medium text-SM uppercase">SYNC STATUS</span>
					</sl-button>
				</div>
				<div class="flex flex-col gap-1">
					<p><span class="font-medium">Task Id:</span> {selectedEntity?.task_id}</p>
					<p><span class="font-medium">Entity Uuid:</span> {selectedEntity?.entity_id}</p>
					<p>
						<span class="font-medium">Status:</span>
						{selectedEntity?.status?.replaceAll('_', ' ')}
					</p>
				</div>
				{#if selectedEntity?.status !== 'SURVEY_SUBMITTED'}
					<div class="flex gap-2">
						<sl-button
							disabled={entityToNavigate?.entityId === selectedEntity?.osmid}
							variant="default"
							size="small"
							class="secondary flex-grow"
							onclick={() => {
								navigateToEntity();
							}}
							onkeydown={(e: KeyboardEvent) => {
								if (e.key === 'Enter') {
									navigateToEntity();
								}
							}}
							role="button"
							tabindex="0"
						>
							<hot-icon slot="prefix" name="direction" class="!text-[1rem] cursor-pointer duration-200"></hot-icon>
							<span class="font-barlow-medium text-sm">NAVIGATE HERE</span>
						</sl-button>
						<sl-button
							loading={entitiesStore.updateEntityStatusLoading}
							variant="default"
							size="small"
							class="primary flex-grow"
							onclick={() => {
								mapFeature();
							}}
							onkeydown={(e: KeyboardEvent) => {
								if (e.key === 'Enter') {
									mapFeature();
								}
							}}
							role="button"
							tabindex="0"
						>
							<hot-icon slot="prefix" name="location" class="!text-[1rem] text-white cursor-pointer duration-200"
							></hot-icon>
							<span class="font-barlow-medium text-sm">MAP FEATURE IN ODK</span>
						</sl-button>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
