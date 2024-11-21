<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import '@hotosm/ui/dist/hotosm-ui';
	import type { PageData } from '../$types';
	import { onMount, onDestroy } from 'svelte';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';

	import SlTabGroup from '@shoelace-style/shoelace/dist/components/tab-group/tab-group.component.js';
	// import EventCard from '$lib/components/event-card.svelte';
	import BottomSheet from '$lib/components/bottom-sheet.svelte';
	import TaskActionDialog from '$lib/components/task-action-dialog.svelte';
	import MapComponent from '$lib/components/map/main.svelte';
	import DialogTaskActions from '$lib/components/dialog-task-actions.svelte';

	import type { ProjectTask, ZoomToTaskEventDetail } from '$lib/types';
	import { generateQrCode, downloadQrCode } from '$lib/utils/qrcode';
	import { convertDateToTimeAgo } from '$lib/utils/datetime';
	import { getTaskStore, getTaskEventStream } from '$store/tasks.svelte.ts';
	import {
		entitiesStatusStore,
		selectedEntity,
		getEntityStatusStream,
		subscribeToEntityStatusUpdates,
	} from '$store/entities.svelte.ts';
	import More from '$lib/components/more/index.svelte';
	import { getProjectSetupStepStore } from '$store/common.svelte.ts';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	// $effect: ({ electric, project } = data)

	let mapComponent: maplibregl.Map | undefined = $state(undefined);
	let tabGroup: SlTabGroup;
	let selectedTab: string = $state('map');
	let isTaskActionModalOpen = $state(false);

	const taskStore = getTaskStore();
	const taskEventStream = getTaskEventStream(data.projectId);
	// Update the geojson task states when a new event is added
	$effect(() => {
		if (taskStore.latestEvent) {
			taskStore.appendTaskStatesToFeatcol(data.project.tasks);
		}
	});
	// const entityStatusStream = getEntityStatusStream(data.projectId);
	// $effect(() => {
	// 	if ($entitiesStatusStore) {
	// 		// TODO replace this with updating the entities geojson
	// 		console.log($entitiesStatusStore)
	// 	}
	// });

	let qrCodeData = $derived(generateQrCode(data.project.name, data.project.odk_token, 'REPLACE_ME_WITH_A_USERNAME'));

	function zoomToTask(taskId: number) {
		const taskObj = data.project.tasks.find((task: ProjectTask) => task.id === taskId);

		if (!taskObj) return;

		// Set as selected task for buttons
		taskStore.setSelectedTaskId(taskObj.id);

		const taskPolygon = polygon(taskObj.outline.coordinates);
		const taskBuffer = buffer(taskPolygon, 5, { units: 'meters' });
		if (taskBuffer && mapComponent) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			mapComponent.fitBounds(taskBbox, { duration: 500 });
		}

		// Open the map tab
		tabGroup.show('map');
	}

	onMount(async () => {
		// In store/tasks.svelte.ts
		await taskStore.subscribeToEvents(taskEventStream);
		await taskStore.appendTaskStatesToFeatcol(data.project.tasks);

		// In store/entities.ts
		// await subscribeToEntityStatusUpdates(entityStatusStream);
	});

	onDestroy(() => {
		taskEventStream.unsubscribeAll();
	});

	const projectSetupStepStore = getProjectSetupStepStore();

	$effect(() => {
		// if project loaded for the first time, set projectSetupStep to 1 else get it from localStorage
		if (!localStorage.getItem(`project-${data.projectId}-setup`)) {
			localStorage.setItem(`project-${data.projectId}-setup`, projectSetupStepEnum['odk_project_load']);
			projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['odk_project_load']);
		} else {
			projectSetupStepStore.setProjectSetupStep(localStorage.getItem(`project-${data.projectId}-setup`));
		}
		// if project loaded for the first time then show qrcode tab
		if (+projectSetupStepStore.projectSetupStep === projectSetupStepEnum['odk_project_load']) {
			tabGroup.updateComplete.then(() => {
				tabGroup.show('qrcode');
			});
		}
	});
</script>

<!-- There is a new event to display in the top right corner -->
{#if taskStore.latestEvent}
	<hot-card id="notification-banner" class="absolute z-10 top-18 right-0 font-sans hidden sm:flex">
		<b>{convertDateToTimeAgo(taskStore.latestEvent.created_at)}</b> | {taskStore.latestEvent.event}
		on task {taskStore.latestEvent.task_id} by {taskStore.latestEvent.username || 'anon'}
	</hot-card>
{/if}

<!-- The dialog should overlay with actions for a task -->
{#if taskStore.selectedTaskId}
	<TaskActionDialog state={taskStore.selectedTaskState} projectId={data.projectId} taskId={taskStore.selectedTaskId} />
{/if}

<!-- The main page -->
<div class="h-[calc(100svh-4.625rem)]">
	<MapComponent
		setMapRef={(map) => {
			mapComponent = map;
		}}
		toggleTaskActionModal={(value) => {
			isTaskActionModalOpen = value;
		}}
		projectOutlineCoords={data.project.outline.coordinates}
		projectId={data.projectId}
		entitiesUrl={data.project.data_extract_url}
	/>
	<!-- task action buttons popup -->
	<DialogTaskActions
		{isTaskActionModalOpen}
		toggleTaskActionModal={(value) => {
			isTaskActionModalOpen = value;
		}}
		{selectedTab}
		projectData={data?.project}
	/>

	{#if selectedTab !== 'map'}
		<BottomSheet onClose={() => tabGroup.show('map')}>
			{#if selectedTab === 'events'}
				<!-- {#if taskStore.events.length > 0}
					{#each taskStore.events as record}
						<EventCard
							{record}
							highlight={record.task_id === taskStore.selectedTaskId}
							on:zoomToTask={(e) => zoomToTask(e)}
						/>
					{/each}
				{/if} -->

				<More projectData={data?.project} zoomToTask={(taskId) => zoomToTask(taskId)} />
			{/if}
			{#if selectedTab === 'offline'}
				<span class="font-barlow-medium text-base">Coming soon!</span>
			{/if}
			{#if selectedTab === 'qrcode'}
				<div class="flex flex-col items-center p-4 space-y-4">
					<!-- Text above the QR code -->
					<div class="text-center w-full">
						<div class="font-bold text-lg font-barlow-medium">Scan this QR Code in ODK Collect</div>
					</div>

					<!-- QR Code Container -->
					<div class="flex justify-center w-full max-w-sm">
						<hot-qr-code value={qrCodeData} label="Scan to open ODK Collect" size="250"></hot-qr-code>
					</div>

					<!-- Download Button -->
					<sl-button onclick={downloadQrCode} size="small" class="secondary w-full max-w-[200px]">
						<hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
						></hot-icon>
						<span class="font-barlow-medium text-base uppercase">Download QR</span>
					</sl-button>

					<!-- Open ODK Button -->
					<sl-button
						size="small"
						class="primary w-full max-w-[200px]"
						href="odkcollect://form/{data.project.odk_form_id}{taskStore.selectedTaskId
							? `?task_filter=${taskStore.selectedTaskId}`
							: ''}"
					>
						<span class="font-barlow-medium text-base uppercase">Open ODK</span></sl-button
					>
				</div>
			{/if}
		</BottomSheet>
	{/if}

	<sl-tab-group
		class="z-9999 fixed bottom-0 left-0 right-0"
		placement="bottom"
		no-scroll-controls
		onsl-tab-show={(e: CustomEvent<{ name: string }>) => {
			selectedTab = e.detail.name;
			if (
				e.detail.name !== 'qrcode' &&
				+projectSetupStepStore.projectSetupStep === projectSetupStepEnum['odk_project_load']
			) {
				localStorage.setItem(`project-${data.projectId}-setup`, projectSetupStepEnum['task_selection']);
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

<!-- </div> -->

<style>
	:root {
		--nav-height: 4rem;
	}
	/* sl-tab-group {
		bottom: 0;
		width: 100%;
	} */

	/* sl-tab-group::part(base) {
		position: relative;
	} */

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

	/* The tab active indicator */
	/* sl-tab-group::part(active-tab-indicator) {
	} */

	/* Each tab item (icon) container */
	sl-tab {
		padding-left: 3vw;
		padding-right: 3vw;
	}

	/* The tab item icon */
	hot-icon {
		font-size: 2rem;
	}

	/* Floating map buttons
	hot-icon-button {
		font-size: 2rem;
	} */

	#notification-banner {
		--padding: 0.3rem;
	}
</style>
