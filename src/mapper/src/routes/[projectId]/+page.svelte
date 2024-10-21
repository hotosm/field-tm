<script lang="ts">
	import '@hotosm/ui/dist/hotosm-ui';
	import SlTabGroup from '@shoelace-style/shoelace/dist/components/tab-group/tab-group.component.js';
	import type { PageData } from '../$types';
	import { onMount, onDestroy } from 'svelte';
	import { writable } from 'svelte/store';
	import { Shape, ShapeStream } from '@electric-sql/client';
	import {
		MapLibre,
		GeoJSON,
		FillLayer,
		LineLayer,
		hoverStateFilter,
		SymbolLayer,
		NavigationControl,
		ScaleControl,
		Control,
		ControlGroup,
		ControlButton,
	} from 'svelte-maplibre';
	import type { FeatureCollection } from 'geojson';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';

	import type { ProjectData, ProjectTask, ZoomToTaskEventDetail } from '$lib/types';
	import { statusEnumLabelToValue, statusEnumValueToLabel } from '$lib/task-events';
	import {
		mapTask,
		finishTask,
		resetTask,
		// validateTask,
		// goodTask,
		// commentTask,
	} from '$lib/task-events';
	// import { createLiveQuery } from '$lib/live-query';
	import { generateQrCode, downloadQrCode } from '$lib/qrcode';
	import EventCard from '$lib/components/event-card.svelte';
	import Legend from '$lib/components/page/legend.svelte';
	import LayerSwitcher from '$lib/components/page/layer-switcher.svelte';
	import BottomSheet from '$lib/components/common/bottom-sheet.svelte';
	import Error from './+error.svelte';
	import '$styles/page.css';
	import BlackLockImg from '$assets/images/black-lock.png';
	import RedLockImg from '$assets/images/red-lock.png';
	import More from '$lib/components/page/more/index.svelte';
	import '$styles/button.css';
	import { GetDeviceRotation } from '$utilFunctions/getDeviceRotation';
	import LocationArcImg from '$assets/images/locationArc.png';
	import LocationDotImg from '$assets/images/locationDot.png';
	import { setAlert } from '$store/common';

	export let data: PageData;

	// $: ({ electric, project } = data)
	let map: maplibregl.Map | undefined;
	let loaded: boolean;
	let tabGroup: SlTabGroup;

	let selectedTab: string = 'map';
	let panelDisplay: string = 'none';
	$: panelDisplay = selectedTab === 'map' ? 'none' : 'block';
	let toggleTaskActionModal = false;

	// *** Task history sync *** //
	const taskFeatcolStore = writable<FeatureCollection>({ type: 'FeatureCollection', features: [] });
	const taskHistoryStream = new ShapeStream({
		url: 'http://localhost:7055/v1/shape/task_history',
		where: `project_id=${data.projectId}`,
	});
	const taskHistoryEvents = new Shape(taskHistoryStream);
	const taskEventArray = writable([]);
	const latestEvent = writable();
	$: if ($latestEvent) {
		updateTaskFeatures();
	}

	async function getLatestEventForTasks() {
		const taskEventMap = await taskHistoryEvents.value;
		const taskEventArrayFromApi = Array.from(taskEventMap.values());

		// Update the taskEventArray writable store
		taskEventArray.set(taskEventArrayFromApi);

		const latestActions = new Map();

		for (const taskData of taskEventArrayFromApi) {
			// Use the task_id as the key and action as the value
			latestActions.set(taskData.task_id, taskData.action);
		}

		return latestActions;
	}

	async function updateTaskFeatures() {
		const latestActions = await getLatestEventForTasks();

		const features = data.project.tasks.map((x: ProjectTask) => {
			const taskId = x.outline_geojson.id;
			const statusString = latestActions.get(taskId);
			const status = statusString ? statusEnumLabelToValue(statusString) : '0';

			return {
				...x.outline_geojson,
				properties: {
					...x.outline_geojson.properties,
					status,
				},
			};
		});

		taskFeatcolStore.set({
			type: 'FeatureCollection',
			features: features,
		});
	}

	// *** Selected task *** //
	$: qrCodeData = generateQrCode(data.project.project_info.name, data.project.odk_token, 'TEMP');

	let selectedTaskId = writable<number | null>(null);
	let featureClicked = writable(false);
	let selectedTask = writable<any>(null);
	let selectedTaskStatus = writable<string>('');

	$: selectedTask.set(data.project.tasks.find((task: ProjectTask) => task.id === $selectedTaskId));

	$: (async () => {
		const task = $selectedTask;
		if (task && task.id) {
			const latestActions = await getLatestEventForTasks();
			const statusLabel = latestActions.get(task.id);
			selectedTaskStatus.set(statusLabel ? statusLabel : 'RELEASED_FOR_MAPPING');
		} else {
			selectedTaskStatus.set('');
		}
	})();

	function zoomToTask(event: CustomEvent<ZoomToTaskEventDetail>) {
		const taskId = event.detail.taskId;
		const taskObj = data.project.tasks.find((task: ProjectTask) => task.id === taskId);

		if (!taskObj) return;

		// Set as selected task for buttons
		selectedTaskId.set(taskObj.id);

		const taskPolygon = polygon(taskObj.outline_geojson.geometry.coordinates);
		const taskBuffer = buffer(taskPolygon, 5, { units: 'meters' });
		if (taskBuffer && map) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			map.fitBounds(taskBbox, { duration: 500 });
		}

		// Open the map tab
		tabGroup.show('map');
	}

	// const mapStyle = {
	// 			"version": 8,
	// 			"name": "OpenStreetMap",
	// 			"sources": {
	// 			"osm": {
	// 				"type": "raster",
	// 				"tiles": ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
	// 				"tileSize": 256,
	// 				"attribution": "&copy; OpenStreetMap Contributors",
	// 				"maxzoom": 19
	// 			}
	// 			},
	// 			"layers": [
	// 			{
	// 				"id": "osm",
	// 				"type": "raster",
	// 				"source": "osm"
	// 			}
	// 			]
	// 		}

	onMount(async () => {
		const projectPolygon = polygon(data.project.outline_geojson.geometry.coordinates);
		const projectBuffer = buffer(projectPolygon, 100, { units: 'meters' });
		if (projectBuffer && map) {
			const projectBbox: [number, number, number, number] = bbox(projectBuffer) as [number, number, number, number];
			map.fitBounds(projectBbox, { duration: 0 });
		}

		taskHistoryEvents.subscribe((taskHistoryEvent) => {
			let newEvent;
			for (newEvent of taskHistoryEvent);
			if (newEvent) {
				latestEvent.set(newEvent[1]);
			}
		});
		// Do initial load of task features
		await updateTaskFeatures();
	});

	// geolocation
	let coords: [number, number];
	let rotationDeg: number | undefined;
	let toggleGeolocationStatus = false;
	let watchId;

	$: if (map && toggleGeolocationStatus) {
		// zoom to user's current location
		navigator.geolocation.getCurrentPosition((position) => {
			const currentCoordinate = [position.coords.longitude, position.coords.latitude];
			map.flyTo({
				center: currentCoordinate,
				essential: true,
				zoom: 18,
			});
		});

		// track users location
		watchId = navigator.geolocation.watchPosition(
			function (pos) {
				coords = [pos.coords.longitude, pos.coords.latitude];
			},
			function (error) {
				alert(`ERROR: ${error.message}`);
			},
			{
				enableHighAccuracy: true,
			},
		);
	} else {
		// stop tracking user's location on location toggle off
		navigator.geolocation.clearWatch(watchId);
	}
	const isFirefox = typeof InstallTrigger !== 'undefined';
	const isSafari =
		/constructor/i.test(window.HTMLElement) ||
		(function (p) {
			return p.toString() === '[object SafariRemoteNotification]';
			// @ts-ignore
		})(!window['safari'] || (typeof safari !== 'undefined' && window['safari'].pushNotification));

	// locationGeojson: to display point on the map
	let locationGeojson: FeatureCollection;
	$: locationGeojson = {
		type: 'FeatureCollection',
		features: [
			{
				type: 'Feature',
				geometry: {
					type: 'Point',
					coordinates: coords,
				},
				// firefox & safari doesn't support device orientation sensor, so if the browser any of the two set orientation to false
				properties: { orientation: !(isFirefox || isSafari) },
			},
		],
	};

	$: if (map && toggleGeolocationStatus) {
		if (isFirefox || isSafari) {
			// firefox & safari doesn't support device orientation sensor
			setAlert.set({
				variant: 'warning',
				message: "Unable to handle device orientation. Your browser doesn't support device orientation sensors.",
			});
		} else {
			// See the API specification at: https://w3c.github.io/orientation-sensor
			// We use referenceFrame: 'screen' because the web page will rotate when
			// the phone switches from portrait to landscape.
			const sensor = new AbsoluteOrientationSensor({
				frequency: 60,
				referenceFrame: 'screen',
			});
			sensor.addEventListener('reading', (event) => {
				rotationDeg = GetDeviceRotation(sensor.quaternion);
			});

			Promise.all([
				navigator.permissions.query({ name: 'accelerometer' }),
				navigator.permissions.query({ name: 'magnetometer' }),
				navigator.permissions.query({ name: 'gyroscope' }),
			]).then((results) => {
				if (results.every((result) => result.state === 'granted')) {
					sensor.start();
				} else {
				}
			});
		}
	}

	onDestroy(() => {
		taskHistoryStream.unsubscribeAll();
	});
</script>

{#if $latestEvent}
	<hot-card id="notification-banner" class="absolute z-10 top-18 right-0 font-sans hidden sm:flex">
		Latest: {$latestEvent.action_text}
	</hot-card>
{/if}

{#if $selectedTaskId}
	{#if $selectedTaskStatus == 'RELEASED_FOR_MAPPING'}
		<sl-tooltip content="MAP">
			<hot-icon-button
				name="play"
				class="fixed top-30 left-1/2 transform -translate-x-1/2 text-5xl z-10 bg-green-500 text-white rounded-full p-1"
				label="MAP"
				on:click={mapTask(data.projectId, $selectedTaskId)}
			></hot-icon-button>
		</sl-tooltip>
	{:else if $selectedTaskStatus == 'LOCKED_FOR_MAPPING'}
		<sl-tooltip content="FINISH">
			<hot-icon-button
				name="stop"
				class="fixed top-30 left-1/2 transform -translate-x-1/2 text-5xl z-10 bg-blue-500 text-white rounded-full p-1"
				label="FINISH"
				on:click={finishTask(data.projectId, $selectedTaskId)}
			></hot-icon-button>
		</sl-tooltip>
	{:else if $selectedTaskStatus == 'MARKED_MAPPED'}
		<sl-tooltip content="RESET">
			<hot-icon-button
				name="arrow-counterclockwise"
				class="fixed top-30 left-1/2 transform -translate-x-1/2 text-5xl z-10 bg-yellow-500 text-white rounded-full p-1"
				label="RESET"
				on:click={resetTask(data.projectId, $selectedTaskId)}
			></hot-icon-button>
		</sl-tooltip>
	{/if}
{/if}

<div class="h-[calc(100vh-4.625rem)]">
	<MapLibre
		bind:map
		bind:loaded
		style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
		class="flex-auto w-full sm:aspect-video h-[calc(100%-4rem)]"
		center={[0, 0]}
		zoom={2}
		attributionControl={false}
		on:click={(e) => {
			featureClicked.subscribe((fClicked) => {
				if (!fClicked) {
					selectedTaskId.set(null);
				}
				featureClicked.set(false);
				toggleTaskActionModal = false;
			});
		}}
		images={[
			{ id: '1', url: BlackLockImg },
			{ id: '3', url: RedLockImg },
			{ id: 'locationArc', url: LocationArcImg },
			{ id: 'locationDot', url: LocationDotImg },
		]}
	>
		<NavigationControl position="top-left" />
		<ScaleControl />
		<Control class="flex flex-col gap-y-2" position="top-left">
			<ControlGroup>
				<ControlButton on:click={() => (toggleGeolocationStatus = !toggleGeolocationStatus)}
					><hot-icon
						name="geolocate"
						class={`!text-[1.2rem] cursor-pointer  duration-200 ${toggleGeolocationStatus ? 'text-red-600' : 'text-[#52525B]'}`}
					></hot-icon></ControlButton
				>
			</ControlGroup></Control
		>
		{#if toggleGeolocationStatus}
			<GeoJSON data={locationGeojson} id="point">
				<SymbolLayer
					applyToClusters={false}
					hoverCursor="pointer"
					layout={{
						// if orientation true (meaning the browser supports device orientation sensor show location dot with orientation sign)
						'icon-image': ['case', ['==', ['get', 'orientation'], true], 'locationArc', 'locationDot'],
						'icon-allow-overlap': true,
						'text-field': '{mag}',
						'text-offset': [0, -2],
						'text-size': 12,
						'icon-rotate': rotationDeg || 0, // rotate location icon acc to device orientation
						'icon-rotation-alignment': 'map',
						'icon-size': 0.5,
					}}
				/>
			</GeoJSON>
		{/if}
		<GeoJSON id="states" data={$taskFeatcolStore} promoteId="TASKS">
			<FillLayer
				hoverCursor="pointer"
				paint={{
					'fill-color': [
						'match',
						['get', 'status'],
						'0',
						'#ffffff',
						'1',
						'#008099',
						'2',
						'#ade6ef',
						'3',
						'#fceca4',
						'4',
						'#40ac8c',
						'5',
						'#d73f3e',
						'#c5fbf5', // default color if no match is found
					],
					'fill-opacity': hoverStateFilter(0.5, 0),
				}}
				beforeLayerType="symbol"
				manageHoverState
				on:click={(e) => {
					featureClicked.set(true);
					const clickedTask = e.detail.features?.[0]?.properties?.uid;
					selectedTaskId.set(clickedTask);
					toggleTaskActionModal = true;
				}}
			/>
			<LineLayer
				layout={{ 'line-cap': 'round', 'line-join': 'round' }}
				paint={{
					'line-color': ['case', ['==', ['get', 'uid'], $selectedTaskId], '#fa1100', '#0fffff'],
					'line-width': 3,
					'line-opacity': ['case', ['==', ['get', 'uid'], $selectedTaskId], 1, 0.35],
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
			<SymbolLayer
				applyToClusters={false}
				hoverCursor="pointer"
				layout={{
					'icon-image': ['case', ['==', ['get', 'status'], '1'], '1', ['==', ['get', 'status'], '3'], '3', ''],
					'icon-allow-overlap': true,
				}}
			/>
		</GeoJSON>
		<div class="absolute right-3 bottom-3 sm:right-5 sm:bottom-5">
			<LayerSwitcher />
			<Legend />
		</div>
	</MapLibre>

	{#if $selectedTaskId && selectedTab === 'map' && toggleTaskActionModal && ($selectedTaskStatus === 'RELEASED_FOR_MAPPING' || $selectedTaskStatus === 'LOCKED_FOR_MAPPING')}
		<div class="flex justify-center !w-[100vw] absolute bottom-[4rem] left-0 pointer-events-none z-50">
			<div
				class="bg-white w-[100vw] h-fit font-barlow-regular w-[100vw] md:max-w-[580px] pointer-events-auto px-4 pb-3 sm:pb-4 rounded-t-3xl"
			>
				<div class="flex justify-between items-center">
					<p class="text-[#333] text-xl font-barlow-semibold leading-0 pt-2">Task #{$selectedTaskId}</p>
					<hot-icon
						name="close"
						class="!text-[1.5rem] text-[#52525B] cursor-pointer hover:text-red-600 duration-200"
						on:click={() => (toggleTaskActionModal = false)}
					></hot-icon>
				</div>

				{#if $selectedTaskStatus == 'RELEASED_FOR_MAPPING'}
					<p class="my-4 sm:my-6">Do you want to start mapping task #{$selectedTaskId}?</p>
					<div class="flex justify-center gap-x-2">
						<sl-button
							size="small"
							variant="default"
							class="secondary"
							on:click={() => (toggleTaskActionModal = false)}
							outline><span class="font-barlow-medium text-sm">CANCEL</span></sl-button
						>
						<sl-button
							variant="default"
							size="small"
							class="primary"
							on:click={mapTask(data.projectId, $selectedTaskId)}
						>
							<div class="flex items-center gap-1">
								<hot-icon name="location" class="!text-[1rem] text-white cursor-pointer duration-200"></hot-icon>
								<p class="font-barlow-medium text-sm leading-[0]">START MAPPING</p>
							</div>
						</sl-button>
					</div>
				{:else if $selectedTaskStatus == 'LOCKED_FOR_MAPPING'}
					<p class="my-4 sm:my-6">Task #{$selectedTaskId} has been locked, Is the task completely mapped?</p>
					<div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
						<sl-button
							on:click={resetTask(data.projectId, $selectedTaskId)}
							variant="default"
							outline
							size="small"
							class="secondary"
						>
							<div class="flex items-center gap-1">
								<hot-icon
									name="close"
									class="!text-[1rem] text-[#d73f37] cursor-pointer duration-200 hover:text-[#b91c1c]"
									on:click={() => (toggleTaskActionModal = false)}
								></hot-icon>
								<p class="font-barlow-medium text-sm leading-[0]">CANCEL MAPPING</p>
							</div></sl-button
						>
						<sl-button
							on:click={finishTask(data.projectId, $selectedTaskId)}
							variant="default"
							size="small"
							class="primary"
							><div class="flex items-center gap-1">
								<hot-icon
									name="check"
									class="!text-[1rem] text-white cursor-pointer duration-200"
									on:click={() => (toggleTaskActionModal = false)}
								></hot-icon>
								<p class="font-barlow-medium text-sm leading-[0]">COMPLETE MAPPING</p>
							</div></sl-button
						>
						<sl-button variant="default" size="small" class="gray col-span-2 sm:col-span-1">
							<p class="font-barlow-medium text-sm leading-[0]">GO TO ODK</p>
						</sl-button>
					</div>
					<div class="flex justify-center gap-2"></div>
				{/if}
			</div>
		</div>
	{/if}

	{#if selectedTab !== 'map'}
		<BottomSheet
			onClose={() => {
				tabGroup.show('map');
			}}
		>
			{#if selectedTab === 'events'}
				<!-- {#if $taskEventArray.length > 0}
					{#each $taskEventArray as record}
						<EventCard {record} highlight={record.task_id === $selectedTaskId} on:zoomToTask={(e) => zoomToTask(e)}
						></EventCard>
					{/each}
				{/if} -->

				<!-- uncomment More to view stacked component containing comment, instructions, activities -->
				<More />
			{/if}
			{#if selectedTab === 'offline'}
				<div>TODO stuff here</div>
			{/if}
			{#if selectedTab === 'qrcode'}
				<div class="flex flex-col items-center p-4 space-y-4">
					<!-- Text above the QR code -->
					<div class="text-center w-full">
						<div class=" font-bold text-lg font-barlow-medium">Scan this QR Code in ODK Collect</div>
					</div>

					<!-- QR Code Container -->
					<div class="flex justify-center w-full max-w-sm">
						<hot-qr-code value={qrCodeData} label="Scan to open ODK Collect" size="250" radius="0.5" errorCorrection="L"
						></hot-qr-code>
					</div>

					<!-- Download Button -->
					<div class="w-full max-w-sm text-center">
						<hot-icon-button
							name="download"
							label="Download QRCode"
							on:click={downloadQrCode(data.project.project_info.name, qrCodeData)}>Download</hot-icon-button
						>
					</div>

					<!-- Open ODK Button -->
					<div class="w-full max-w-sm text-center">
						<sl-button
							class="primary"
							href="odkcollect://form/{data.project.xform_id}{$selectedTaskId ? `?task_filter=${$selectedTaskId}` : ''}"
							><span class="font-barlow-medium text-base">Open ODK</span></sl-button
						>
					</div>
				</div>
			{/if}
		</BottomSheet>
	{/if}

	<sl-tab-group
		class="z-9999 fixed bottom-0 left-0 right-0"
		placement="bottom"
		no-scroll-controls
		on:sl-tab-show={(e) => {
			selectedTab = e.detail.name;
		}}
		style="--panel-display: none"
		bind:this={tabGroup}
	>
		<sl-tab slot="nav" panel="map">
			<hot-icon name="map" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
		</sl-tab>
		<sl-tab slot="nav" panel="events">
			<hot-icon name="list" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
		</sl-tab>
		<sl-tab slot="nav" panel="offline">
			<hot-icon name="wifi-off" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
		</sl-tab>
		<sl-tab slot="nav" panel="qrcode">
			<hot-icon name="qr-code" class="!text-[1.7rem] !sm:text-[2rem]"></hot-icon>
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
