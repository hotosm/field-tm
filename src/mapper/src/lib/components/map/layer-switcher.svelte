<!-- A component to render a style selection prompt, including a thumbnail
preview of the style content.

Currently a thumbnail is render only for raster style types.
We should be able to handle:
  - RasterDEMSourceSpecification
  - RasterSourceSpecification
  - VectorSourceSpecification

To achieve this and make it more flexible, it would probably be best
to render a MapLibre minimap for each style, allowing the library
to handle the parsing of URLs and rendering. The zoom could be
set to the minZoom to display a thumbnail image.

E.g.
```
map = new Map({
  container: div,
  style: uri,
  attributionControl: false,
  interactive: false
});
``` -->

<script lang="ts">
	import { onDestroy } from 'svelte';
	import { clickOutside } from '$lib/utils/clickOutside';

	type Props = {
		extraStyles: maplibregl.StyleSpecification[];
		map: maplibregl.Map | undefined;
		sourcesIdToReAdd: string[];
	};

	const { extraStyles, map, sourcesIdToReAdd }: Props = $props();

	let allStyles: MapLibreStylePlusMetadata[] | [] = $state([]);
	let selectedStyleUrl: string | undefined = $state(undefined);
	let isClosed = $state(true);
	let isOpen = $state(false);

	$effect(() => {
		if (extraStyles.length > 0) {
			fetchStyleInfo();
		} else {
			allStyles = [];
		}
	});

	type MapLibreStylePlusMetadata = maplibregl.StyleSpecification & {
		metadata: {
			thumbnail?: string;
		};
	};

	/**
	 * Extract the raster thumbnail root tile, or return an empty string.
	 */
	function getRasterThumbnailUrl(style: maplibregl.StyleSpecification): string {
		const rasterSource = Object.values(style.sources).find((source) => source.type === 'raster') as
			| maplibregl.RasterSourceSpecification
			| undefined;

		if (!rasterSource || !rasterSource.tiles?.length) {
			const placeholderSvg = `
		  data:image/svg+xml,<svg id="map_placeholder" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 105.93 122.88">
		  <defs><style>.cls-1{fill-rule:evenodd;}</style></defs><title>map</title><path class="cls-1" 
		  d="M56.92,73.14a1.62,1.62,0,0,1-1.86.06A65.25,65.25,0,0,1,38.92,58.8,51.29,51.29,0,0,1,28.06,35.37C26.77,27.38,28,19.7,32,13.45a27,27,
		  0,0,1,6-6.66A29.23,29.23,0,0,1,56.36,0,26,26,0,0,1,73.82,7.12a26,26,0,0,1,4.66,5.68c4.27,7,5.19,16,3.31,25.12A55.29,55.29,0,0,1,56.92,
		  73.14Zm-19,.74V101.7l30.15,13V78.87a65.17,65.17,0,0,0,6.45-5.63v41.18l25-12.59v-56l-9.61,3.7a61.61,61.61,0,0,0,2.38-7.81l9.3-3.59A3.22,
		  3.22,0,0,1,105.7,40a3.18,3.18,0,0,1,.22,1.16v62.7a3.23,3.23,0,0,1-2,3L72.72,122.53a3.23,3.23,0,0,1-2.92,0l-35-15.17L4.68,122.53a3.22,
		  3.22,0,0,1-4.33-1.42A3.28,3.28,0,0,1,0,119.66V53.24a3.23,3.23,0,0,1,2.32-3.1L18.7,43.82a58.63,58.63,0,0,0,2.16,6.07L6.46,
		  55.44v59l25-12.59V67.09a76.28,76.28,0,0,0,6.46,6.79ZM55.15,14.21A13.72,13.72,0,1,1,41.43,27.93,13.72,13.72,0,0,1,55.15,14.21Z"/></svg>`;
			return placeholderSvg;
		}

		const firstTileUrl = rasterSource.tiles[0];
		const minzoom = rasterSource.minzoom || 0;

		return firstTileUrl.replace('{x}', '0').replace('{y}', '0').replace('{z}', minzoom.toString());
	}

	/**
	 * Process the style to add metadata and return it.
	 */
	function processStyle(style: maplibregl.StyleSpecification): MapLibreStylePlusMetadata {
		const thumbnailUrl = getRasterThumbnailUrl(style);
		return {
			...style,
			metadata: {
				...style.metadata,
				thumbnail: thumbnailUrl,
			},
		};
	}

	/**
	 * Fetch styles and prepare them with thumbnails.
	 */
	async function fetchStyleInfo() {
		const currentMapStyle = map?.getStyle();
		if (currentMapStyle) {
			const processedStyle = processStyle(currentMapStyle);
			selectedStyleUrl = processedStyle?.metadata?.thumbnail || undefined;
			allStyles = [processedStyle];
		}

		const extraProcessedStyles = await Promise.all(
			extraStyles.map(async (style) => {
				if (typeof style === 'string') {
					const styleResponse = await fetch(style);
					const styleJson = await styleResponse.json();
					return processStyle(styleJson);
				} else {
					return processStyle(style);
				}
			}),
		);

		allStyles = allStyles.concat(extraProcessedStyles);
	}

	function selectStyle(style: MapLibreStylePlusMetadata) {
		// returns all the map style i.e. all layers, sources
		const currentMapStyle = map?.getStyle();

		// reAddLayers: user defined layers that needs to be preserved
		const reAddLayers = currentMapStyle?.layers?.filter((layer) => {
			return sourcesIdToReAdd?.includes(layer?.source);
		});

		// reAddSources: user defined sources that needs to be preserved
		const reAddSources = Object?.entries(currentMapStyle?.sources)
			?.filter(([key]) => sourcesIdToReAdd?.includes(key))
			?.map(([key, value]) => ({ [key]: value }));

		selectedStyleUrl = style.metadata.thumbnail;

		// changes to selected base layer (note: user defined layer and sources are lost)
		map?.setStyle(style);
		isClosed = !isClosed;

		// reapply user defined source
		if (reAddSources?.length > 0) {
			for (const reAddSource of reAddSources) {
				for (const [id, source] of Object.entries(reAddSource)) {
					if (!map?.getStyle().sources[id]) {
						map?.addSource(id, source);
					}
				}
			}
		}
		// reapply user defined layers
		if (reAddLayers?.length > 0) {
			for (const layer of reAddLayers) {
				if (!map?.getStyle().layers.find((layerx) => layerx?.id === layer.id)) {
					map?.addLayer(layer);
				}
			}
		}
	}

	onDestroy(() => {
		allStyles = [];
		selectedStyleUrl = undefined;
		isClosed = true;
	});
</script>

<div class="relative" use:clickOutside onclick_outside={() => (isOpen = false)}>
	<div
		onclick={() => (isOpen = !isOpen)}
		role="button"
		onkeydown={(e) => {
			if (e.key === 'Enter') {
				isOpen = !isOpen;
			}
		}}
		tabindex="0"
	>
		<img
			style="border: 1px solid #d73f3f;"
			class="w-[2.824rem] h-[2.824rem] rounded-full"
			src={selectedStyleUrl}
			alt="Basemap Icon"
		/>
	</div>
	<div
		class={`absolute bottom-0 right-14 bg-white rounded-md p-4 duration-200 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
	>
		<p class="font-barlow-semibold text-lg mb-2">Base Maps</p>
		<div class="grid grid-cols-2 w-[212px] gap-3">
			{#each allStyles as style, _}
				<div
					class={`layer-card ${selectedStyleUrl === style.metadata.thumbnail ? 'active' : ''} h-[3.75rem] relative overflow-hidden rounded-md cursor-pointer hover:border-red-600`}
					onclick={() => selectStyle(style)}
					role="button"
					onkeydown={(e) => {
						if (e.key === 'Enter') selectStyle(style);
					}}
					tabindex="0"
				>
					<img src={style.metadata.thumbnail} alt="Style Thumbnail" class="w-full h-full object-cover" />
					<span class="absolute top-0 left-0 bg-white bg-opacity-80 px-1 rounded-br">{style.name}</span>
				</div>{/each}
		</div>
	</div>
</div>

<style>
	.layer-card {
		border: 2px solid white;
	}
	.layer-card:hover {
		border-color: #d73f3f;
		transition-duration: 200ms;
	}

	.active {
		border-color: #d73f3f;
	}
</style>
