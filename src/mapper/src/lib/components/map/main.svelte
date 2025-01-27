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
	import { MaplibreTerradrawControl } from '@watergis/maplibre-gl-terradraw';
	import { Protocol } from 'pmtiles';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type { Position, Geometry as GeoJSONGeometry, FeatureCollection, Feature } from 'geojson';
	import { centroid } from '@turf/centroid';

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
	import { readFileFromOPFS } from '$lib/fs/opfs.ts';
	import { loadOfflinePmtiles } from '$lib/utils/basemaps.ts';
	import { projectSetupStep as projectSetupStepEnum, NewGeomTypes } from '$constants/enums.ts';
	import { baseLayers, osmStyle, pmtilesStyle } from '$constants/baseLayers.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { clickOutside } from '$lib/utils/clickOutside.ts';

	type bboxType = [number, number, number, number];

	interface Props {
		projectOutlineCoords: Position[][];
		entitiesUrl: string;
		toggleActionModal: (value: 'task-modal' | 'entity-modal' | null) => void;
		projectId: number;
		setMapRef: (map: maplibregl.Map | undefined) => void;
		draw?: boolean;
		drawGeomType: NewGeomTypes | undefined;
		handleDrawnGeom?: ((drawInstance: any, geojson: GeoJSONGeometry) => void) | null;
	}

	let {
		projectOutlineCoords,
		entitiesUrl,
		toggleActionModal,
		projectId,
		setMapRef,
		draw = false,
		drawGeomType,
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
	let projectSetupStep: number | null = $state(null);
	let lineWidth = $state(1); // Initial line width of the rejected entities
	let expanding = true; // Whether the line is expanding
	let selectedControl: 'layer-switcher' | 'legend' | null = $state(null);
	let selectedStyleUrl: string | undefined = $state(undefined);

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
	type DrawModeOptions = 'point' | 'linestring' | 'delete-selection' | 'polygon';
	const currentDrawMode: DrawModeOptions = drawGeomType ? (drawGeomType.toLowerCase() as DrawModeOptions) : 'point';
	const drawControl = new MaplibreTerradrawControl({
		modes: [currentDrawMode, 'select', 'delete'],
		// Note We do not open the toolbar options, allowing the user
		// to simply click with a pre-defined mode active
		// open: true,
	});

	$effect(() => {
		projectSetupStep = +(projectSetupStepStore.projectSetupStep || 0);
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
			const entityCentroid = centroid(clickedEntityFeature[0].geometry);
			const clickedEntityId = clickedEntityFeature[0]?.properties?.osm_id;
			entitiesStore.setSelectedEntity(clickedEntityId);
			entitiesStore.setSelectedEntityCoordinate({
				entityId: clickedEntityId,
				coordinate: entityCentroid?.geometry?.coordinates,
			});
		} else {
			entitiesStore.setSelectedEntity(null);
			entitiesStore.setSelectedEntityCoordinate(null);
		}

		// if clicked point contains task layer
		if (clickedTaskFeature && clickedTaskFeature?.length > 0) {
			taskAreaClicked = true;
			const clickedTaskId = clickedTaskFeature[0]?.properties?.fid;
			taskStore.setSelectedTaskId(clickedTaskId, clickedTaskFeature[0]?.properties?.task_index);
			if (+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['task_selection']) {
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
				drawInstance.setMode(currentDrawMode);

				drawInstance.on('finish', (id: string, _context: any) => {
					// Save the drawn geometry location, then delete all geoms from store
					const features: { id: string; geometry: GeoJSONGeometry }[] = drawInstance.getSnapshot();
					const drawnFeature = features.find((geom) => geom.id === id);
					let firstGeom: GeoJSONGeometry | null = null;
					if (drawnFeature && drawnFeature.geometry) {
						firstGeom = drawnFeature.geometry;
					} else {
						console.error(`Feature with id ${id} not found or has no geometry.`);
					}

					if (firstGeom) {
						handleDrawnGeom(drawInstance, firstGeom);
						displayDrawHelpText = false;
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

	function addStatusToGeojsonProperty(geojsonData: FeatureCollection): FeatureCollection {
		return {
			...geojsonData,
			features: geojsonData.features.map((feature) => {
				const entity = entitiesStore.entitiesStatusList.find((entity) => entity.osmid === feature?.properties?.osm_id);
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

		const interval = setInterval(() => {
			if (expanding) {
				lineWidth += 0.3;
				if (lineWidth >= 4) expanding = false; // Maximum width
			} else {
				lineWidth -= 0.3;
				if (lineWidth <= 1) expanding = true; // Minimum width
			}
		}, 50); // Update every 50ms for smooth animation

		return () => {
			clearInterval(interval);
		};
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
	<NavigationControl position="top-left" showZoom={false} />
	<ScaleControl />
	<Control class="flex flex-col gap-y-2" position="top-left">
		<ControlGroup>
			<ControlButton title="Zoom to project" on:click={zoomToProject}
				><hot-icon name="crop-free" class={`!text-[1.2rem] cursor-pointer duration-200 text-black`}
				></hot-icon></ControlButton
			>
		</ControlGroup></Control
	>
	<Control class="flex flex-col gap-y-2" position="bottom-right">
		<div
			class="rounded-full w-[2.25rem] h-[2.25rem] overflow-hidden flex items-center justify-center border-1 border-solid border-red-600 bg-[#FFEDED]"
		>
			<sl-icon-button
				name="arrow-repeat"
				label="Settings"
				disabled={entitiesStore.syncEntityStatusLoading}
				class={`text-[1.25rem] rotate-90 text-red-600 ${entitiesStore.syncEntityStatusLoading && 'animate-spin'}`}
				onclick={async () => await entitiesStore.syncEntityStatus(projectId)}
				onkeydown={async (e: KeyboardEvent) => {
					e.key === 'Enter' && (await entitiesStore.syncEntityStatus(projectId));
				}}
				role="button"
				tabindex="0"
			></sl-icon-button>
		</div>
		<div
			aria-label="layer switcher"
			onclick={() => {
				selectedControl = 'layer-switcher';
			}}
			role="button"
			onkeydown={(e) => {
				if (e.key === 'Enter') {
					selectedControl = 'layer-switcher';
				}
			}}
			tabindex="0"
		>
			<img
				style="border: 1px solid #d73f3f;"
				class="w-[2.25rem] h-[2.25rem] rounded-full"
				src={selectedStyleUrl}
				alt="Basemap Icon"
			/>
		</div>
		<div
			aria-label="toggle legend"
			class="group text-nowrap cursor-pointer"
			onclick={() => (selectedControl = 'legend')}
			role="button"
			onkeydown={(e) => {
				if (e.key === 'Enter') {
					selectedControl = 'legend';
				}
			}}
			tabindex="0"
		>
			<hot-icon
				style="border: 1px solid #D7D7D7;"
				name="legend-toggle"
				class="!text-[1.7rem] text-[#333333] bg-white p-1 rounded-full group-hover:text-red-600 duration-200"
			></hot-icon>
		</div>
	</Control>
	<!-- Add the Geolocation GeoJSON layer to the map -->
	<Geolocation {map}></Geolocation>
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
				'fill-opacity': ['match', ['get', 'status'], 'MARKED_BAD', 0, 0.6],
				'fill-color': [
					'match',
					['get', 'status'],
					'READY',
					'#9c9a9a',
					'OPENED_IN_ODK',
					'#fae15f',
					'SURVEY_SUBMITTED',
					'#71bf86',
					'MARKED_BAD',
					'#fa1100',
					'#c5fbf5', // default color if no match is found
				],
				'fill-outline-color': [
					'match',
					['get', 'status'],
					'READY',
					'#000000',
					'OPENED_IN_ODK',
					'#ffd603',
					'SURVEY_SUBMITTED',
					'#32a852',
					'MARKED_BAD',
					'#fa1100',
					'#c5fbf5',
				],
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
		<LineLayer
			layout={{ 'line-cap': 'round', 'line-join': 'round' }}
			paint={{
				'line-color': '#fa1100',
				'line-width': ['case', ['==', ['get', 'osm_id'], entitiesStore.selectedEntity || ''], 1, 0],
				'line-opacity': ['case', ['==', ['get', 'osm_id'], entitiesStore.selectedEntity || ''], 1, 0.35],
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
	</FlatGeobuf>
	<GeoJSON id="bad-geoms" data={entitiesStore.badGeomList}>
		<FillLayer
			id="bad-geom-fill-layer"
			hoverCursor="pointer"
			paint={{
				'fill-color': '#fa1100',
				'fill-opacity': 0.3,
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
		<LineLayer
			layout={{ 'line-cap': 'round', 'line-join': 'round' }}
			paint={{
				'line-color': '#fa1100',
				'line-width': lineWidth,
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
	</GeoJSON>

	<!-- pulse effect layer representing rejected entities -->

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
		<div class="absolute top-7 bg-[#F097334D] min-w-[14rem] z-10 left-[50%] translate-x-[-50%] p-1">
			<p class="uppercase font-barlow font-medium text-base">click on a task to select a feature for mapping</p>
		</div>
	{/if}

	<!-- Help for drawing a new geometry -->
	{#if displayDrawHelpText}
		<div class="absolute top-7 w-fit bg-[#F097334D] z-10 left-[50%] translate-x-[-50%] p-1">
			<p class="uppercase font-barlow font-medium text-base">Click on the map to create a new point</p>
		</div>
	{/if}
</MapLibre>

<div
	use:clickOutside
	onclick_outside={() => (selectedControl = null)}
	class={`font-barlow flex justify-center !w-[100vw] absolute left-0 z-20 duration-400 ${selectedControl ? 'bottom-[4rem]' : '-bottom-[100%] pointer-events-none'}`}
>
	<div class="bg-white w-full font-regular md:max-w-[580px] px-4 py-3 sm:py-4 rounded-t-3xl">
		<div class="flex justify-end">
			<hot-icon
				name="close"
				class="!text-[1.5rem] text-[#52525B] cursor-pointer hover:text-red-600 duration-200"
				onclick={() => (selectedControl = null)}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						selectedControl = null;
					}
				}}
				role="button"
				tabindex="0"
			></hot-icon>
		</div>
		<LayerSwitcher
			{map}
			styles={allBaseLayers}
			sourcesIdToReAdd={['tasks', 'entities', 'geolocation']}
			selectedStyleName={selectedBaselayer}
			{selectedStyleUrl}
			setSelectedStyleUrl={(style) => (selectedStyleUrl = style)}
			isOpen={selectedControl === 'layer-switcher'}
		></LayerSwitcher>
		<Legend isOpen={selectedControl === 'legend'} />
	</div>
</div>
