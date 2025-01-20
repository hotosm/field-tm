<script lang="ts">
	import { distance } from '@turf/distance';
	import type { Coord } from '@turf/helpers';
	import { TaskStatusEnum, type ProjectData } from '$lib/types';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getAlertStore } from '$store/common.svelte.ts';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { mapTask } from '$lib/db/events';
	import type { SlDialog } from '@shoelace-style/shoelace';

	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: ProjectData;
	};

	let { isTaskActionModalOpen, toggleTaskActionModal, selectedTab, projectData }: Props = $props();

	let dialogRef: SlDialog | null = $state(null);
	let toggleDistanceWarningDialog = $state(false);

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

	const handleMapFeature = () => {
		/**
		 	Logic to handle mapping feature in different scenarios:
			1. No geolocation, no force geo constraint: allow mapping, ignore / do not show warning
			2. No geolocation, force geo constraint: block mapping, show prompt to enable geolocation
			3. Geolocation, no force geo constraint: show warning dialog if feature is far away
			4. Geolocation, force geo constraint: block mapping if out of range else allow
		**/
		const coordTo = entitiesStore.selectedEntityCoordinate?.coordinate;
		const coordFrom = entitiesStore.userLocationCoord;

		// Run only if geo_restrict_force_error is set to true
		if (projectData?.geo_restrict_force_error) {
			// Geolocation not enabled, warn user
			if (!coordFrom) {
				alertStore.setAlert({
					message:
						'This project has distance constraint enabled. Please enable device geolocation for optimal functionality',
					variant: 'warning',
				});
				return;
			}

			const entityDistance = distance(coordFrom as Coord, coordTo as Coord, { units: 'kilometers' }) * 1000;
			if (entityDistance && entityDistance > projectData?.geo_restrict_distance_meters) {
				// Feature is far away from user, warn user
				alertStore.setAlert({
					message: `The feature must be within ${projectData?.geo_restrict_distance_meters} meters of your location`,
					variant: 'warning',
				});
				return;
			}
		}

		// Show warning dialog if geo_restrict_force_error is set to false, user location enabled and feature is far away
		if (
			!projectData?.geo_restrict_force_error &&
			coordFrom &&
			distance(coordFrom as Coord, coordTo as Coord, { units: 'kilometers' }) * 1000 >
				projectData?.geo_restrict_distance_meters
		) {
			toggleDistanceWarningDialog = true;
			return;
		}

		mapFeature();
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
	<div class="font-barlow flex justify-center !w-[100vw] absolute bottom-[4rem] left-0 pointer-events-none z-50">
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
			<div class="flex flex-col gap-4">
				<div class="flex items-center justify-between">
					<p class="text-[#333] text-xl font-semibold">Feature {selectedEntity?.osmid}</p>
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
						<span class="font-barlow font-medium text-sm uppercase">SYNC STATUS</span>
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
							<span class="font-barlow font-medium text-sm">NAVIGATE HERE</span>
						</sl-button>
						<sl-button
							loading={entitiesStore.updateEntityStatusLoading}
							variant="default"
							size="small"
							class="primary flex-grow"
							onclick={() => {
								handleMapFeature();
							}}
							onkeydown={(e: KeyboardEvent) => {
								if (e.key === 'Enter') {
									handleMapFeature();
								}
							}}
							role="button"
							tabindex="0"
						>
							<hot-icon slot="prefix" name="location" class="!text-[1rem] text-white cursor-pointer duration-200"
							></hot-icon>
							<span class="font-barlow font-medium text-sm">MAP FEATURE IN ODK</span>
						</sl-button>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

{#if entitiesStore.selectedEntityCoordinate?.coordinate && entitiesStore.userLocationCoord}
	<hot-dialog
		bind:this={dialogRef}
		class="dialog-overview z-50 font-barlow font-regular"
		open={toggleDistanceWarningDialog}
		onsl-hide={() => {
			toggleDistanceWarningDialog = false;
		}}
		noHeader
	>
		<div class="flex items-start flex-col">
			<p class="text-base mb-5 text-gray-700">
				Your are <b
					>{(
						distance(
							entitiesStore.selectedEntityCoordinate?.coordinate as Coord,
							entitiesStore.userLocationCoord as Coord,
							{ units: 'kilometers' },
						) * 1000
					).toFixed(2)}m</b
				> away from the feature. Are you sure you want to map this feature?
			</p>
			<div class="flex gap-2 ml-auto">
				<sl-button
					variant="default"
					size="small"
					class="secondary flex-grow"
					onclick={() => (toggleDistanceWarningDialog = false)}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							toggleDistanceWarningDialog = false;
						}
					}}
					role="button"
					tabindex="0"
				>
					<span class="font-barlow font-medium text-sm">NO</span>
				</sl-button>
				<sl-button
					variant="default"
					size="small"
					class="primary flex-grow"
					onclick={() => {
						mapFeature();
						toggleDistanceWarningDialog = false;
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							mapFeature();
							toggleDistanceWarningDialog = false;
						}
					}}
					role="button"
					tabindex="0"
				>
					<span class="font-barlow font-medium text-sm">YES</span>
				</sl-button>
			</div>
		</div>
	</hot-dialog>
{/if}
