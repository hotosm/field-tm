<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import '$styles/map.css';
	import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
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
		CircleLayer,
	} from 'svelte-maplibre';
	import maplibre from 'maplibre-gl';
	import { MaplibreTerradrawControl } from '@watergis/maplibre-gl-terradraw';
	import { Protocol } from 'pmtiles';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type { Position, Geometry as GeoJSONGeometry, FeatureCollection } from 'geojson';
	import { centroid } from '@turf/centroid';

	import LocationArcImg from '$assets/images/locationArc.png';
	import LocationDotImg from '$assets/images/locationDot.png';
	import MapPinGrey from '$assets/images/map-pin-grey.png';
	import MapPinRed from '$assets/images/map-pin-red.png';
	import MapPinYellow from '$assets/images/map-pin-yellow.png';
	import MapPinGreen from '$assets/images/map-pin-green.png';
	import MapPinBlue from '$assets/images/map-pin-blue.png';
	import BlackLockImg from '$assets/images/black-lock.png';
	import RedLockImg from '$assets/images/red-lock.png';
	import Arrow from '$assets/images/arrow.png';

	import { m } from '$translations/messages.js';
	import Legend from '$lib/components/map/legend.svelte';
	import LayerSwitcher from '$lib/components/map/layer-switcher.svelte';
	import Geolocation from '$lib/components/map/geolocation.svelte';
	import FlatGeobuf from '$lib/components/map/flatgeobuf-layer.svelte';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getProjectSetupStepStore, getProjectBasemapStore } from '$store/common.svelte.ts';
	import { readFileFromOPFS } from '$lib/fs/opfs.ts';
	import { loadOfflinePmtiles } from '$lib/map/basemaps.ts';
	import { projectSetupStep as projectSetupStepEnum, MapGeomTypes } from '$constants/enums.ts';
	import { baseLayers, osmStyle, pmtilesStyle } from '$constants/baseLayers.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { clickOutside } from '$lib/map/click-outside.ts';

	type bboxType = [number, number, number, number];

	interface Props {
		projectOutlineCoords: Position[][];
		entitiesUrl: string;
		toggleActionModal: (value: 'task-modal' | 'entity-modal' | null) => void;
		projectId: number;
		setMapRef: (map: maplibregl.Map | undefined) => void;
		primaryGeomType: MapGeomTypes;
		draw?: boolean;
		drawGeomType: MapGeomTypes | undefined;
		handleDrawnGeom?: ((drawInstance: any, geojson: GeoJSONGeometry) => void) | null;
	}

	let {
		projectOutlineCoords,
		entitiesUrl,
		toggleActionModal,
		projectId,
		setMapRef,
		primaryGeomType,
		draw = false,
		drawGeomType,
		handleDrawnGeom,
	}: Props = $props();

	const cssValue = (property) => getComputedStyle(document.documentElement).getPropertyValue(property).trim();

	const taskStore = getTaskStore();
	const projectSetupStepStore = getProjectSetupStepStore();
	const entitiesStore = getEntitiesStatusStore();
	const projectBasemapStore = getProjectBasemapStore();

	let map: maplibregl.Map | undefined = $state();
	let loaded: boolean = $state(false);
	let selectedBaselayer: string = $state('OSM');
	let taskAreaClicked: boolean = $state(false);
	let projectSetupStep: number | null = $state(null);
	let lineWidth = $state(1); // Initial line width of the rejected entities (polygon)
	let circleRadius = $state(15); // Initial line width of the rejected entities (point)
	let expanding = true; // Whether the line is expanding
	let selectedControl: 'layer-switcher' | 'legend' | null = $state(null);
	let selectedStyleUrl: string | undefined = $state(undefined);

	let fillLayerColors = {
		UNLOCKED_TO_MAP: '#ffffff',
		LOCKED_FOR_MAPPING: '#008099',
		UNLOCKED_TO_VALIDATE: '#ade6ef',
		LOCKED_FOR_VALIDATION: '#fceca4',
		UNLOCKED_DONE: '#40ac8c',
		default: '#c5fbf5',
		primary: 'red',
	};

	let taskCentroidGeojson = $derived({
		...taskStore.featcol,
		features: taskStore.featcol?.features?.map((feat) => centroid(feat?.geometry, { properties: feat.properties })),
	});
	// use Map for quick lookups
	let entityMapByEntity = $derived(
		new Map(entitiesStore.entitiesStatusList.map((entity) => [entity.entity_id, entity])),
	);
	let entityMapByOsm = $derived(new Map(entitiesStore.entitiesStatusList.map((entity) => [entity.osmid, entity])));
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
		let entityLayerName: string;
		let newEntityLayerName: string;
		switch (drawGeomType) {
			case MapGeomTypes.POINT:
				entityLayerName = 'entity-point-layer';
				newEntityLayerName = 'new-entity-point-layer';
				break;
			case MapGeomTypes.POLYGON:
				entityLayerName = 'entity-polygon-layer';
				newEntityLayerName = 'new-entity-polygon-layer';
				break;
			case MapGeomTypes.LINESTRING:
				entityLayerName = 'entity-line-layer';
				newEntityLayerName = 'new-entity-line-layer';
				break;
			default:
				throw new Error(`Unsupported geometry type: ${drawGeomType}`);
		}
		// returns list of features of entity layer present on that clicked point
		const clickedEntityFeature = map?.queryRenderedFeatures(e.point, {
			layers: [entityLayerName],
		});
		const clickedNewEntityFeature = map?.queryRenderedFeatures(e.point, {
			layers: [newEntityLayerName],
		});
		// returns list of features of task layer present on that clicked point
		const clickedTaskFeature = map?.queryRenderedFeatures(e.point, {
			layers: ['task-fill-layer'],
		});
		// if clicked point contains entity then set it's osm id else set null to store
		if (clickedEntityFeature && clickedEntityFeature?.length > 0) {
			const entityCentroid = centroid(clickedEntityFeature[0].geometry);
			const clickedEntityId = clickedEntityFeature[0]?.properties?.entity_id;
			entitiesStore.setSelectedEntity(clickedEntityId);
			entitiesStore.setSelectedEntityCoordinate({
				entityId: clickedEntityId,
				coordinate: entityCentroid?.geometry?.coordinates,
			});
		} else if (clickedNewEntityFeature && clickedNewEntityFeature?.length > 0) {
			const entityCentroid = centroid(clickedNewEntityFeature[0].geometry);
			const clickedEntityId = clickedNewEntityFeature[0]?.properties?.entity_id;
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

		if (
			(clickedEntityFeature && clickedEntityFeature?.length > 0) ||
			(clickedNewEntityFeature && clickedNewEntityFeature?.length > 0)
		) {
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

	function addStatusToGeojsonProperty(geojsonData: FeatureCollection, entityType: '' | 'new'): FeatureCollection {
		if (entityType === 'new') {
			return {
				...geojsonData,
				features: geojsonData.features.map((feature) => {
					const entity = entityMapByEntity.get(feature?.properties?.entity_id);
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
		} else {
			return {
				...geojsonData,
				features: geojsonData.features.map((feature) => {
					const entity = entityMapByOsm.get(feature?.properties?.osm_id);
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
	}

	function zoomToProject() {
		const taskBuffer = buffer(taskStore.featcol, 5, { units: 'meters' });
		if (taskBuffer && map) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			map?.fitBounds(taskBbox, { duration: 500 });
		}
	}

	onMount(async () => {
		// Give the browser a tick to apply all styles
		requestAnimationFrame(() => {
			setTimeout(() => {
				// Load color from CSS variables
				const unlockedToMapColor = cssValue('--sl-color-neutral-300');
				const lockedForMappingColor = cssValue('--sl-color-warning-700');
				const unlockedToValidateColor = cssValue('--sl-color-primary-400');
				const lockedForValidationColor = cssValue('--sl-color-success-700');
				const unlockedDoneColor = cssValue('--sl-color-success-700');
				const primary = cssValue('--sl-color-primary-700');

				// Replace your color variables with the ones fetched from CSS
				fillLayerColors = {
					UNLOCKED_TO_MAP: unlockedToMapColor || fillLayerColors['UNLOCKED_TO_MAP'],
					LOCKED_FOR_MAPPING: lockedForMappingColor || fillLayerColors['LOCKED_FOR_MAPPING'],
					UNLOCKED_TO_VALIDATE: unlockedToValidateColor || fillLayerColors['UNLOCKED_TO_VALIDATE'],
					LOCKED_FOR_VALIDATION: lockedForValidationColor || fillLayerColors['LOCKED_FOR_VALIDATION'],
					UNLOCKED_DONE: unlockedDoneColor || fillLayerColors['UNLOCKED_DONE'],
					default: fillLayerColors['default'], // Keep default color as is
					primary: primary || fillLayerColors['primary'],
				};
			}, 100);
		});

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
			if (drawGeomType === MapGeomTypes.POLYGON) {
				if (expanding) {
					lineWidth += 0.3;
					if (lineWidth >= 4) expanding = false; // Maximum width
				} else {
					lineWidth -= 0.3;
					if (lineWidth <= 1) expanding = true; // Minimum width
				}
			} else if (drawGeomType === MapGeomTypes.POINT) {
				if (expanding) {
					circleRadius += 0.5;
					if (circleRadius >= 25) expanding = false; // Maximum radius
				} else {
					circleRadius -= 0.5;
					if (circleRadius <= 15) expanding = true; // Minimum radius
				}
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
	class="map"
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
		{ id: 'MAP_PIN_GREY', url: MapPinGrey },
		{ id: 'MAP_PIN_RED', url: MapPinRed },
		{ id: 'MAP_PIN_BLUE', url: MapPinBlue },
		{ id: 'MAP_PIN_YELLOW', url: MapPinYellow },
		{ id: 'MAP_PIN_GREEN', url: MapPinGreen },
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
	<Control class="control" position="top-left">
		<ControlGroup>
			<ControlButton title="Zoom to project" on:click={zoomToProject}
				><hot-icon name="crop-free" class="icon"></hot-icon></ControlButton
			>
		</ControlGroup></Control
	>
	<Control class="control" position="bottom-right">
		<div class="content">
			<sl-icon-button
				name="arrow-repeat"
				label="Settings"
				disabled={entitiesStore.syncEntityStatusLoading}
				class={`sync-button ${entitiesStore.syncEntityStatusLoading && 'animate-spin'}`}
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
			<img class="basemap-icon" src={selectedStyleUrl} alt="Basemap Icon" />
		</div>
		<div
			aria-label="toggle legend"
			class="toggle-legend"
			onclick={() => (selectedControl = 'legend')}
			role="button"
			onkeydown={(e) => {
				if (e.key === 'Enter') {
					selectedControl = 'legend';
				}
			}}
			tabindex="0"
		>
			<hot-icon name="legend-toggle" class="icon"></hot-icon>
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
					fillLayerColors['UNLOCKED_TO_MAP'],
					'LOCKED_FOR_MAPPING',
					fillLayerColors['LOCKED_FOR_MAPPING'],
					'UNLOCKED_TO_VALIDATE',
					fillLayerColors['UNLOCKED_TO_VALIDATE'],
					'LOCKED_FOR_VALIDATION',
					fillLayerColors['LOCKED_FOR_VALIDATION'],
					'UNLOCKED_DONE',
					fillLayerColors['UNLOCKED_DONE'],
					fillLayerColors['default'], // default color if no match,
				],
				'fill-opacity': hoverStateFilter(0.3, 0),
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
		<LineLayer
			layout={{ 'line-cap': 'round', 'line-join': 'round' }}
			paint={{
				'line-color': [
					'case',
					['==', ['get', 'fid'], taskStore.selectedTaskId],
					fillLayerColors['primary'],
					fillLayerColors['primary'],
				],
				'line-width': 3,
				'line-opacity': ['case', ['==', ['get', 'fid'], taskStore.selectedTaskId], 1, 0.35],
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
	</GeoJSON>
	<GeoJSON id="tasks-centroid" data={taskCentroidGeojson} promoteId="fid">
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
				'symbol-placement': 'point',
				'icon-allow-overlap': true,
			}}
		/>
	</GeoJSON>
	<!-- The features / entities -->
	{#if entitiesUrl}
		<FlatGeobuf
			id="entities"
			url={entitiesUrl}
			extent={taskStore.selectedTaskGeom}
			extractGeomCols={true}
			promoteId="id"
			processGeojson={(geojsonData) => addStatusToGeojsonProperty(geojsonData, '')}
			geojsonUpdateDependency={[entityMapByEntity, entityMapByOsm]}
		>
			{#if primaryGeomType === MapGeomTypes.POLYGON}
				<FillLayer
					id="entity-polygon-layer"
					paint={{
						'fill-opacity': ['match', ['get', 'status'], 'MARKED_BAD', 0, 0.6],
						'fill-color': [
							'match',
							['get', 'status'],
							'READY',
							cssValue('--sl-color-neutral-300'),
							'OPENED_IN_ODK',
							cssValue('--sl-color-warning-700'),
							'SURVEY_SUBMITTED',
							cssValue('--sl-color-success-700'),
							'VALIDATED',
							cssValue('--sl-color-success-500'),
							'MARKED_BAD',
							cssValue('--sl-color-danger-700'),
							cssValue('--sl-color-primary-700'), // default color if no match is found
						],
						'fill-outline-color': [
							'match',
							['get', 'status'],
							'READY',
							cssValue('--sl-color-neutral-1000'),
							'OPENED_IN_ODK',
							cssValue('--sl-color-warning-900'),
							'SURVEY_SUBMITTED',
							cssValue('--sl-color-success-900'),
							'MARKED_BAD',
							cssValue('--sl-color-danger-900'),
							cssValue('--sl-color-primary-700'),
						],
					}}
					beforeLayerType="symbol"
					manageHoverState
				/>
				<LineLayer
					layout={{ 'line-cap': 'round', 'line-join': 'round' }}
					paint={{
						'line-color': cssValue('--sl-color-primary-700'),
						'line-width': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity || ''], 1, 0],
						'line-opacity': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity || ''], 1, 0.35],
					}}
					beforeLayerType="symbol"
					manageHoverState
				/>
			{:else if primaryGeomType === MapGeomTypes.POINT}
				<SymbolLayer
					id="entity-point-layer"
					applyToClusters={false}
					hoverCursor="pointer"
					manageHoverState
					layout={{
						'icon-image': [
							'match',
							['get', 'status'],
							'READY',
							'MAP_PIN_GREY',
							'OPENED_IN_ODK',
							'MAP_PIN_YELLOW',
							'SURVEY_SUBMITTED',
							'MAP_PIN_GREEN',
							'VALIDATED',
							'MAP_PIN_BLUE',
							'MARKED_BAD',
							'MAP_PIN_RED',
							cssValue('--sl-color-primary-700'), // default color if no match is found
						],
						'icon-allow-overlap': true,
						'icon-size': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity || ''], 1.6, 1],
					}}
				/>
			{/if}
		</FlatGeobuf>
	{/if}
	<GeoJSON id="bad-geoms" data={entitiesStore.badGeomList}>
		{#if drawGeomType === MapGeomTypes.POLYGON}
			<FillLayer
				id="bad-geom-fill-layer"
				hoverCursor="pointer"
				paint={{
					'fill-color': cssValue('--sl-color-primary-700'),
					'fill-opacity': 0.3,
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
			<LineLayer
				layout={{ 'line-cap': 'round', 'line-join': 'round' }}
				paint={{
					'line-color': cssValue('--sl-color-primary-700'),
					'line-width': lineWidth,
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
		{:else if drawGeomType === MapGeomTypes.POINT}
			<CircleLayer
				id="bad-geom-circle-layer"
				hoverCursor="pointer"
				paint={{
					'circle-color': cssValue('--sl-color-primary-700'),
					'circle-opacity': 0.4,
					'circle-radius': circleRadius,
					'circle-stroke-opacity': hoverStateFilter(0, 1),
				}}
			/>
		{/if}
	</GeoJSON>
	<GeoJSON id="new-geoms" data={addStatusToGeojsonProperty(entitiesStore.newGeomList, 'new')}>
		{#if drawGeomType === MapGeomTypes.POLYGON}
			<FillLayer
				id="new-entity-polygon-layer"
				paint={{
					'fill-opacity': ['match', ['get', 'status'], 'MARKED_BAD', 0, 0.6],
					'fill-color': [
						'match',
						['get', 'status'],
						'READY',
						cssValue('--sl-color-neutral-300'),
						'OPENED_IN_ODK',
						cssValue('--sl-color-warning-700'),
						'SURVEY_SUBMITTED',
						cssValue('--sl-color-success-700'),
						'VALIDATED',
						cssValue('--sl-color-success-500'),
						'MARKED_BAD',
						cssValue('--sl-color-danger-700'),
						cssValue('--sl-color-primary-700'), // default color if no match is found
					],
					'fill-outline-color': [
						'match',
						['get', 'status'],
						'READY',
						cssValue('--sl-color-neutral-1000'),
						'OPENED_IN_ODK',
						cssValue('--sl-color-warning-900'),
						'SURVEY_SUBMITTED',
						cssValue('--sl-color-success-900'),
						'MARKED_BAD',
						cssValue('--sl-color-danger-900'),
						cssValue('--sl-color-primary-700'),
					],
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
			<LineLayer
				layout={{ 'line-cap': 'round', 'line-join': 'round' }}
				paint={{
					'line-color': cssValue('--sl-color-primary-700'),
					'line-width': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity || ''], 1, 0],
					'line-opacity': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity || ''], 1, 0.35],
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
		{:else if drawGeomType === MapGeomTypes.POINT}
			<!-- id="new-geom-symbol-layer" -->
			<SymbolLayer
				id="new-entity-point-layer"
				applyToClusters={false}
				hoverCursor="pointer"
				manageHoverState
				layout={{
					'icon-image': [
						'match',
						['get', 'status'],
						'READY',
						'MAP_PIN_GREY',
						'OPENED_IN_ODK',
						'MAP_PIN_YELLOW',
						'SURVEY_SUBMITTED',
						'MAP_PIN_GREEN',
						'VALIDATED',
						'MAP_PIN_BLUE',
						'MARKED_BAD',
						'MAP_PIN_RED',
						cssValue('--sl-color-primary-700'), // default color if no match is found
					],
					'icon-allow-overlap': true,
					'icon-size': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity || ''], 1.6, 1],
				}}
			/>
		{/if}
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
		<div class="help-text">
			<p>{m['map.click_on_a_task']()}</p>
		</div>
	{/if}

	<!-- Help for drawing a new geometry -->
	{#if displayDrawHelpText}
		<div class="help-text-2">
			<p>{m['map.click_on_the_map']()}</p>
		</div>
	{/if}
</MapLibre>

<div
	use:clickOutside
	onclick_outside={() => (selectedControl = null)}
	class={`map-control-container ${selectedControl ? 'selected' : 'not-selected'}`}
>
	<div class="wrapper">
		<div class="icon-container">
			<hot-icon
				name="close"
				class="icon"
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
