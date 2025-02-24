<script lang="ts">
	import { distance } from '@turf/distance';
	import type { Coord } from '@turf/helpers';
	import { TaskStatusEnum, type ProjectData } from '$lib/types';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getAlertStore } from '$store/common.svelte.ts';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { mapTask } from '$lib/db/events';
	import type { SlDialog } from '@shoelace-style/shoelace';

	type statusType = 'READY' | 'OPENED_IN_ODK' | 'SURVEY_SUBMITTED' | 'MARKED_BAD' | 'VALIDATED';
	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: ProjectData;
	};

	function getStatusStyle(status: statusType) {
		switch (status) {
			case 'READY':
				return 'bg-gray-100 text-gray-700';
			case 'OPENED_IN_ODK':
				return 'bg-yellow-100 text-yellow-700';
			case 'SURVEY_SUBMITTED':
				return 'bg-green-100 text-green-700';
			case 'MARKED_BAD':
				return 'bg-red-100 text-red-700';
			case 'VALIDATED':
				return 'bg-blue-100 text-blue-700';
		}
	}

	let { isTaskActionModalOpen, toggleTaskActionModal, selectedTab, projectData }: Props = $props();

	let dialogRef: SlDialog | null = $state(null);
	let toggleDistanceWarningDialog = $state(false);
	let showCommentsPopup: boolean = $state(false);

	const entitiesStore = getEntitiesStatusStore();
	const alertStore = getAlertStore();
	const taskStore = getTaskStore();

	const selectedEntityOsmId = $derived(entitiesStore.selectedEntity);
	const selectedEntity = $derived(
		entitiesStore.entitiesStatusList?.find((entity) => entity.osmid === selectedEntityOsmId),
	);
	const selectedEntityCoordinate = $derived(entitiesStore.selectedEntityCoordinate);
	const entityToNavigate = $derived(entitiesStore.entityToNavigate);
	const entityComments = $derived(
		taskStore.events
			?.filter(
				(event) =>
					event.event === 'COMMENT' &&
					event.comment?.startsWith('#submissionId:uuid:') &&
					`#featureId:${entitiesStore.selectedEntity}` === event.comment?.split(' ')?.[1],
			)
			?.reverse(),
	);

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
		<div
			class="bg-white w-full font-regular md:max-w-[580px] pointer-events-auto px-4 py-3 sm:py-4 rounded-t-3xl max-h-[60vh] overflow-y-scroll"
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
				<p class="text-[#333] text-lg font-semibold">Feature {selectedEntity?.osmid}</p>
				<div class="flex flex-col gap-2">
					<div class="flex">
						<p class="min-w-[6.25rem] text-[#2B2B2B]">Task Id</p>
						:
						<p class="text-[#161616] font-medium ml-2">{selectedEntity?.task_id}</p>
					</div>
					<div class="flex">
						<p class="min-w-[6.25rem] text-[#2B2B2B]">Entity Uuid</p>
						:
						<p class="break-all text-[#161616] font-medium ml-2">{selectedEntity?.entity_id}</p>
					</div>
					<div class="flex items-center">
						<p class="min-w-[6.25rem] text-[#2B2B2B]">Status</p>
						:
						<p
							class={`text-[#161616] font-medium capitalize border-[1px] border-solid ml-2 py-1 px-3 rounded-full ${getStatusStyle(selectedEntity?.status)}`}
						>
							{selectedEntity?.status?.replaceAll('_', ' ')?.toLowerCase()}
						</p>
					</div>
					{#if entityComments?.length > 1}
						<div class="flex">
							<p class="min-w-[6.25rem] text-[#2B2B2B]">Comments</p>
							:
							<div class="flex flex-col ml-2 gap-2 flex-1">
								{#each entityComments?.slice(0, 2) as comment}
									<div class="bg-[#F6F5F5] rounded px-2 py-1">
										<div class="flex items-center justify-between mb-1">
											<p>{comment?.username}</p>
											<div class="flex items-center gap-2">
												<hot-icon name="clock-history" class="!text-[0.8rem] text-red-600 cursor-pointer"></hot-icon>
												<p class="text-sm">{comment?.created_at?.split(' ')[0]}</p>
											</div>
										</div>
										<p class="font-medium">
											{comment?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}
										</p>
									</div>
								{/each}
								{#if entityComments?.length > 2}
									<div class="flex items-center gap-2">
										<div class="h-[1px] bg-gray-200 flex flex-1"></div>
										<div
											class="text-sm text-gray-600 hover:text-gray-800 cursor-pointer font-light"
											onclick={() => (showCommentsPopup = true)}
											onkeydown={(e: KeyboardEvent) => {
												if (e.key === 'Enter') {
													showCommentsPopup = true;
												}
											}}
											tabindex="0"
											role="button"
										>
											See all comments
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
				{#if selectedEntity?.status !== 'SURVEY_SUBMITTED' && selectedEntity?.status !== 'VALIDATED'}
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

<hot-dialog
	label="Feature Comments"
	class="dialog-overview z-50 font-barlow font-regular"
	open={showCommentsPopup}
	onsl-hide={() => {
		showCommentsPopup = false;
	}}
>
	<div class="flex flex-col gap-3">
		{#each entityComments as comment}
			<div class="bg-[#F6F5F5] rounded px-2 py-1">
				<div class="flex items-center justify-between mb-2">
					<p>{comment?.username}</p>
					<div class="flex items-center gap-2">
						<hot-icon name="clock-history" class="!text-[0.8rem] text-red-600 cursor-pointer"></hot-icon>
						<p class="text-sm">{comment?.created_at?.split(' ')[0]}</p>
					</div>
				</div>
				<p class="font-medium">
					{comment?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}
				</p>
			</div>
		{/each}
	</div>
</hot-dialog>
