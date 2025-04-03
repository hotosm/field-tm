<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
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

	// Update the geojson task states when a new event is added
	$effect(() => {
		if (taskStore.latestEvent) {
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
			if (taskStore.latestEvent?.created_at) {
				latestEventTime = convertDateToTimeAgo(taskStore.latestEvent.created_at);
			}
		};

		updateLatestTime();

		const interval = setInterval(updateLatestTime, 60000);

		return () => clearInterval(interval); // Cleanup interval on unmount
	});

	function zoomToTask(taskId: number) {
		const taskObj = data.project.tasks.find((task: ProjectTask) => task.id === taskId);

		if (!taskObj) return;

		// Set as selected task for buttons
		taskStore.setSelectedTaskId(taskObj.id, taskObj?.task_index);

		const taskPolygon = polygon(taskObj.outline.coordinates);
		const taskBuffer = buffer(taskPolygon, 5, { units: 'meters' });
		if (taskBuffer && maplibreMap) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			maplibreMap.fitBounds(taskBbox, { duration: 500 });
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
			localStorage.setItem(`project-${data.projectId}-setup`, projectSetupStepEnum['odk_project_load'].toString());
			projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['odk_project_load']);
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
{#if taskStore.latestEvent}
	<div
		id="notification-banner"
		class="absolute z-10 top-15 sm:top-18.8 right-0 font-sans flex bg-white text-black bg-opacity-70 text-sm sm:text-base px-1 rounded-bl-md"
	>
		<b class="">{latestEventTime}</b>&nbsp;| {taskStore.latestEvent.event}
		on task {taskStore.taskIdIndexMap[taskStore.latestEvent.task_id]} by {taskStore.latestEvent.username || 'anon'}
	</div>
{/if}

<!-- The main page -->
<div class="h-[calc(100svh-3.699rem)] sm:h-[calc(100svh-4.625rem)] font-barlow" style="position: relative">
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
		<div class="absolute inset-0 z-20 flex items-center justify-center translate-y-[-5rem] pointer-events-none">
			<div class="pointer-events-auto bg-white px-4 py-2 rounded-md shadow-lg w-fit max-w-[65%]">
				<p class="mb-2">Is the geometry in the correct place?</p>
				<div class="flex gap-2 justify-end">
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
						class="secondary w-fit"
					>
						<span class="font-barlow font-medium text-xs uppercase">{m['popup.cancel']()}</span>
					</sl-button>
					<sl-button
						onclick={() => mapNewFeatureInODK()}
						onkeydown={(e: KeyboardEvent) => {
							e.key === 'Enter' && mapNewFeatureInODK();
						}}
						role="button"
						tabindex="0"
						size="small"
						class="w-fit"
						variant="primary"
						loading={isGeometryCreationLoading}
					>
						<span class="font-barlow font-medium text-xs uppercase">PROCEED</span>
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
				<QRCodeComponent {infoDialogRef} projectName={data.project.name} projectOdkToken={data.project.odk_token}>
					<!-- Open ODK Button (Hide if it's project walkthrough step) -->
					{#if +(projectSetupStepStore.projectSetupStep || 0) !== projectSetupStepEnum['odk_project_load']}
						<sl-button
							size="small"
							variant="primary"
							class="w-full max-w-[200px]"
							href="odkcollect://form/{data.project.odk_form_id}"
						>
							<span class="font-barlow font-medium text-base uppercase">{m['odk.open']()}</span></sl-button
						>
					{/if}
				</QRCodeComponent>
			{/if}
		</BottomSheet>
		<hot-dialog
			bind:this={infoDialogRef}
			class="dialog-overview"
			style="--width: fit; --body-spacing: 0.5rem"
			no-header
		>
			<div class="flex flex-col gap-[0.5rem]">
				<img
					src={ImportQrGif}
					alt="manual process of importing qr code gif"
					style="border: 1px solid #ededed;"
					class="h-[70vh]"
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
					class="w-fit ml-auto"
				>
					<span class="font-barlow font-medium text-SM uppercase">CLOSE</span>
				</sl-button>
			</div>
		</hot-dialog>
	{/if}

	{#if displayWebFormsDrawer === false}
		<sl-tab-group
			class={'z-9999 fixed bottom-0 left-0 right-0'}
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
			style="--panel-display: none"
			bind:this={tabGroup}
		>
			<sl-tab slot="nav" panel="map">
				<hot-icon name="map" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
			</sl-tab>
			<sl-tab slot="nav" panel="offline">
				<hot-icon name="wifi-off" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
			</sl-tab>
			<sl-tab slot="nav" panel="qrcode">
				<hot-icon name="qr-code" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
			</sl-tab>
			<sl-tab slot="nav" panel="events">
				<hot-icon name="three-dots" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
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

<style>
	:root {
		--nav-height: 4rem;
	}

	sl-tab-group::part(body) {
		display: var(--panel-display);
		position: fixed;
		bottom: var(--nav-height);
		width: 100%;
		height: calc(80vh - var(--nav-height));
		min-height: 25vh;
		max-height: 90vh;
		background-color: rgba(255, 255, 255, 1);
		overflow: auto;
		border-top-left-radius: 1rem;
		border-top-right-radius: 1rem;
		z-index: 100; /* Map is using z-index 10 */
	}

	/* The tab selector */
	sl-tab-group::part(nav) {
		display: flex;
		justify-content: center;
		background-color: var(--hot-white);
		height: var(--nav-height);
		background-color: white;
	}

	/* Each tab item (icon) container */
	sl-tab {
		padding-left: 3vw;
		padding-right: 3vw;
	}

	/* The tab item icon */
	hot-icon {
		font-size: 2rem;
	}

	#notification-banner {
		--padding: 0.3rem;
	}
</style>
