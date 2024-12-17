<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
	import '@hotosm/ui/dist/hotosm-ui';
	import { onMount } from 'svelte';
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
	import maplibre from 'maplibre-gl';
	import MaplibreTerradrawControl from '@watergis/maplibre-gl-terradraw';
	import { Protocol } from 'pmtiles';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type { GeoJSON as GeoJSONType, Position, Geometry as GeoJSONGeometry } from 'geojson';

	import LocationArcImg from '$assets/images/locationArc.png';
	import LocationDotImg from '$assets/images/locationDot.png';
	import BlackLockImg from '$assets/images/black-lock.png';
	import RedLockImg from '$assets/images/red-lock.png';
	import Arrow from '$assets/images/arrow.png';

	import Legend from '$lib/components/map/legend.svelte';
	import LayerSwitcher from '$lib/components/map/layer-switcher.svelte';
	import Geolocation from '$lib/components/map/geolocation.svelte';
	import FlatGeobuf from '$lib/components/map/flatgeobuf-layer.svelte';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getProjectSetupStepStore, getProjectBasemapStore } from '$store/common.svelte.ts';
	// import { entityFeatcolStore, selectedEntityId } from '$store/entities';
	import { readFileFromOPFS } from '$lib/fs/opfs.ts';
	import { loadOfflinePmtiles } from '$lib/utils/basemaps.ts';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import { baseLayers, osmStyle, pmtilesStyle } from '$constants/baseLayers.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';

	type bboxType = [number, number, number, number];

	interface Props {
		projectOutlineCoords: Position[][];
		entitiesUrl: string;
		toggleActionModal: (value: 'task-modal' | 'entity-modal' | null) => void;
		projectId: number;
		setMapRef: (map: maplibregl.Map | undefined) => void;
		draw?: boolean;
		handleDrawnGeom?: ((geojson: GeoJSONGeometry) => void) | null;
	}

	let {
		projectOutlineCoords,
		entitiesUrl,
		toggleActionModal,
		projectId,
		setMapRef,
		draw = false,
		handleDrawnGeom,
	}: Props = $props();

	const taskStore = getTaskStore();
	const projectSetupStepStore = getProjectSetupStepStore();
	const entitiesStore = getEntitiesStatusStore();
	const projectBasemapStore = getProjectBasemapStore();

	let map: maplibregl.Map | undefined = $state();
	let loaded: boolean = $state(false);
	let selectedBaselayer: string = $state('OSM');
	let taskAreaClicked: boolean = $state(false);
	let toggleGeolocationStatus: boolean = $state(false);
	let toggleNavigationMode: boolean = $state(false);
	let projectSetupStep = $state(null);
	// Trigger adding the PMTiles layer to baselayers, if PmtilesUrl is set
	let allBaseLayers: maplibregl.StyleSpecification[] = $derived(
		projectBasemapStore.projectPmtilesUrl
			? [
					...baseLayers,
					{
						...pmtilesStyle,
						sources: {
							...pmtilesStyle.sources,
							pmtiles: {
								...pmtilesStyle.sources.pmtiles,
								url: projectBasemapStore.projectPmtilesUrl,
							},
						},
					},
				]
			: baseLayers,
	);
	// // This does not work! Infinite looping
	// // Trigger adding the PMTiles layer to baselayers, if PmtilesUrl is set
	// $effect(() => {
	// 	if (projectBasemapStore.projectPmtilesUrl) {
	// 		const layers = allBaseLayers
	// 		.filter((layer) => layer.name !== "PMTiles")
	// 		.push(
	// 			{
	// 				...pmtilesStyle,
	// 				sources: {
	// 					...pmtilesStyle.sources,
	// 					pmtiles: {
	// 						...pmtilesStyle.sources.pmtiles,
	// 						url: projectBasemapStore.projectPmtilesUrl,
	// 					},
	// 				},
	// 			},
	// 		)
	// 		allBaseLayers = layers;
	// 	}
	// })
	let displayDrawHelpText: boolean = $state(false);
	const drawControl = new MaplibreTerradrawControl({
		modes: [
			'point',
			// 'polygon',
			// 'linestring',
			// 'delete',
		],
		// Note We do not open the toolbar options, allowing the user
		// to simply click with a pre-defined mode active
		// open: true,
	});

	$effect(() => {
		projectSetupStep = +projectSetupStepStore.projectSetupStep;
	});

	// set the map ref to parent component
	$effect(() => {
		if (map) {
			setMapRef(map);
		}
	});

	// using this function since outside click of entity layer couldn't be tracked via FillLayer
	function handleMapClick(e: maplibregl.MapMouseEvent) {
		// returns list of features of entity layer present on that clicked point
		const clickedEntityFeature = map?.queryRenderedFeatures(e.point, {
			layers: ['entity-fill-layer'],
		});
		// returns list of features of task layer present on that clicked point
		const clickedTaskFeature = map?.queryRenderedFeatures(e.point, {
			layers: ['task-fill-layer'],
		});

		// if clicked point contains entity then set it's osm id else set null to store
		if (clickedEntityFeature && clickedEntityFeature?.length > 0) {
			const clickedEntityId = clickedEntityFeature[0]?.properties?.osm_id;
			entitiesStore.setSelectedEntity(clickedEntityId);
		} else {
			entitiesStore.setSelectedEntity(null);
		}

		// if clicked point contains task layer
		if (clickedTaskFeature && clickedTaskFeature?.length > 0) {
			taskAreaClicked = true;
			const clickedTaskId = clickedTaskFeature[0]?.properties?.fid;
			taskStore.setSelectedTaskId(clickedTaskId, clickedTaskFeature[0]?.properties?.task_index);
			if (+projectSetupStepStore.projectSetupStep === projectSetupStepEnum['task_selection']) {
				localStorage.setItem(`project-${projectId}-setup`, projectSetupStepEnum['complete_setup']);
				projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['complete_setup']);
			}
		}

		if (clickedEntityFeature && clickedEntityFeature?.length > 0) {
			toggleActionModal('entity-modal');
		} else if (clickedTaskFeature && clickedTaskFeature?.length > 0) {
			toggleActionModal('task-modal');
		} else {
			toggleActionModal(null);
		}
	}

	$effect(() => {
		if (map) {
			map.on('click', handleMapClick);
			// Cleanup on component unmount
			return () => {
				map?.off('click', handleMapClick);
			};
		}
	});

	// Workaround due to bug in @watergis/mapbox-gl-terradraw
	function removeTerraDrawLayers() {
		if (map) {
			if (map.getLayer('td-point')) map.removeLayer('td-point');
			if (map.getSource('td-point')) map.removeSource('td-point');

			if (map.getLayer('td-linestring')) map.removeLayer('td-linestring');
			if (map.getSource('td-linestring')) map.removeSource('td-linestring');

			if (map.getLayer('td-polygon')) map.removeLayer('td-polygon');
			if (map.getSource('td-polygon')) map.removeSource('td-polygon');

			if (map.getLayer('td-polygon-outline')) map.removeLayer('td-polygon-outline');
			if (map.getSource('td-polygon-outline')) map.removeSource('td-polygon-outline');
		}
	}
	// Add draw layer & handle emitted geom
	$effect(() => {
		if (draw) {
			map?.addControl(drawControl, 'top-left');
			displayDrawHelpText = true;

			const drawInstance = drawControl.getTerraDrawInstance();
			if (drawInstance && handleDrawnGeom) {
				drawInstance.start();
				drawInstance.setMode('point');

				drawInstance.on('finish', (id: string, _context: any) => {
					// Save the drawn geometry location, then delete all geoms from store
					const features: { id: string; geometry: GeoJSONGeometry }[] = drawInstance.getSnapshot();
					const drawnFeature = features.find((geom) => geom.id === id);
					let firstGeom: GeoJSONGeometry = null;
					if (drawnFeature && drawnFeature.geometry) {
						firstGeom = drawnFeature.geometry;
					} else {
						console.error(`Feature with id ${id} not found or has no geometry.`);
					}
					drawInstance.stop();

					if (firstGeom) {
						removeTerraDrawLayers();
						handleDrawnGeom(firstGeom);
					}
				});
			}
		} else {
			removeTerraDrawLayers();
			map?.removeControl(drawControl);
			displayDrawHelpText = false;
		}
	});

	// Fit the map bounds to the project area
	$effect(() => {
		if (map && projectOutlineCoords) {
			const projectPolygon = polygon(projectOutlineCoords);
			const projectBuffer = buffer(projectPolygon, 100, { units: 'meters' });
			if (projectBuffer) {
				const projectBbox: bboxType = bbox(projectBuffer) as bboxType;
				map.fitBounds(projectBbox, { duration: 0 });
			}
		}
	});

	function addStatusToGeojsonProperty(geojsonData: GeoJSONType) {
		return {
			...geojsonData,
			features: geojsonData.features.map((feature) => {
				const entity = entitiesStore.entitiesStatusList.find((entity) => entity.osmid === feature.properties.osm_id);
				return {
					...feature,
					properties: {
						...feature.properties,
						status: entity?.status,
						entity_id: entity?.entity_id,
					},
				};
			}),
		};
	}

	function zoomToProject() {
		const taskBuffer = buffer(taskStore.featcol, 5, { units: 'meters' });
		if (taskBuffer && map) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			map?.fitBounds(taskBbox, { duration: 500 });
		}
	}

	// if navigation mode on, tilt map by 50 degrees
	$effect(() => {
		if (toggleNavigationMode && toggleGeolocationStatus) {
			map?.setPitch(50);
		} else {
			map?.setPitch(0);
		}
	});

	// if map loaded, turn on geolocation by default
	$effect(() => {
		if (loaded) toggleGeolocationStatus = true;
	});

	onMount(async () => {
		// Register pmtiles protocol
		if (!maplibre.config.REGISTERED_PROTOCOLS.hasOwnProperty('pmtiles')) {
			let protocol = new Protocol();
			maplibre.addProtocol('pmtiles', protocol.tile);
		}

		// Attempt loading OPFS PMTiles layers on first load
		// note that this sets projectBasemapStore.projectPmtilesUrl
		const offlineBasemapFile = await readFileFromOPFS(`${projectId}/basemap.pmtiles`);
		if (offlineBasemapFile) {
			await loadOfflinePmtiles(projectId);
			selectedBaselayer = 'PMTiles';
		}
	});
</script>

<!-- Note here we still use Svelte 4 on:click until svelte-maplibre migrates -->
<MapLibre
	bind:map
	bind:loaded
	style={osmStyle}
	class="flex-auto w-full sm:aspect-video h-[calc(100%-4rem)]"
	center={[0, 0]}
	zoom={2}
	attributionControl={false}
	on:click={(_e) => {
		// deselect everything on click, to allow for re-selection
		// if the user clicks on a feature layer directly (on:click)
		taskStore.setSelectedTaskId(null, null);
		taskAreaClicked = false;
		toggleActionModal(null);
		entitiesStore.setSelectedEntity(null);
	}}
	images={[
		{ id: 'LOCKED_FOR_MAPPING', url: BlackLockImg },
		{ id: 'LOCKED_FOR_VALIDATION', url: RedLockImg },
		{ id: 'locationArc', url: LocationArcImg },
		{ id: 'locationDot', url: LocationDotImg },
		{ id: 'arrow', url: Arrow },
	]}
>
	<!-- Controls -->
	<NavigationControl position="top-left" />
	<ScaleControl />
	<Control class="flex flex-col gap-y-2" position="top-left">
		<ControlGroup>
			<ControlButton
				on:click={() => {
					toggleGeolocationStatus = !toggleGeolocationStatus;
					toggleNavigationMode = false;
				}}
				><hot-icon
					name="geolocate"
					class={`!text-[1.2rem] cursor-pointer  duration-200 ${toggleGeolocationStatus ? 'text-red-600' : 'text-[#52525B]'}`}
				></hot-icon></ControlButton
			>
		</ControlGroup></Control
	>
	<Control class="flex flex-col gap-y-2" position="top-left">
		<ControlGroup>
			<ControlButton on:click={zoomToProject}
				><hot-icon name="crop-free" class={`!text-[1.2rem] cursor-pointer duration-200 text-black`}
				></hot-icon></ControlButton
			>
		</ControlGroup></Control
	>
	<Control class="flex flex-col gap-y-2" position="top-left">
		<ControlGroup>
			<ControlButton on:click={() => (toggleNavigationMode = !toggleNavigationMode)}
				><hot-icon
					name="send"
					class={`!text-[1.2rem] cursor-pointer duration-200 ${toggleNavigationMode ? 'text-red-600' : 'text-[#52525B]'}`}
				></hot-icon></ControlButton
			>
		</ControlGroup></Control
	>
	<Control class="flex flex-col gap-y-2" position="bottom-right">
		<LayerSwitcher
			{map}
			styles={allBaseLayers}
			sourcesIdToReAdd={['tasks', 'entities', 'geolocation']}
			selectedStyleName={selectedBaselayer}
		></LayerSwitcher>
		<Legend />
	</Control>
	<!-- Add the Geolocation GeoJSON layer to the map -->
	{#if toggleGeolocationStatus}
		<Geolocation {map} {toggleGeolocationStatus} {toggleNavigationMode}></Geolocation>
	{/if}
	<!-- The task area geojson -->
	<GeoJSON id="tasks" data={taskStore.featcol} promoteId="fid">
		<FillLayer
			id="task-fill-layer"
			hoverCursor="pointer"
			paint={{
				'fill-color': [
					'match',
					['get', 'state'],
					'UNLOCKED_TO_MAP',
					'#ffffff',
					'LOCKED_FOR_MAPPING',
					'#008099',
					'UNLOCKED_TO_VALIDATE',
					'#ade6ef',
					'LOCKED_FOR_VALIDATION',
					'#fceca4',
					'UNLOCKED_DONE',
					'#40ac8c',
					'#c5fbf5', // default color if no match is found
				],
				'fill-opacity': hoverStateFilter(0.3, 0),
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
		<LineLayer
			layout={{ 'line-cap': 'round', 'line-join': 'round' }}
			paint={{
				'line-color': ['case', ['==', ['get', 'fid'], taskStore.selectedTaskId], '#fa1100', '#0fffff'],
				'line-width': 3,
				'line-opacity': ['case', ['==', ['get', 'fid'], taskStore.selectedTaskId], 1, 0.35],
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
		<SymbolLayer
			applyToClusters={false}
			hoverCursor="pointer"
			layout={{
				'icon-image': [
					'case',
					['==', ['get', 'state'], 'LOCKED_FOR_MAPPING'],
					'LOCKED_FOR_MAPPING',
					['==', ['get', 'state'], 'LOCKED_FOR_VALIDATION'],
					'LOCKED_FOR_VALIDATION',
					'',
				],
				'icon-allow-overlap': true,
			}}
		/>
	</GeoJSON>
	<!-- The features / entities -->
	<FlatGeobuf
		id="entities"
		url={entitiesUrl}
		extent={taskStore.selectedTaskGeom}
		extractGeomCols={true}
		promoteId="id"
		processGeojson={(geojsonData) => addStatusToGeojsonProperty(geojsonData)}
		geojsonUpdateDependency={entitiesStore.entitiesStatusList}
	>
		<FillLayer
			id="entity-fill-layer"
			paint={{
				'fill-opacity': 0.3,
				'fill-color': [
					'match',
					['get', 'status'],
					'READY',
					'#d62822',
					'OPENED_IN_ODK',
					'#fad30a',
					'SURVEY_SUBMITTED',
					'#32a852',
					'#c5fbf5', // default color if no match is found
				],
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
		<LineLayer
			layout={{ 'line-cap': 'round', 'line-join': 'round' }}
			paint={{
				'line-color': '#fa1100',
				'line-width': ['case', ['==', ['get', 'osm_id'], entitiesStore.selectedEntity], 1, 0],
				'line-opacity': ['case', ['==', ['get', 'osm_id'], entitiesStore.selectedEntity], 1, 0.35],
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
	</FlatGeobuf>

	<!-- Offline pmtiles, if present (alternative approach, not baselayer) -->
	<!-- {#if projectBasemapStore.projectPmtilesUrl}
	<RasterTileSource
		url={projectBasemapStore.projectPmtilesUrl}
		tileSize={512}
	>
		<RasterLayer id="pmtile-basemap" paint={{'raster-opacity': 0.8}}></RasterLayer>
	</RasterTileSource>
	{/if} -->

	<!-- Help text for user on first load -->
	{#if projectSetupStep === projectSetupStepEnum['task_selection']}
		<div class="absolute top-5 w-fit bg-[#F097334D] z-10 left-[50%] translate-x-[-50%] p-1">
			<p class="uppercase font-barlow-medium text-base">please select a task / feature for mapping</p>
		</div>
	{/if}

	<!-- Help for drawing a new geometry -->
	{#if displayDrawHelpText}
		<div class="absolute top-5 w-fit bg-[#F097334D] z-10 left-[50%] translate-x-[-50%] p-1">
			<p class="uppercase font-barlow-medium text-base">Click on the map to create a new point</p>
		</div>
	{/if}
</MapLibre>
