<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onDestroy } from 'svelte';
	import { GeoJSON as MapLibreGeoJSON, type ClusterOptions } from 'svelte-maplibre';
	import { getId, updatedSourceContext, addSource, removeSource } from 'svelte-maplibre';
	import type { HeaderMeta } from 'flatgeobuf';
	import type { GeoJSON, Polygon, FeatureCollection } from 'geojson';
	import { flatgeobufToGeoJson, filterGeomsCentroidsWithin } from '$lib/map/flatgeobuf';

	type bboxType = [number, number, number, number];
	interface Props {
		id?: string;
		url: string;
		extent?: bboxType | Polygon | null;
		extractGeomCols: boolean;
		metadataFunc?: (headerMetadata: HeaderMeta) => void;
		promoteId?: string;
		children?: Snippet;
		processGeojson?: (geojson: FeatureCollection) => FeatureCollection;
		geojsonUpdateDependency?: any;
		cluster?: ClusterOptions | undefined;
	}

	let {
		id = getId('flatgeobuf'),
		url,
		extent,
		extractGeomCols = false,
		promoteId = undefined,
		metadataFunc,
		children,
		processGeojson,
		geojsonUpdateDependency = '',
		cluster,
	}: Props = $props();

	const { map, self: sourceId } = updatedSourceContext();
	let sourceObj: maplibregl.GeoJSONSource | undefined = $state();
	let geojsonData: GeoJSON = $state({ type: 'FeatureCollection', features: [] });

	// Set currentSourceId as reactive property once determined from context
	let currentSourceId: string | undefined = $state();
	$effect(() => {
		currentSourceId = $sourceId;
	});

	// Deserialise flatgeobuf to GeoJSON, reactive to bbox/extent changes
	async function updateGeoJSONData() {
		const featcol: FeatureCollection | null = await flatgeobufToGeoJson(url, extent, metadataFunc, extractGeomCols);
		// If there is no data, set to an empty FeatureCollection to avoid
		// re-adding layer if the bbox extent is updated
		if (!featcol) {
			geojsonData = {
				type: 'FeatureCollection',
				features: [],
			};
		// For Polygon geoms, only display if the centroid is within specified extent
		} else if (extent && 'type' in extent && extent.type === 'Polygon') {
			const filteredGeojsonData = filterGeomsCentroidsWithin(featcol, extent);
			if (processGeojson) {
				geojsonData = processGeojson(filteredGeojsonData);
			} else {
				geojsonData = filteredGeojsonData;
			}
		// Else display Point and Polyline geoms if they intersect the extent
		} else {
			if (processGeojson) {
				geojsonData = processGeojson(featcol);
			} else {
				geojsonData = featcol;
			}
		}

		currentSourceId = id;
		removeSource($map, currentSourceId!, sourceObj);
		addSourceToMap();
	}

	$effect(() => {
		geojsonUpdateDependency;
		updateGeoJSONData();
	});

	function addSourceToMap() {
		if (!$map) return;

		const initialData: maplibregl.SourceSpecification = {
			type: 'geojson',
			data: geojsonData,
			promoteId,
		};

		// Use the currentSourceId in addSource
		addSource(
			$map,
			currentSourceId!,
			initialData,
			(sourceId) => sourceId === currentSourceId,
			() => {
				sourceObj = $map?.getSource(currentSourceId!) as maplibregl.GeoJSONSource;
			},
		);
	}

	onDestroy(() => {
		if (sourceObj && $map) {
			removeSource($map, currentSourceId!, sourceObj);
			currentSourceId = undefined;
			sourceObj = undefined;
		}
	});
</script>

<MapLibreGeoJSON id={currentSourceId} data={geojsonData} {promoteId} {cluster}>
	{@render children?.()}
</MapLibreGeoJSON>
