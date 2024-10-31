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
	import { getTaskStore } from '$store/tasks.svelte.ts';
    // import { entityFeatcolStore, selectedEntityId } from '$store/entities';

    interface Props {
        projectOutlineCoords: Position[][],
        toggleTaskActionModal: boolean;
    }

    let {
        projectOutlineCoords,
        toggleTaskActionModal = $bindable(),
     }: Props = $props();

    const taskStore = getTaskStore();

	let map: maplibregl.Map | undefined = $state();
	let loaded: boolean = $state(false);
	let taskAreaClicked = $state(false);
	let toggleGeolocationStatus = $state(false);

    // Fit the map bounds to the project area
	$effect(() => {
		if (map && projectOutlineCoords) {
            const projectPolygon = polygon(projectOutlineCoords);
            const projectBuffer = buffer(projectPolygon, 100, { units: 'meters' });
            const projectBbox: [number, number, number, number] = bbox(projectBuffer) as [number, number, number, number];
            map.fitBounds(projectBbox, { duration: 0 });
		}
	});

	const osmStyle = {
		id: 'OSM Raster',
		version: 8,
		name: 'OpenStreetMap',
		sources: {
		osm: {
			type: 'raster',
			tiles: [
			'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
			'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
			'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
			],
			minzoom: 0,
			maxzoom: 19,
			attribution:
			'© <a target="_blank" rel="noopener" href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>',
		},
		},
		layers: [
		{
			id: 'osm',
			type: 'raster',
			source: 'osm',
			layout: {
			visibility: 'visible',
			},
		},
		],
	};
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
        toggleTaskActionModal = false;
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
    <GeoJSON id="states" data={taskStore.featcol} promoteId="TASKS">
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
                'fill-opacity': hoverStateFilter(0.1, 0),
            }}
            beforeLayerType="symbol"
            manageHoverState
            on:click={(e) => {
                taskAreaClicked = true;
                const clickedTaskId = e.detail.features?.[0]?.properties?.fid;
                taskStore.setSelectedTaskId(clickedTaskId);
                toggleTaskActionModal = true;
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
                'icon-image': ['case', 
                ['==', ['get', 'state'], 'LOCKED_FOR_MAPPING'], 'LOCKED_FOR_MAPPING', 
                ['==', ['get', 'status'],'LOCKED_FOR_VALIDATION'], 'LOCKED_FOR_VALIDATION', ''],
                'icon-allow-overlap': true,
            }}
        />
    </GeoJSON>
    <!-- The features / entities geojson
    <GeoJSON id="states" data={$entityFeatcolStore} promoteId="ENTITIES">
        <FillLayer
            hoverCursor="pointer"
            paint={{
                'fill-color': [
                    'match',
                    ['get', 'status'],
                    'READY',
                    '#ffffff',
                    'OPENED_IN_ODK',
                    '#008099',
                    'SURVEY_SUBMITTED',
                    '#ade6ef',
                    'MARKED_BAD',
                    '#fceca4',
                    '#c5fbf5', // default color if no match is found
                ],
                'fill-opacity': hoverStateFilter(0.1, 0),
            }}
            beforeLayerType="symbol"
            manageHoverState
            on:click={(e) => {
                // taskAreaClicked = true;
                // const clickedEntityId = e.detail.features?.[0]?.properties?.fid;
                // entityStore.selectedEntityId = clickedEntityId;
                // toggleTaskActionModal = true;
            }}
        />
        <LineLayer
            layout={{ 'line-cap': 'round', 'line-join': 'round' }}
            paint={{
                'line-color': ['case', ['==', ['get', 'fid'], $selectedEntityId], '#fa1100', '#0fffff'],
                'line-width': 3,
                'line-opacity': ['case', ['==', ['get', 'fid'], $selectedEntityId], 1, 0.35],
            }}
            beforeLayerType="symbol"
            manageHoverState
        />
    </GeoJSON> -->
    <div class="absolute right-3 bottom-3 sm:right-5 sm:bottom-5">
        <LayerSwitcher />
        <Legend />
    </div>
</MapLibre>
