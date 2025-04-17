<script lang="ts">
	import '$styles/dialog-entities-actions.css';
	import { distance } from '@turf/distance';
	import type { Coord } from '@turf/helpers';
	import type { SlDialog, SlDrawer } from '@shoelace-style/shoelace';

	import { m } from '$translations/messages.js';
	import { TaskStatusEnum, type ProjectData } from '$lib/types';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getAlertStore, getCommonStore } from '$store/common.svelte.ts';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { mapTask } from '$lib/db/events';

	type statusType = 'READY' | 'OPENED_IN_ODK' | 'SURVEY_SUBMITTED' | 'MARKED_BAD' | 'VALIDATED';
	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: ProjectData;
		displayWebFormsDrawer: Boolean;
	};
	function getStatusStyle(status: statusType) {
		switch (status) {
			case 'READY':
				return 'bg-neutral-100 text-neutral-700';
			case 'OPENED_IN_ODK':
				return 'bg-warning-100 text-warning-700';
			case 'SURVEY_SUBMITTED':
				return 'bg-success-100 text-success-700';
			case 'MARKED_BAD':
				return 'bg-danger-100 text-danger-700';
			case 'VALIDATED':
				return 'bg-blue-100 text-blue-700';
		}
	}

	let {
		isTaskActionModalOpen,
		toggleTaskActionModal,
		selectedTab,
		projectData,
		displayWebFormsDrawer = $bindable(false),
	}: Props = $props();

	const entitiesStore = getEntitiesStatusStore();
	const alertStore = getAlertStore();
	const commonStore = getCommonStore();
	const taskStore = getTaskStore();

	let dialogRef: SlDialog | null = $state(null);
	let toggleDistanceWarningDialog = $state(false);
	let showCommentsPopup: boolean = $state(false);

	// use Map for quick lookups
	let entityMap = $derived(new Map(entitiesStore.entitiesStatusList.map((entity) => [entity.entity_id, entity])));

	const selectedEntityId = $derived(entitiesStore.selectedEntity || '');
	const selectedEntity = $derived(entityMap.get(selectedEntityId));
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
					// NOTE here we don't translate the field as English values are always saved as the Entity label
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
						m['dialog_entities_actions.distance_constraint'](),
					variant: 'warning',
				});
				return;
			}

			const entityDistance = distance(coordFrom as Coord, coordTo as Coord, { units: 'kilometers' }) * 1000;
			if (entityDistance && entityDistance > projectData?.geo_restrict_distance_meters) {
				// Feature is far away from user, warn user
				alertStore.setAlert({
					message: `${m['dialog_entities_actions.feature_must_be']()} ${projectData?.geo_restrict_distance_meters} ${m['dialog_entities_actions.meters_location']()}`,
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
			alertStore.setAlert({ message: m['dialog_entities_actions.enable_location'](), variant: 'warning' });
			return;
		}
		entitiesStore.setEntityToNavigate(selectedEntityCoordinate);
	};
</script>

{#if isTaskActionModalOpen && selectedTab === 'map' && selectedEntity}
	<div class="task-action-modal">
		<div
			class="content"
		>
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
			<div class="section-container">
				<p class="selected-title">{m['popup.feature']()} {selectedEntity?.osmid}</p>
				<div class="section">
					<div class="item">
						<p class="label">{m['popup.task_id']()}</p>
						:
						<p class="value">{selectedEntity?.task_id}</p>
					</div>
					<div class="item">
						<p class="label">{m['dialog_entities_actions.entity_uuid']()}</p>
						:
						<p class="value">{selectedEntity?.entity_id}</p>
					</div>
					<div class="item items-center">
						<p class="label">{m['dialog_entities_actions.status']()}</p>
						:
						<p
							class={`${getStatusStyle(selectedEntity?.status)}`}
						>
							{m[`entity_states.${selectedEntity?.status}`]()}
						</p>
					</div>
					{#if entityComments?.length > 0}
						<div class="dialog-comments">
							<p class="label">{m['dialog_entities_actions.comments']()}</p>
							:
							<div class="dialog-comments-list">
								{#each entityComments?.slice(0, 2) as comment}
									<div class="dialog-comment">
										<div class="dialog-comment-content">
											<p>{comment?.username}</p>
											<div class="dialog-comment-info">
												<hot-icon name="clock-history"></hot-icon>
												<p class="created-at">{comment?.created_at?.split(' ')[0]}</p>
											</div>
										</div>
										<p class="dialog-comment-text">
											{comment?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}
										</p>
									</div>
								{/each}
								{#if entityComments?.length > 2}
									<div class="dialog-comment-see-all">
										<div class="dialog-comment-see-all-empty"></div>
										<div
											class="dialog-comment-see-all-link"
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
					<div class="entity">
						<sl-button
							disabled={entityToNavigate?.entityId === selectedEntity?.entity_id}
							variant="default"
							size="small"
							class="entity-button-to"
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
							<hot-icon slot="prefix" name="direction"></hot-icon>
							<span>{m['popup.navigate_here']()}</span>
						</sl-button>
						{#if commonStore.enableWebforms === false}
							<sl-button
								loading={entitiesStore.updateEntityStatusLoading}
								variant="primary"
								size="small"
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
								<hot-icon slot="prefix" name="location"
								></hot-icon>
								<span>{m['popup.map_in_odk']()}</span>
							</sl-button>
						{/if}
						{#if commonStore.enableWebforms}
							<sl-button
								loading={entitiesStore.updateEntityStatusLoading}
								variant="primary"
								size="small"
								onclick={() => {
									toggleTaskActionModal(false);
									entitiesStore.updateEntityStatus(projectData.id, {
										entity_id: selectedEntity?.entity_id,
										status: 1,
										// NOTE here we don't translate the field as English values are always saved as the Entity label
										label: `Task ${selectedEntity?.task_id} Feature ${selectedEntity?.osmid}`,
									});
									displayWebFormsDrawer = true;
								}}
								onkeydown={(e: KeyboardEvent) => {
									if (e.key === 'Enter') {
										toggleTaskActionModal(false);
										entitiesStore.updateEntityStatus(projectData.id, {
											entity_id: selectedEntity?.entity_id,
											status: 1,
											// NOTE here we don't translate the field as English values are always saved as the Entity label
											label: `Task ${selectedEntity?.task_id} Feature ${selectedEntity?.osmid}`,
										});
										displayWebFormsDrawer = true;
									}
								}}
								role="button"
								tabindex="0"
							>
								<hot-icon slot="prefix" name="location"
								></hot-icon>
								<span>{m['dialog_entities_actions.collect_data']()}</span>
							</sl-button>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

{#if entitiesStore.selectedEntityCoordinate?.coordinate && entitiesStore.userLocationCoord}
	<hot-dialog
		bind:this={dialogRef}
		class="entity-dialog"
		open={toggleDistanceWarningDialog}
		onsl-hide={() => {
			toggleDistanceWarningDialog = false;
		}}
		noHeader
	>
		<div class="entity-dialog-content">
			<p class="entity-dialog-youare">
				{m['dialog_entities_actions.you_are']()} <b
					>{(
						distance(
							entitiesStore.selectedEntityCoordinate?.coordinate as Coord,
							entitiesStore.userLocationCoord as Coord,
							{ units: 'kilometers' },
						) * 1000
					).toFixed(2)}m</b
				> {m['dialog_entities_actions.away_sure']()}
			</p>
			<div class="entity-dialog-actions">
				<sl-button
					variant="default"
					size="small"
					class="secondary"
					onclick={() => (toggleDistanceWarningDialog = false)}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							toggleDistanceWarningDialog = false;
						}
					}}
					role="button"
					tabindex="0"
				>
					<span>NO</span>
				</sl-button>
				<sl-button
					variant="primary"
					size="small"
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
					<span>YES</span>
				</sl-button>
			</div>
		</div>
	</hot-dialog>
{/if}

<hot-dialog
	label="Feature Comments"
	class="feature-comments-dialog"
	open={showCommentsPopup}
	onsl-hide={() => {
		showCommentsPopup = false;
	}}
>
	<div class="feature-comments">
		{#each entityComments as comment}
			<div class="feature-comment">
				<div class="feature-comment-meta">
					<p>{comment?.username}</p>
					<div class="feature-comment-history">
						<hot-icon name="clock-history"></hot-icon>
						<p>{comment?.created_at?.split(' ')[0]}</p>
					</div>
				</div>
				<p>
					{comment?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}
				</p>
			</div>
		{/each}
	</div>
</hot-dialog>
