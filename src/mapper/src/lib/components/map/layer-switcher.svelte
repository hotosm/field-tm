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
	import '$styles/map-layer-switcher.css';
	import { onDestroy } from 'svelte';

	type MapLibreStylePlusMetadata = maplibregl.StyleSpecification & {
		metadata: {
			thumbnail?: string;
		};
	};

	type Props = {
		styles: maplibregl.StyleSpecification[];
		selectedStyleName?: string | undefined;
		map: maplibregl.Map | undefined;
		selectedStyleUrl: string | undefined;
		setSelectedStyleUrl: (url: string | undefined) => void;
		isOpen: boolean;
	};

	const { styles, selectedStyleName, map, selectedStyleUrl, setSelectedStyleUrl, isOpen }: Props = $props();

	let allStyles: MapLibreStylePlusMetadata[] | [] = $state([]);
	// This variable is used for updating the prop selectedStyleName dynamically
	let reactiveStyleSelection: MapLibreStylePlusMetadata | undefined = $state(undefined);

	// Get style info when styles are updated
	$effect(() => {
		if (styles.length > 0) {
			// We do not await this to avoid complicating reactive logic
			fetchStyleInfo();
		} else {
			allStyles = [];
		}
	});

	$effect(() => {
		// Set initial selected style
		reactiveStyleSelection = allStyles.find((style) => style.name === selectedStyleName) || allStyles[0];
		setSelectedStyleUrl(reactiveStyleSelection?.metadata?.thumbnail);
	});

	// Update the map when a new style is selected
	$effect(() => {
		if (reactiveStyleSelection) {
			selectStyle(reactiveStyleSelection);
		}
	});

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
		const thumbnailUrl = style?.metadata?.thumbnail || getRasterThumbnailUrl(style);
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
		let processedStyles: MapLibreStylePlusMetadata[] = [];

		// Process the current map style
		const currentMapStyle = map?.getStyle();
		if (currentMapStyle) {
			processedStyles.push(processStyle(currentMapStyle));
		}

		// Process additional styles (download first if style is URL)
		for (const style of styles) {
			if (typeof style === 'string') {
				const response = await fetch(style);
				const styleJson = await response.json();
				processedStyles.push(processStyle(styleJson));
			} else {
				processedStyles.push(processStyle(style));
			}
		}

		// Deduplicate styles by `name`
		allStyles = processedStyles.filter((style, index, self) => self.findIndex((s) => s.name === style.name) === index);
	}

	function selectStyle(style: MapLibreStylePlusMetadata) {
		const currentMapStyle = map?.getStyle();

		if (!currentMapStyle || style.name === currentMapStyle.name) return;

		setSelectedStyleUrl(style.metadata.thumbnail);

		map?.setStyle(style);
	}
	onDestroy(() => {
		allStyles = [];
		setSelectedStyleUrl(undefined);
	});
</script>

<div class={`layer-switcher ${isOpen ? 'open' : 'closed'}`}>
	<p class="title">Base Maps</p>
	<div class="content">
		{#each allStyles as style, _}
			<div
				class={`layer-card ${selectedStyleUrl === style.metadata.thumbnail ? 'active' : ''}`}
				onclick={() => selectStyle(style)}
				role="button"
				onkeydown={(e) => {
					if (e.key === 'Enter') selectStyle(style);
				}}
				tabindex="0"
			>
				<img src={style.metadata.thumbnail} alt="Style Thumbnail" />
				<span class="name">{style.name}</span>
			</div>
		{/each}
	</div>
</div>
