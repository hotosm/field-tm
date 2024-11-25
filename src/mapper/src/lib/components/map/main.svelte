<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import '@hotosm/ui/dist/hotosm-ui';
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
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type { Position, Polygon, FeatureCollection } from 'geojson';

	import LocationArcImg from '$assets/images/locationArc.png';
	import LocationDotImg from '$assets/images/locationDot.png';
	import BlackLockImg from '$assets/images/black-lock.png';
	import RedLockImg from '$assets/images/red-lock.png';

	import Legend from '$lib/components/map/legend.svelte';
	import LayerSwitcher from '$lib/components/map/layer-switcher.svelte';
	import Geolocation from '$lib/components/map/geolocation.svelte';
	import FlatGeobuf from '$lib/components/map/flatgeobuf-layer.svelte';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getProjectSetupStepStore } from '$store/common.svelte.ts';
	// import { entityFeatcolStore, selectedEntityId } from '$store/entities';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import { baseLayers, osmStyle } from '$constants/baseLayers.ts';

	type bboxType = [number, number, number, number];

	interface Props {
		projectOutlineCoords: Position[][];
		entitiesUrl: string;
		toggleTaskActionModal: (value: boolean) => void;
		projectId: number;
		setMapRef: (map: maplibregl.Map | undefined) => void;
	}

	let { projectOutlineCoords, entitiesUrl, toggleTaskActionModal, projectId, setMapRef }: Props = $props();

	const taskStore = getTaskStore();
	const projectSetupStepStore = getProjectSetupStepStore();

	let map: maplibregl.Map | undefined = $state();
	let loaded: boolean = $state(false);
	let taskAreaClicked: boolean = $state(false);
	let toggleGeolocationStatus: boolean = $state(false);
	let projectSetupStep = $state(null);

	$effect(() => {
		projectSetupStep = +projectSetupStepStore.projectSetupStep;
	});

	// set the map ref to parent component
	$effect(() => {
		if (map) {
			setMapRef(map);
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
		taskStore.setSelectedTaskId(null);
		taskAreaClicked = false;
		toggleTaskActionModal(false);
	}}
	images={[
		{ id: 'LOCKED_FOR_MAPPING', url: BlackLockImg },
		{ id: 'LOCKED_FOR_VALIDATION', url: RedLockImg },
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
	<!-- Add the Geolocation GeoJSON layer to the map -->
	{#if toggleGeolocationStatus}
		<Geolocation bind:map bind:toggleGeolocationStatus></Geolocation>
	{/if}
	<!-- The task area geojson -->
	<GeoJSON id="tasks" data={taskStore.featcol} promoteId="fid">
		<FillLayer
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
			on:click={(e) => {
				taskAreaClicked = true;
				const clickedTaskId = e.detail.features?.[0]?.properties?.fid;
				taskStore.setSelectedTaskId(clickedTaskId);
				toggleTaskActionModal(true);
				if (+projectSetupStepStore.projectSetupStep === projectSetupStepEnum['task_selection']) {
					localStorage.setItem(`project-${projectId}-setup`, projectSetupStepEnum['complete_setup']);
					projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['complete_setup']);
				}
			}}
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
	<FlatGeobuf id="entities" url={entitiesUrl} extent={taskStore.selectedTaskGeom} extractGeomCols={true} promoteId="id">
		<FillLayer
			paint={{
				'fill-color': '#006600',
				'fill-opacity': 0.5,
			}}
			beforeLayerType="symbol"
			manageHoverState
		/>
	</FlatGeobuf>
	<Control class="flex flex-col gap-y-2" position="bottom-right">
		<LayerSwitcher {map} extraStyles={baseLayers} sourcesIdToReAdd={['tasks', 'entities', 'geolocation']} />
		<Legend />
	</Control>
	{#if projectSetupStep === projectSetupStepEnum['task_selection']}
		<div class="absolute top-5 w-fit bg-[#F097334D] z-10 left-[50%] translate-x-[-50%] p-1">
			<p class="uppercase font-barlow-medium text-base">please select a task / feature for mapping</p>
		</div>
	{/if}
</MapLibre>
