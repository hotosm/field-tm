<script lang="ts">
	import '$styles/dialog-entities-actions.css';
	import { distance } from '@turf/distance';
	import type { Coord } from '@turf/helpers';
	import type { SlDialog } from '@shoelace-style/shoelace';

	import { m } from '$translations/messages.js';
	import { type APIProject } from '$lib/types';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getAlertStore, getCommonStore } from '$store/common.svelte.ts';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { mapTask } from '$lib/db/events';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { projectStatus } from '$constants/enums';

	const API_URL = import.meta.env.VITE_API_URL;

	type Props = {
		isTaskActionModalOpen: boolean;
		toggleTaskActionModal: (value: boolean) => void;
		selectedTab: string;
		projectData: APIProject;
		displayWebFormsDrawer: Boolean;
	};

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
	const loginStore = getLoginStore();

	let dialogRef: SlDialog | null = $state(null);
	let confirmationDialogRef: SlDialog | null = $state(null);
	let submissionDetailsRef: SlDialog | null = $state(null);
	let toggleDistanceWarningDialog = $state(false);
	let showCommentsPopup: boolean = $state(false);
	let showDeleteEntityPopup: boolean = $state(false);
	let showSubmissionDetailsPopup: boolean = $state(false);
	let submissionData: Record<string, any> | null = $state(null);
	let loadingSubmission = false;

	const selectedEntity = $derived(entitiesStore.selectedEntity);
	const selectedEntityCoordinate = $derived(entitiesStore.selectedEntityCoordinate);
	const latestSubmissionId = $derived(entitiesStore.selectedEntity?.submission_ids?.split(',').at(-1))
	const entityToNavigate = $derived(entitiesStore.entityToNavigate);
	const entityComments = $derived(
		taskStore.events
			?.filter(
				(event) =>
					event.event === 'COMMENT' &&
					event.comment?.startsWith('#submissionId:uuid:') &&
					`#featureId:${selectedEntity?.entity_id}` === event.comment?.split(' ')?.[1],
			)
			?.reverse(),
	);

	const updateEntityTaskStatus = () => {
		if (selectedEntity?.status === 'READY') {
			entitiesStore.updateEntityStatus(projectData.id, {
				entity_id: selectedEntity?.entity_id,
				status: 1,
				// NOTE here we don't translate the field as English values are always saved as the Entity label
				label: `Feature ${selectedEntity?.osm_id}`,
			});

			if (taskStore.selectedTaskId && taskStore.selectedTaskState === 'UNLOCKED_TO_MAP')
				mapTask(projectData?.id, taskStore.selectedTaskId);
		}
	};

	const mapFeatureInODKApp = () => {
		const xformId = projectData?.odk_form_id;
		const entityUuid = selectedEntity?.entity_id;

		if (!xformId || !entityUuid) return;

		const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
		if (isMobile) {
			updateEntityTaskStatus();
			// Load entity in ODK Collect by intent
			// NOTE we have since removed support for the custom ODK Collect application
			// however, this will still open the app without any existing data loaded
			// (if the user has the old custom app, it may still work and load the feature)
			document.location.href = `odkcollect://form/${xformId}?feature=${entityUuid}`;
		} else {
			alertStore.setAlert({ message: 'Requires a mobile phone with ODK Collect.', variant: 'warning' });
		}
	};

	const mapFeatureInWebForms = () => {
		toggleTaskActionModal(false);
		updateEntityTaskStatus();
		displayWebFormsDrawer = true;
	};

	const mapFeature = () => {
		if (commonStore.enableWebforms) {
			mapFeatureInWebForms();
		} else {
			mapFeatureInODKApp();
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
					message: m['dialog_entities_actions.distance_constraint'](),
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

	const deleteNewFeature = async (entityId: string) => {
		const { entity_id, created_by } = entitiesStore.newGeomFeatcol.features.find(
			(feature: Record<string, any>) => feature.properties?.entity_id === entityId,
		)?.properties;
		if (created_by && created_by === loginStore.getAuthDetails?.sub) {
			await entitiesStore.deleteNewEntity(projectData.id, entity_id);
			showDeleteEntityPopup = false;
		} else {
			alertStore.setAlert({
				message: m['dialog_entities_actions.contact_pm_for_entity_deletion'](),
				variant: 'warning',
			});
		}
	};

	const getAndDisplaySubmissionDetails = async (submissionId: string) => {
		// FIXME this should probably be done via backend
		try {
			loadingSubmission = true;
			showSubmissionDetailsPopup = true;

			const res = await fetch(`${API_URL}/submission/${submissionId}?project_id=${projectData.id}`, {
				credentials: 'include',
			});

			if (!res.ok) throw new Error(`Failed to fetch submission: ${res.statusText}`);
			const dataJson = await res.json();
			const surveyQuestionsGroup = dataJson?.survey_questions;
			
			// Fields to exclude from display (system/metadata fields)
			const excludeFields = [
				'__id',
				'__system',
				'meta',
				'start',
				'end',
				'deviceid',
				'phonenumber',
				'email',
				'warmup',
				'feature',
				'xid',
				'xlocation',
				'submission_ids',
				'created_by',
				'today',
				'username',
				'task_id',
				'status',
			];
			
			// Nested when verification group included
			if (surveyQuestionsGroup) {
				submissionData = dataJson?.survey_questions;
			// When no verification group, questions are not grouped
			} else {
				// Filter out excluded fields
				const filteredData = Object.entries(dataJson)
					.filter(([key]) => !excludeFields.includes(key))
					.reduce((acc, [key, value]) => {
						acc[key] = value;
						return acc;
					}, {} as Record<string, any>);
				
				submissionData = filteredData;
				console.log(submissionData);
			}
		} catch (err) {
			console.error("Error loading submission:", err);
			submissionData = { error: "Failed to load submission details." };
		} finally {
			loadingSubmission = false;
		}
	};

	function isObject(value: any): boolean {
		return value && typeof value === 'object' && !Array.isArray(value);
	}

	function hasNonNullValues(obj: any): boolean {
		return Object.values(obj).some(v => v !== null && v !== undefined);
	}
</script>

{#if isTaskActionModalOpen && selectedTab === 'map' && selectedEntity}
	<div class="task-action-modal">
		<div class="content">
			<div class="icon">
				<sl-icon
					name="close"
					onclick={() => {
						toggleTaskActionModal(false);
						entitiesStore.setSelectedEntityId(null);
						entitiesStore.setSelectedEntityCoordinate(null);
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							toggleTaskActionModal(false);
							entitiesStore.setSelectedEntityId(null);
							entitiesStore.setSelectedEntityCoordinate(null);
						}
					}}
					role="button"
					tabindex="0"
				></sl-icon>
			</div>
			<div class="section-container">
				<div class="header">
					<p class="selected-title">
						{m['popup.feature']()} {selectedEntity?.osm_id}
					</p>

					{#if selectedEntity?.osm_id < 0 && (selectedEntity?.status === 'READY' || selectedEntity?.status === 'OPENED_IN_ODK')}
						<div
							onclick={() => (showDeleteEntityPopup = true)}
							onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && (showDeleteEntityPopup = true)}
							role="button"
							tabindex="0"
							class="icon group"
						>
							<sl-icon name="trash"></sl-icon>
							<p class="action">{m['popup.delete_feature']()}</p>
						</div>
					{/if}
				</div>

				<div class="section">
					<!-- Task ID -->
					<div class="detail-row">
						<p class="label">{m['popup.task_id']()}</p>
						<p class="value">{selectedEntity?.task_id}</p>
					</div>

					<!-- Unique ID -->
					<div class="detail-row">
						<p class="label">{m['dialog_entities_actions.unique_id']()}</p>
						<p class="value">{selectedEntity?.entity_id}</p>
					</div>

					<!-- Mapping status -->
					<div class="detail-row">
						<p class="label">{m['dialog_entities_actions.status']()}</p>
						<p class={`status ${selectedEntity?.status}`}>
							{m[`entity_states.${selectedEntity?.status}`]()}
						</p>
					</div>

					<!-- Created by current user -->
					{#if selectedEntity?.created_by && selectedEntity?.created_by === loginStore.getAuthDetails?.sub}
						<div class="detail-row">
							<p class="label">{m['dialog_entities_actions.created_by']()}</p>
							<p class="value font-bold">{m['dialog_entities_actions.you_created_this']()}</p>
						</div>
					{/if}

					<!-- Comments -->
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
												<sl-icon name="clock-history"></sl-icon>
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
											onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && (showCommentsPopup = true)}
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

				<!-- Action Buttons -->
				{#if projectData.status === projectStatus.PUBLISHED}
					<div class="entity-buttons">
						<!-- View Existing Data button (if available) -->
						{#if latestSubmissionId}
							<sl-button
								variant="default"
								size="small"
								class="entity-button"
								onclick={() => getAndDisplaySubmissionDetails(latestSubmissionId)}
								onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && getAndDisplaySubmissionDetails(latestSubmissionId)}
								role="button"
								tabindex="0"
							>
								<sl-icon slot="prefix" name="file-earmark-text"></sl-icon>
								<span>{m['dialog_entities_actions.view_existing_data']()}</span>
							</sl-button>
						{/if}

						<!-- Navigate Here + Collect Data buttons -->
						<div class="entity-button-row">
							<sl-button
								disabled={entityToNavigate?.entityId === selectedEntity?.entity_id}
								variant="default"
								size="small"
								class="entity-button"
								onclick={() => navigateToEntity()}
								onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && navigateToEntity()}
								role="button"
								tabindex="0"
							>
								<sl-icon slot="prefix" name="direction"></sl-icon>
								<span>{m['popup.navigate_here']()}</span>
							</sl-button>

							<sl-button
								loading={entitiesStore.updateEntityStatusLoading}
								variant="primary"
								size="small"
								class="entity-button"
								onclick={() => handleMapFeature()}
								onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && handleMapFeature()}
								role="button"
								tabindex="0"
							>
								<sl-icon slot="prefix" name="location"></sl-icon>
								<span>
									{commonStore.enableWebforms
										? m['dialog_entities_actions.collect_data']()
										: m['popup.map_in_odk']()}
								</span>
							</sl-button>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

{#if entitiesStore.selectedEntityCoordinate?.coordinate && entitiesStore.userLocationCoord}
	<sl-dialog
		bind:this={dialogRef}
		class="entity-dialog"
		open={toggleDistanceWarningDialog}
		onsl-hide={() => {
			toggleDistanceWarningDialog = false;
		}}
		noHeader
	>
		<div class="entity-dialog-content">
			<p class="entity-dialog-distance-confirm">
				{m['dialog_entities_actions.far_away_confirm']({
					distance: `${(
						distance(
							entitiesStore.selectedEntityCoordinate?.coordinate as Coord,
							entitiesStore.userLocationCoord as Coord,
							{ units: 'kilometers' },
						) * 1000
					).toFixed(2)}m`,
				})}
			</p>
			<div class="entity-dialog-actions">
				<sl-button
					variant="default"
					size="small"
					class="secondary"
					onclick={() => (toggleDistanceWarningDialog = false)}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') toggleDistanceWarningDialog = false;
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
	</sl-dialog>
{/if}

<sl-dialog
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
						<sl-icon name="clock-history"></sl-icon>
						<p>{comment?.created_at?.split(' ')[0]}</p>
					</div>
				</div>
				<p>
					{comment?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}
				</p>
			</div>
		{/each}
	</div>
</sl-dialog>

<!-- new entity delete confirmation -->
<sl-dialog
	bind:this={confirmationDialogRef}
	class="entity-delete-dialog"
	open={showDeleteEntityPopup}
	onsl-hide={() => (showDeleteEntityPopup = false)}
	noHeader
>
	<p class="content">{m['dialog_entities_actions.entity_delete_confirmation']()}</p>
	<div class="button-wrapper">
		<sl-button
			size="small"
			variant="default"
			class="secondary"
			onclick={() => (showDeleteEntityPopup = false)}
			outline
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') showDeleteEntityPopup = false;
			}}
			role="button"
			tabindex="0"
		>
			<span>{m['common.no']()}</span>
		</sl-button>
		<sl-button
			variant="primary"
			size="small"
			onclick={() => deleteNewFeature(selectedEntity?.entity_id)}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') deleteNewFeature(selectedEntity?.entity_id);
			}}
			role="button"
			tabindex="0"
		>
			<span>{m['common.yes']()}</span>
		</sl-button>
	</div>
</sl-dialog>

<!-- modal to view submission data on request -->
<sl-dialog
	bind:this={submissionDetailsRef}
	class="submission-details-dialog"
	open={showSubmissionDetailsPopup}
	onsl-hide={() => (showSubmissionDetailsPopup = false)}
	noHeader
>
	<div class="dialog-header">
		<h3>{m['dialog_entities_actions.view_existing_data']()}</h3>
		<sl-icon name="x" class="close-icon" onclick={() => submissionDetailsRef.hide()}></sl-icon>
	</div>

	{#if loadingSubmission}
		<div class="loading">
			<sl-spinner></sl-spinner>
		</div>
	{:else if submissionData && Object.keys(submissionData).length > 0}
		<div class="submission-details-content">
			{#each Object.entries(submissionData) as [key, value]}
				{#if isObject(value)}
					<details open>
						<summary class="section-title">{key}</summary>
						<div class="nested">
							{#each Object.entries(value) as [nestedKey, nestedValue]}
								{#if nestedValue !== null && nestedValue !== undefined}
									<div class="submission-item">
										<p class="label">{nestedKey}</p>
										<p class="value">{nestedValue}</p>
									</div>
								{/if}
							{/each}
							{#if !hasNonNullValues(value)}
								<p class="empty-section">No data available</p>
							{/if}
						</div>
					</details>
				{:else}
				{#if value}
					<div class="submission-item">
						<p class="label">{key}</p>
						<p class="value">{value}</p>
					</div>
				{/if}
				{/if}
			{/each}
		</div>
	{:else}
		<p class="empty">{m['dialog_entities_actions.no_data']()}</p>
	{/if}
</sl-dialog>
