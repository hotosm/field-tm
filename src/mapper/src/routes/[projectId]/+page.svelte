<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import '@hotosm/ui/dist/hotosm-ui';
	import type { PageData } from '../$types';
	import { onMount, onDestroy } from 'svelte';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import ImportQrGif from '$assets/images/importQr.gif';

	import SlTabGroup from '@shoelace-style/shoelace/dist/components/tab-group/tab-group.component.js';
	import SlDialog from '@shoelace-style/shoelace/dist/components/dialog/dialog.component.js';
	import BottomSheet from '$lib/components/bottom-sheet.svelte';
	import MapComponent from '$lib/components/map/main.svelte';
	import QRCodeComponent from '$lib/components/qrcode.svelte';
	import BasemapComponent from '$lib/components/offline/basemaps.svelte';
	import DialogTaskActions from '$lib/components/dialog-task-actions.svelte';
	import DialogEntityActions from '$lib/components/dialog-entities-actions.svelte';
	import type { ProjectTask } from '$lib/types';
	import { openOdkCollectNewFeature } from '$lib/odk/collect';
	import { convertDateToTimeAgo } from '$lib/utils/datetime';
	import { getTaskStore, getTaskEventStream } from '$store/tasks.svelte.ts';
	import { getEntitiesStatusStore, getEntityStatusStream } from '$store/entities.svelte.ts';
	import More from '$lib/components/more/index.svelte';
	import { getProjectSetupStepStore, getCommonStore } from '$store/common.svelte.ts';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import type { ShapeStream } from '@electric-sql/client';

	const API_URL = import.meta.env.VITE_API_URL;

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let maplibreMap: maplibregl.Map | undefined = $state(undefined);
	let tabGroup: SlTabGroup;
	let openedActionModal: 'entity-modal' | 'task-modal' | null = $state(null);
	let infoDialogRef: SlDialog | null = $state(null);
	let isDrawEnabled: boolean = $state(false);
	let latestEventTime: string = $state('');

	const taskStore = getTaskStore();
	const entitiesStore = getEntitiesStatusStore();
	const commonStore = getCommonStore();

	const taskEventStream = getTaskEventStream(data.projectId);

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
		// In store/tasks.svelte.ts
		await taskStore.subscribeToEvents(taskEventStream);
		await taskStore.appendTaskStatesToFeatcol(data.project.tasks);
	});

	onDestroy(() => {
		taskEventStream?.unsubscribeAll();
	});

	$effect(() => {
		let entityStatusStream: ShapeStream | undefined;

		async function getEntityStatus() {
			const entityStatusResponse = await fetch(`${API_URL}/projects/${data.projectId}/entities/statuses`, {
				credentials: 'include',
			});
			const response = await entityStatusResponse.json();
			entityStatusStream = getEntityStatusStream(data.projectId);
			await entitiesStore.subscribeToEntityStatusUpdates(entityStatusStream, response);
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
			tabGroup.updateComplete.then(() => {
				tabGroup.show('qrcode');
			});
		}
	});
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
<div class="h-[calc(100svh-3.699rem)] sm:h-[calc(100svh-4.625rem)]">
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
		draw={isDrawEnabled}
		handleDrawnGeom={(geom) => {
			isDrawEnabled = false;
			openOdkCollectNewFeature(data?.project?.odk_form_id, geom);
		}}
	></MapComponent>
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
							class="primary w-full max-w-[200px]"
							href="odkcollect://form/{data.project.odk_form_id}{taskStore.selectedTaskId
								? `?task_filter=${taskStore.selectedTaskId}`
								: ''}"
						>
							<span class="font-barlow font-medium text-base uppercase">Open ODK</span></sl-button
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
					class="primary w-fit ml-auto"
				>
					<span class="font-barlow font-medium text-SM uppercase">CLOSE</span>
				</sl-button>
			</div>
		</hot-dialog>
	{/if}

	<sl-tab-group
		class="z-9999 fixed bottom-0 left-0 right-0"
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
