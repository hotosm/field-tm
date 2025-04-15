<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import './page.css';
	import type { PageData } from './$types';
	import { onMount, onDestroy } from 'svelte';
	import type { ShapeStream } from '@electric-sql/client';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type SlTabGroup from '@shoelace-style/shoelace/dist/components/tab-group/tab-group.component.js';
	import type SlDialog from '@shoelace-style/shoelace/dist/components/dialog/dialog.component.js';

	import { m } from '$translations/messages.js';
	import ImportQrGif from '$assets/images/importQr.gif';
	import BottomSheet from '$lib/components/bottom-sheet.svelte';
	import MapComponent from '$lib/components/map/main.svelte';
	import QRCodeComponent from '$lib/components/qrcode.svelte';
	import BasemapComponent from '$lib/components/offline/basemaps.svelte';
	import DialogTaskActions from '$lib/components/dialog-task-actions.svelte';
	import DialogEntityActions from '$lib/components/dialog-entities-actions.svelte';
	import OdkWebFormsWrapper from '$lib/components/forms/wrapper.svelte';
	import type { ProjectTask } from '$lib/types';
	import { openOdkCollectNewFeature } from '$lib/odk/collect';
	import { convertDateToTimeAgo } from '$lib/utils/datetime';
	import { getTaskStore, getTaskEventStream } from '$store/tasks.svelte.ts';
	import { getEntitiesStatusStore, getEntityStatusStream, getNewBadGeomStream } from '$store/entities.svelte.ts';
	import More from '$lib/components/more/index.svelte';
	import { getProjectSetupStepStore, getCommonStore, getAlertStore } from '$store/common.svelte.ts';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import type { SlDrawer } from '@shoelace-style/shoelace';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let webFormsRef: HTMLElement | undefined = $state();
	let displayWebFormsDrawer = $state(false);

	let maplibreMap: maplibregl.Map | undefined = $state(undefined);
	let tabGroup: SlTabGroup;
	let openedActionModal: 'entity-modal' | 'task-modal' | null = $state(null);
	let infoDialogRef: SlDialog | null = $state(null);
	let isDrawEnabled: boolean = $state(false);
	let latestEventTime: string = $state('');
	let isGeometryCreationLoading: boolean = $state(false);
	
	const taskStore = getTaskStore();
	const entitiesStore = getEntitiesStatusStore();
	const commonStore = getCommonStore();
	const alertStore = getAlertStore();

	const taskEventStream = getTaskEventStream(data.projectId);
	const entityStatusStream = getEntityStatusStream(data.projectId);
	const newBadGeomStream = getNewBadGeomStream(data.projectId);

	const selectedEntityId = $derived(entitiesStore.selectedEntity);
	const latestEvent = $derived(taskStore.latestEvent);
	const commentMention = $derived(taskStore.commentMention);
	const enableWebforms = $derived(commonStore.config?.enableWebforms || false);

	// Update the geojson task states when a new event is added
	$effect(() => {
		if (latestEvent) {
			taskStore.appendTaskStatesToFeatcol(data.project.tasks);
		}
	});

	$effect(() => {
		let taskIdIndexMap: Record<number, number> = {};
		if (data?.project?.tasks && data?.project?.tasks?.length > 0) {
			data?.project?.tasks?.forEach((task: ProjectTask) => {
				taskIdIndexMap[task.id] = task.project_task_index;
			});
		}
		taskStore.setTaskIdIndexMap(taskIdIndexMap);
	});

	// update the latest time time every minute
	$effect(() => {
		const updateLatestTime = () => {
			if (latestEvent?.created_at) {
				latestEventTime = convertDateToTimeAgo(latestEvent.created_at);
			}
		};

		updateLatestTime();

		const interval = setInterval(updateLatestTime, 60000);

		return () => clearInterval(interval); // Cleanup interval on unmount
	});

	function zoomToTask(taskId: number, fitOptions?: Record<string, any> =  {duration: 0}) {
		const taskObj = data.project.tasks.find((task: ProjectTask) => task.id === taskId);

		if (!taskObj) return;
		// Set as selected task for buttons
		taskStore.setSelectedTaskId(taskObj.id, taskObj?.task_index);

		const taskPolygon = polygon(taskObj.outline.coordinates);
		const taskBuffer = buffer(taskPolygon, 5, { units: 'meters' });
		if (taskBuffer && maplibreMap) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			maplibreMap.fitBounds(taskBbox, fitOptions);
		}

		// Open the map tab
		tabGroup.show('map');
	}

	onMount(async () => {
		await entitiesStore.subscribeToNewBadGeom(newBadGeomStream);

		// In store/tasks.svelte.ts
		await taskStore.subscribeToEvents(taskEventStream);
		await taskStore.appendTaskStatesToFeatcol(data.project.tasks);
	});

	onDestroy(() => {
		taskEventStream?.unsubscribeAll();
	});

	$effect(() => {
		entitiesStore.syncEntityStatus(data.projectId);
	});

	$effect(() => {
		entitiesStore.entitiesList;
		let entityStatusStream: ShapeStream | undefined;

		if (entitiesStore.entitiesList?.length === 0) return;
		async function getEntityStatus() {
			entityStatusStream = getEntityStatusStream(data.projectId);
			await entitiesStore.subscribeToEntityStatusUpdates(entityStatusStream, entitiesStore.entitiesList);
		}

		getEntityStatus();
		return () => {
			entityStatusStream?.unsubscribeAll();
		};
	});
	const projectSetupStepStore = getProjectSetupStepStore();

	$effect(() => {
		// if project loaded for the first time, set projectSetupStep to 1 else get it from localStorage
		if (!localStorage.getItem(`project-${data.projectId}-setup`)) {
			// if webforms enabled, avoid project load in odk step
			if (enableWebforms) {
				localStorage.setItem(`project-${data.projectId}-setup`, projectSetupStepEnum['task_selection'].toString());
				projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['task_selection']);
			} else {
				localStorage.setItem(`project-${data.projectId}-setup`, projectSetupStepEnum['odk_project_load'].toString());
				projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['odk_project_load']);
			}
		} else {
			const projectStep = localStorage.getItem(`project-${data.projectId}-setup`);
			projectSetupStepStore.setProjectSetupStep(projectStep ? +projectStep : 0);
		}
		// if project loaded for the first time then show qrcode tab
		if (+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['odk_project_load']) {
			if (tabGroup) {
				tabGroup.updateComplete.then(() => {
					tabGroup.show('qrcode');
				});
			}
		}
	});

	let newFeatureDrawInstance: any = $state(null);
	let newFeatureGeom: any = $state(null);

	function cancelMapNewFeatureInODK() {
		newFeatureDrawInstance.clear();
		isDrawEnabled = false;
		newFeatureDrawInstance = null;
		newFeatureGeom = null;
	}

	async function mapNewFeatureInODK() {
		{
			/*
			1: create entity in ODK of newly created feature
			2: create geom record to show the feature on map
			3: pass entity uuid to ODK intent URL as a param 
			*/
		}
		try {
			isGeometryCreationLoading = true;
			const entity = await entitiesStore.createEntity(data.projectId, {
				type: 'FeatureCollection',
				features: [{ type: 'Feature', geometry: newFeatureGeom, properties: {} }],
			});
			await entitiesStore.createGeomRecord(data.projectId, {
				status: 'NEW',
				geojson: { type: 'Feature', geometry: newFeatureGeom, properties: { entity_id: entity.uuid } },
				project_id: data.projectId,
			});
			entitiesStore.syncEntityStatus(data.projectId);
			cancelMapNewFeatureInODK();
			openOdkCollectNewFeature(data?.project?.odk_form_id, entity.uuid);
		} catch (error) {
			alertStore.setAlert({ message: 'Unable to create entity', variant: 'danger' });
		} finally {
			isGeometryCreationLoading = false;
		}
	}
</script>

<!-- There is a new event to display in the top right corner -->
{#if latestEvent}
	<div
		id="notification-banner"
		class="floating-msg"
	>
		<b>{latestEventTime}</b>&nbsp;| {latestEvent.event}
		on task {taskStore.taskIdIndexMap[latestEvent.task_id]} by {latestEvent.username || 'anon'}
	</div>
{/if}

<!-- Alert shown when user is tagged on a comment when they is active -->
{#if commentMention}
	<div class="alert-msg">
		<sl-alert open={true} variant="neutral">
			<sl-icon slot="icon" name="chat"></sl-icon>
			<strong>{commentMention?.username} mentioned you on a comment</strong><br />
			<p>{commentMention?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}</p>
			<div class="page-content">
				<sl-button
					onclick={() => {
						taskStore.dismissCommentMention();
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							taskStore.dismissCommentMention();
						}
					}}
					role="button"
					tabindex="0"
					size="small"
				>
					<span>Dismiss</span>
				</sl-button>
				<sl-button
					onclick={() => {
						zoomToTask(commentMention.task_id, { duration: 0, padding:	{bottom: 325} });
						const osmId = commentMention?.comment?.split(' ')?.[1]?.replace('#featureId:', '');
						entitiesStore.setSelectedEntity(osmId);
						openedActionModal = 'entity-modal'
						taskStore.dismissCommentMention();
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							const osmId = commentMention?.comment?.split(' ')?.[1]?.replace('#featureId:', '');
							if (osmId) {
								entitiesStore.setSelectedEntity(osmId);
							}
							taskStore.dismissCommentMention();
						}
					}}
					role="button"
					tabindex="0"
					size="small"
				>
					<span>Tap to View</span>
				</sl-button>
			</div>
		</sl-alert>
	</div>
{/if}

<!-- The main page -->
<div class="main-page">
	<MapComponent
		setMapRef={(map) => {
			maplibreMap = map;
		}}
		toggleActionModal={(value) => {
			openedActionModal = value;
		}}
		projectOutlineCoords={data.project.outline.coordinates}
		projectId={data.projectId}
		entitiesUrl={data.project.data_extract_url}
		primaryGeomType={data.project.primary_geom_type}
		draw={isDrawEnabled}
		drawGeomType={data.project?.new_geom_type}
		handleDrawnGeom={(drawInstance, geom) => {
			newFeatureDrawInstance = drawInstance;
			newFeatureGeom = geom;
			// after drawing a feature, allow user to modify the drawn feature
			newFeatureDrawInstance.setMode('select');
		}}
	></MapComponent>

	{#if newFeatureGeom}
		<div class="proceed-dialog">
			<div class="proceed-dialog-content">
				<p>Is the geometry in the correct place?</p>
				<div class="buttons">
					<sl-button
						onclick={() => {
							cancelMapNewFeatureInODK();
						}}
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								cancelMapNewFeatureInODK();
							}
						}}
						role="button"
						tabindex="0"
						size="small"
						variant="secondary"
					>
						<span>{m['popup.cancel']()}</span>
					</sl-button>
					<sl-button
						onclick={() => mapNewFeatureInODK()}
						onkeydown={(e: KeyboardEvent) => {
							e.key === 'Enter' && mapNewFeatureInODK();
						}}
						role="button"
						tabindex="0"
						size="small"
						variant="primary"
						loading={isGeometryCreationLoading}
					>
						<span>PROCEED</span>
					</sl-button>
				</div>
			</div>
		</div>
	{/if}
	<!-- task action buttons popup -->
	<DialogTaskActions
		isTaskActionModalOpen={openedActionModal === 'task-modal'}
		toggleTaskActionModal={(value) => {
			openedActionModal = value ? 'task-modal' : null;
		}}
		selectedTab={commonStore.selectedTab}
		projectData={data?.project}
		clickMapNewFeature={() => {
			openedActionModal = null;
			isDrawEnabled = true;
		}}
	/>
	<DialogEntityActions
		isTaskActionModalOpen={openedActionModal === 'entity-modal'}
		toggleTaskActionModal={(value) => {
			openedActionModal = value ? 'entity-modal' : null;
		}}
		selectedTab={commonStore.selectedTab}
		projectData={data?.project}
		bind:displayWebFormsDrawer
	/>
	{#if commonStore.selectedTab !== 'map'}
		<BottomSheet onClose={() => tabGroup.show('map')}>
			{#if commonStore.selectedTab === 'events'}
				<More projectData={data?.project} zoomToTask={(taskId) => zoomToTask(taskId)}></More>
			{/if}
			{#if commonStore.selectedTab === 'offline'}
				<BasemapComponent projectId={data.project.id}></BasemapComponent>
			{/if}
			{#if commonStore.selectedTab === 'qrcode'}
				<QRCodeComponent class="map-qr" {infoDialogRef} projectName={data.project.name} projectOdkToken={data.project.odk_token}>
					<!-- Open ODK Button (Hide if it's project walkthrough step) -->
					{#if +(projectSetupStepStore.projectSetupStep || 0) !== projectSetupStepEnum['odk_project_load']}
						<sl-button
							size="small"
							variant="primary"
							href="odkcollect://form/{data.project.odk_form_id}"
						>
							<span>{m['odk.open']()}</span></sl-button
						>
					{/if}
				</QRCodeComponent>
			{/if}
		</BottomSheet>
		<hot-dialog
			bind:this={infoDialogRef}
			class="dialog-overview"
			no-header
		>
			<div class="content">
				<img
					src={ImportQrGif}
					alt="manual process of importing qr code gif"
					class="manual-qr-gif"
				/>
				<sl-button
					onclick={() => infoDialogRef?.hide()}
					onkeydown={(e: KeyboardEvent) => {
						e.key === 'Enter' && infoDialogRef?.hide();
					}}
					role="button"
					tabindex="0"
					size="small"
					variant="primary"
				>
					<span>CLOSE</span>
				</sl-button>
			</div>
		</hot-dialog>
	{/if}

	{#if displayWebFormsDrawer === false}
		<sl-tab-group
			class="web-forms-drawer"
			placement="bottom"
			no-scroll-controls
			onsl-tab-show={(e: CustomEvent<{ name: string }>) => {
				commonStore.setSelectedTab(e.detail.name);
				if (
					e.detail.name !== 'qrcode' &&
					+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['odk_project_load']
				) {
					localStorage.setItem(`project-${data.projectId}-setup`, projectSetupStepEnum['task_selection'].toString());
					projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['task_selection']);
				}
			}}
			bind:this={tabGroup}
		>
			<sl-tab slot="nav" panel="map">
				<hot-icon name="map"></hot-icon>
			</sl-tab>
			<sl-tab slot="nav" panel="offline">
				<hot-icon name="wifi-off"></hot-icon>
			</sl-tab>
			{#if (!enableWebforms)}
				<sl-tab slot="nav" panel="qrcode">
					<hot-icon name="qr-code"></hot-icon>
				</sl-tab>
			 {/if}
			<sl-tab slot="nav" panel="events">
				<hot-icon name="three-dots"></hot-icon>
			</sl-tab>
		</sl-tab-group>
	{/if}

	<OdkWebFormsWrapper
		bind:webFormsRef
		bind:display={displayWebFormsDrawer}
		projectId={data?.projectId}
		entityId={selectedEntityId || undefined}
		taskId={taskStore.selectedTaskIndex || undefined}
	/>
</div>

