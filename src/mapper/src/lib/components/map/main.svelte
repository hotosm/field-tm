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
	import type { PGlite } from '@electric-sql/pglite';
	import maplibre, { type MapGeoJSONFeature, type PointLike } from 'maplibre-gl';
	import { MaplibreTerradrawControl } from '@watergis/maplibre-gl-terradraw';
	import { Protocol } from 'pmtiles';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type { Position, Geometry as GeoJSONGeometry, FeatureCollection } from 'geojson';
	import { centroid } from '@turf/centroid';

	import LocationArcImg from '$assets/images/locationArc.png';
	import LocationDotImg from '$assets/images/locationDot.png';
	import BlackLockImg from '$assets/images/black-lock.png';
	import RedLockImg from '$assets/images/red-lock.png';
	import Arrow from '$assets/images/arrow.png';

	import { m } from '$translations/messages.js';
	import Legend from '$lib/components/map/legend.svelte';
	import LayerSwitcher from '$lib/components/map/layer-switcher.svelte';
	import Geolocation from '$lib/components/map/geolocation.svelte';
	import FlatGeobuf from '$lib/components/map/flatgeobuf-layer.svelte';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getCommonStore } from '$store/common.svelte.ts';
	import { getProjectSetupStepStore, getProjectBasemapStore } from '$store/common.svelte.ts';
	import { readFileFromOPFS } from '$lib/fs/opfs.ts';
	import { loadOfflinePmtiles } from '$lib/map/basemaps.ts';
	import { projectSetupStep as projectSetupStepEnum, MapGeomTypes } from '$constants/enums.ts';
	import { baseLayers, osmStyle, pmtilesStyle } from '$constants/baseLayers.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { clickOutside } from '$lib/map/click-outside.ts';
	import { geojsonGeomToJavarosa } from '$lib/odk/javarosa';

	type bboxType = [number, number, number, number];

	interface Props {
		projectOutlineCoords: Position[][];
		entitiesUrl: string;
		toggleActionModal: (value: 'task-modal' | 'entity-modal' | null) => void;
		projectId: number;
		setMapRef: (map: maplibregl.Map | undefined) => void;
		primaryGeomType: MapGeomTypes;
		draw?: boolean;
		drawGeomType: MapGeomTypes;
		syncButtonTrigger: () => void;
		handleDrawnGeom?: (drawInstance: any, geojson: GeoJSONGeometry) => void;
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
		syncButtonTrigger,
		handleDrawnGeom,
	}: Props = $props();

	const primaryGeomLayerMapping = {
		POINT: 'entity-point-layer',
		POLYGON: 'entity-polygon-layer',
		POLYLINE: 'entity-line-layer',
	};

	const newGeomLayerMapping = {
		POINT: 'new-entity-point-layer',
		POLYGON: 'new-entity-polygon-layer',
		POLYLINE: 'new-entity-line-layer',
	};

	const cssValue = (property: string) => getComputedStyle(document.documentElement).getPropertyValue(property).trim();

	const commonStore = getCommonStore();
	const taskStore = getTaskStore();
	const projectSetupStepStore = getProjectSetupStepStore();
	const entitiesStore = getEntitiesStatusStore();
	const projectBasemapStore = getProjectBasemapStore();

	let db: PGlite | undefined = $derived(commonStore.db);
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
	let selectedFeatures: MapGeoJSONFeature[] = $state([]);

	let taskCentroidGeojson = $derived({
		...taskStore.featcol,
		features: taskStore.featcol?.features?.map((feat) => centroid(feat?.geometry, { properties: feat.properties })),
	});
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
	const currentDrawMode: DrawModeOptions =
		drawGeomType === 'POLYLINE'
			? 'linestring'
			: drawGeomType
				? (drawGeomType.toLowerCase() as DrawModeOptions)
				: 'point';
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
		let entityLayerName: string = primaryGeomLayerMapping[primaryGeomType];
		let newEntityLayerName: string = newGeomLayerMapping[drawGeomType];

		// reset selected entity geom
		entitiesStore.setSelectedEntityJavaRosaGeom(null);

		// Add a 5px spatial buffer around the clicked point to ease feature selection
		let entityPoint: PointLike | [PointLike, PointLike];
		let newEntityPoint: PointLike | [PointLike, PointLike];
		if (primaryGeomType === MapGeomTypes.POLYLINE) {
			entityPoint = [
				[e.point.x - 5, e.point.y - 5],
				[e.point.x + 5, e.point.y + 5],
			];
		} else {
			entityPoint = e.point;
		}
		if (drawGeomType === MapGeomTypes.POLYLINE) {
			newEntityPoint = [
				[e.point.x - 5, e.point.y - 5],
				[e.point.x + 5, e.point.y + 5],
			];
		} else {
			newEntityPoint = e.point;
		}

		// returns list of features of entity layer present on that clicked point
		const clickedEntityFeature =
			map?.queryRenderedFeatures(entityPoint, {
				layers: [entityLayerName],
			}) || [];
		const clickedNewEntityFeature =
			map?.queryRenderedFeatures(newEntityPoint, {
				layers: [newEntityLayerName],
			}) || [];

		const clickedFeatures = [...clickedEntityFeature, ...clickedNewEntityFeature];
		// if clicked coordinate contain more than multiple entities, assign it to a variable
		if (clickedFeatures.length > 1) {
			selectedFeatures = clickedFeatures;
		}

		// returns list of features of task layer present on that clicked point
		const clickedTaskFeature = map?.queryRenderedFeatures(e.point, {
			layers: ['task-fill-layer'],
		});

		if (clickedEntityFeature && clickedEntityFeature?.length > 0 && clickedFeatures?.length < 2) {
			// if clicked coordinate contains uploaded entity only
			const entityGeometry = clickedEntityFeature[0].geometry;
			entitiesStore.setSelectedEntityJavaRosaGeom(geojsonGeomToJavarosa(entityGeometry));
			const entityCentroid = centroid(entityGeometry);
			const clickedEntityId = clickedEntityFeature[0]?.properties?.entity_id;
			entitiesStore.setSelectedEntityId(clickedEntityId);
			entitiesStore.setSelectedEntityCoordinate({
				entityId: clickedEntityId,
				coordinate: entityCentroid?.geometry?.coordinates,
			});
		} else if (clickedNewEntityFeature && clickedNewEntityFeature?.length > 0 && clickedFeatures?.length < 2) {
			// if clicked coordinate contains new entity only
			const entityCentroid = centroid(clickedNewEntityFeature[0].geometry);
			const clickedEntityId = clickedNewEntityFeature[0]?.properties?.entity_id;
			entitiesStore.setSelectedEntityId(clickedEntityId);
			entitiesStore.setSelectedEntityCoordinate({
				entityId: clickedEntityId,
				coordinate: entityCentroid?.geometry?.coordinates,
			});
		} else {
			// if clicked coordinate doesn't contain any entity, clear the entity states
			entitiesStore.setSelectedEntityId(null);
			entitiesStore.setSelectedEntityCoordinate(null);
		}

		// if clicked point contains task layer
		if (clickedTaskFeature && clickedTaskFeature?.length > 0) {
			taskAreaClicked = true;
			const clickedTaskId = clickedTaskFeature[0]?.properties?.fid;
			taskStore.setSelectedTaskId(db, clickedTaskId, clickedTaskFeature[0]?.properties?.task_index);
			if (+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['task_selection']) {
				localStorage.setItem(`project-${projectId}-setup`, projectSetupStepEnum['complete_setup']);
				projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['complete_setup']);
			}
		}

		if (
			((clickedEntityFeature && clickedEntityFeature?.length > 0) ||
				(clickedNewEntityFeature && clickedNewEntityFeature?.length > 0)) &&
			clickedFeatures?.length < 2
		) {
			// if clicked coordinate contains either one uploaded entity or new entity, open entity actions modal
			selectedFeatures = [];
			toggleActionModal('entity-modal');
		} else if (clickedTaskFeature && clickedTaskFeature?.length > 0 && clickedFeatures?.length === 0) {
			// if clicked coordinate doesn't contain any entity but only task, open task actions modal
			selectedFeatures = [];
			toggleActionModal('task-modal');
		} else if (clickedFeatures?.length > 1) {
			// if multiple entities present
			toggleActionModal(null);
		} else {
			// clear task states i.e. unselect task and it's extract if clicked coordinate doesn't contain any entity or task
			taskStore.setSelectedTaskId(db, null, null);
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
			if (drawGeomType === MapGeomTypes.POLYGON || drawGeomType === MapGeomTypes.POLYLINE) {
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
		taskAreaClicked = false;
		toggleActionModal(null);
		entitiesStore.setSelectedEntityId(null);
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
	<Control class="control" position="top-left">
		<ControlGroup>
			<ControlButton title="Zoom to project" on:click={zoomToProject}
				><hot-icon name="crop-free" class="icon"></hot-icon></ControlButton
			>
		</ControlGroup></Control
	>
	<Control class="control" position="bottom-right">
		{#if commonStore.offlineSyncPercentComplete}
			<div class="offline-sync-percent">{commonStore.offlineSyncPercentComplete}%</div>
		{/if}
		<div class="content">
			<sl-icon-button
				name="arrow-repeat"
				label="Sync"
				disabled={entitiesStore.syncEntityStatusManuallyLoading || commonStore.offlineDataIsSyncing}
				class={`sync-button ${
					(entitiesStore.syncEntityStatusManuallyLoading || commonStore.offlineDataIsSyncing) && 'animate-spin'
				}`}
				onclick={async () => syncButtonTrigger()}
				onkeydown={async (e: KeyboardEvent) => {
					e.key === 'Enter' && syncButtonTrigger();
				}}
				role="button"
				tabindex="0"
			></sl-icon-button>
		</div>
		<div
			class="layer-switcher"
			aria-label="layer switcher"
			onclick={() => {
				selectedControl = 'layer-switcher';
				toggleActionModal(null);
			}}
			role="button"
			onkeydown={(e) => {
				if (e.key === 'Enter') {
					selectedControl = 'layer-switcher';
					toggleActionModal(null);
				}
			}}
			tabindex="0"
		>
			<img class="basemap-icon" src={selectedStyleUrl} alt="Basemap Icon" />
		</div>
		<div
			aria-label="toggle legend"
			class="toggle-legend"
			onclick={() => {
				selectedControl = 'legend';
				toggleActionModal(null);
			}}
			role="button"
			onkeydown={(e) => {
				if (e.key === 'Enter') {
					selectedControl = 'legend';
					toggleActionModal(null);
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
					cssValue('--task-unlocked-to-map'),
					'LOCKED_FOR_MAPPING',
					cssValue('--task-locked-for-mapping'),
					'UNLOCKED_TO_VALIDATE',
					cssValue('--task-unlocked-to-validate'),
					'LOCKED_FOR_VALIDATION',
					cssValue('--task-locked-for-validation'),
					'UNLOCKED_DONE',
					cssValue('--task-unlocked-done'),
					cssValue('--task-unlocked-to-map'), // default color if no match,
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
					cssValue('--task-outline-selected'),
					cssValue('--task-outline'),
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
			url={entitiesStore.fgbOpfsUrl || entitiesUrl}
			extent={primaryGeomType === MapGeomTypes.POLYLINE
				? polygon(projectOutlineCoords).geometry
				: taskStore.selectedTaskGeom}
			extractGeomCols={true}
			promoteId="id"
			processGeojson={(geojsonData) => entitiesStore.addStatusToGeojsonProperty(geojsonData)}
			geojsonUpdateDependency={[entitiesStore.entitiesList]}
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
							cssValue('--entity-ready'),
							'OPENED_IN_ODK',
							cssValue('--entity-opened-in-odk'),
							'SURVEY_SUBMITTED',
							cssValue('--entity-survey-submitted'),
							'VALIDATED',
							cssValue('--entity-validated'),
							'MARKED_BAD',
							cssValue('--entity-marked-bad'),
							cssValue('--entity-ready'), // default color if no match is found
						],
					}}
					beforeLayerType="symbol"
					manageHoverState
				/>
				<LineLayer
					layout={{ 'line-cap': 'round', 'line-join': 'round' }}
					paint={{
						'line-color': [
							'case',
							['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''],
							cssValue('--entity-outline-selected'),
							cssValue('--entity-outline'),
						],
						'line-width': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 1, 0.7],
						'line-opacity': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 1, 1],
					}}
					beforeLayerType="symbol"
					manageHoverState
				/>
			{:else if primaryGeomType === MapGeomTypes.POINT}
				<CircleLayer
					id="entity-point-layer"
					applyToClusters={false}
					hoverCursor="pointer"
					paint={{
						'circle-color': [
							'match',
							['get', 'status'],
							'READY',
							cssValue('--entity-ready'),
							'OPENED_IN_ODK',
							cssValue('--entity-opened-in-odk'),
							'SURVEY_SUBMITTED',
							cssValue('--entity-survey-submitted'),
							'VALIDATED',
							cssValue('--entity-validated'),
							'MARKED_BAD',
							cssValue('--entity-marked-bad'),
							cssValue('--entity-ready'),
						],
						'circle-radius': 8,
						'circle-stroke-width': 1,
						'circle-stroke-color': [
							'case',
							['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''],
							cssValue('--entity-outline-selected'),
							cssValue('--entity-outline'),
						],
					}}
				></CircleLayer>
			{:else if primaryGeomType === MapGeomTypes.POLYLINE}
				<LineLayer
					id="entity-line-layer"
					layout={{ 'line-cap': 'round', 'line-join': 'round' }}
					paint={{
						'line-color': [
							'match',
							['get', 'status'],
							'READY',
							cssValue('--entity-ready'),
							'OPENED_IN_ODK',
							cssValue('--entity-opened-in-odk'),
							'SURVEY_SUBMITTED',
							cssValue('--entity-survey-submitted'),
							'VALIDATED',
							cssValue('--entity-validated'),
							'MARKED_BAD',
							cssValue('--entity-marked-bad'),
							cssValue('--entity-ready'), // default color if no match is found
						],
						'line-width': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 4, 3],
						'line-opacity': [
							'case',
							['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''],
							1,
							0.8,
						],
					}}
					beforeLayerType="symbol"
					manageHoverState
				/>
			{/if}
		</FlatGeobuf>
	{/if}
	<GeoJSON id="bad-geoms" data={entitiesStore.badGeomFeatcol}>
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
				id="bad-geom-circle-point-layer"
				hoverCursor="pointer"
				paint={{
					'circle-color': cssValue('--entity-marked-bad'),
					'circle-radius': 8,
					'circle-stroke-width': 1,
					'circle-stroke-color': cssValue('--entity-outline'),
				}}
			/>
			<CircleLayer
				id="bad-geom-circle-highlight-layer"
				hoverCursor="pointer"
				paint={{
					'circle-color': cssValue('--sl-color-primary-700'),
					'circle-opacity': 0.4,
					'circle-radius': circleRadius,
					'circle-stroke-opacity': hoverStateFilter(0, 1),
				}}
			/>
		{:else if drawGeomType === MapGeomTypes.POLYLINE}
			<LineLayer
				layout={{ 'line-cap': 'round', 'line-join': 'round' }}
				paint={{
					'line-color': cssValue('--sl-color-primary-700'),
					'line-width': lineWidth,
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
		{/if}
	</GeoJSON>
	<GeoJSON id="new-geoms" data={entitiesStore.addStatusToGeojsonProperty(entitiesStore.newGeomFeatcol)}>
		{#if drawGeomType === MapGeomTypes.POLYGON}
			<FillLayer
				id="new-entity-polygon-layer"
				hoverCursor="pointer"
				paint={{
					'fill-opacity': ['match', ['get', 'status'], 'MARKED_BAD', 0, 0.6],
					'fill-color': [
						'match',
						['get', 'status'],
						'READY',
						cssValue('--entity-ready'),
						'OPENED_IN_ODK',
						cssValue('--entity-opened-in-odk'),
						'SURVEY_SUBMITTED',
						cssValue('--entity-survey-submitted'),
						'VALIDATED',
						cssValue('--entity-validated'),
						'MARKED_BAD',
						cssValue('--entity-marked-bad'),
						cssValue('--entity-ready'), // default color if no match is found
					],
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
			<LineLayer
				layout={{ 'line-cap': 'round', 'line-join': 'round' }}
				paint={{
					'line-color': [
						'case',
						['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''],
						cssValue('--entity-outline-selected'),
						cssValue('--entity-outline'),
					],
					'line-width': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 1, 0.7],
					'line-opacity': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 1, 1],
				}}
				beforeLayerType="symbol"
				manageHoverState
			/>
		{:else if drawGeomType === MapGeomTypes.POINT}
			<CircleLayer
				id="new-entity-point-layer"
				applyToClusters={false}
				hoverCursor="pointer"
				paint={{
					'circle-color': [
						'match',
						['get', 'status'],
						'READY',
						cssValue('--entity-ready'),
						'OPENED_IN_ODK',
						cssValue('--entity-opened-in-odk'),
						'SURVEY_SUBMITTED',
						cssValue('--entity-survey-submitted'),
						'VALIDATED',
						cssValue('--entity-validated'),
						'MARKED_BAD',
						cssValue('--entity-marked-bad'),
						cssValue('--entity-ready'),
					],
					'circle-radius': 8,
					'circle-stroke-width': 1,
					'circle-stroke-color': [
						'case',
						['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''],
						cssValue('--entity-outline-selected'),
						cssValue('--entity-outline'),
					],
				}}
			></CircleLayer>
		{:else if drawGeomType === MapGeomTypes.POLYLINE}
			<LineLayer
				id="new-entity-line-layer"
				layout={{ 'line-cap': 'round', 'line-join': 'round' }}
				paint={{
					'line-color': [
						'match',
						['get', 'status'],
						'READY',
						cssValue('--entity-ready'),
						'OPENED_IN_ODK',
						cssValue('--entity-opened-in-odk'),
						'SURVEY_SUBMITTED',
						cssValue('--entity-survey-submitted'),
						'VALIDATED',
						cssValue('--entity-validated'),
						'MARKED_BAD',
						cssValue('--entity-marked-bad'),
						cssValue('--entity-ready'), // default color if no match is found
					],
					'line-width': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 4, 3],
					'line-opacity': ['case', ['==', ['get', 'entity_id'], entitiesStore.selectedEntity?.entity_id || ''], 1, 0.8],
				}}
				beforeLayerType="symbol"
				manageHoverState
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
			sourcesIdToReAdd={['tasks', 'entities', 'geolocation', 'tasks-centroid', 'bad-geoms', 'new-geoms']}
			selectedStyleName={selectedBaselayer}
			{selectedStyleUrl}
			setSelectedStyleUrl={(style) => (selectedStyleUrl = style)}
			isOpen={selectedControl === 'layer-switcher'}
		></LayerSwitcher>
		<Legend isOpen={selectedControl === 'legend'} />
	</div>
</div>

{#if selectedFeatures?.length > 1}
	<div class="select-entities-modal">
		<div class="content">
			<div class="icon">
				<hot-icon
					name="close"
					onclick={() => (selectedFeatures = [])}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							selectedFeatures = [];
						}
					}}
					role="button"
					tabindex="0"
				></hot-icon>
			</div>

			<div>
				{#each selectedFeatures as feature, index}
					<div class="entity">
						<div class="header">
							<h5>{index + 1}. {feature.properties.entity_id}</h5>
							<p class={`status ${feature.properties.status}`}>{m[`entity_states.${feature.properties.status}`]()}</p>
						</div>
						<div class="button-wrapper">
							<sl-button
								variant="primary"
								size="small"
								onclick={() => {
									const entityCentroid = centroid(feature.geometry);
									const clickedEntityId = feature?.properties?.entity_id;
									entitiesStore.setSelectedEntityId(clickedEntityId);
									entitiesStore.setSelectedEntityCoordinate({
										entityId: clickedEntityId,
										coordinate: entityCentroid?.geometry?.coordinates,
									});
									selectedFeatures = [];
									toggleActionModal('entity-modal');
								}}
								onkeydown={() => {}}
								role="button"
								tabindex="0"
							>
								{m['popup.select_this_feature']()}
							</sl-button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
