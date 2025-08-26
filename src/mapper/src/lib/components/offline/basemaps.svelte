<script lang="ts">
	import '$styles/basemaps.css';
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
	import type { SlSelectEvent } from '@shoelace-style/shoelace/dist/events';
	// FIXME this is a workaround to re-import, as using hot-select
	// and hot-option prevents selection of values!
	// perhaps related to https://github.com/hotosm/ui/issues/73
	import '@shoelace-style/shoelace/dist/components/select/select.js';
	import '@shoelace-style/shoelace/dist/components/option/option.js';
	import '@shoelace-style/shoelace/dist/components/button/button.js';
	// import '@shoelace-style/shoelace/dist/components/progress-bar/progress-bar.js';

	import type { Basemap } from '$lib/map/basemaps';
	import { getProjectBasemapStore } from '$store/common.svelte.ts';
	import { loadOnlinePmtiles, writeOfflinePmtiles } from '$lib/map/basemaps';
	import { m } from '$translations/messages.js';

	interface Props {
		projectId: number;
		children?: Snippet;
	}

	let { projectId, children }: Props = $props();
	const basemapStore = getProjectBasemapStore();
	let selectedBasemap: Basemap | null = $state(null);
	let pmtilesDownloadProgress = $state(0);

	// Reactive variables
	let basemapsAvailable: boolean = $derived(basemapStore.projectBasemaps && basemapStore.projectBasemaps.length > 0);

	function downloadPmtilesWithProgress() {
		pmtilesDownloadProgress = 0;

		writeOfflinePmtiles(projectId, selectedBasemap?.url, (percent) => {
			pmtilesDownloadProgress = percent;
		});
	}

	onMount(() => {
		basemapStore.refreshBasemaps(projectId);
	});
</script>

<div class="basemaps">
	<!-- Text above the basemap selector -->
	<div class="text-above">
		<div class="basemaps-content">
			<span>{m['basemaps.manage']()}</span>
		</div>
	</div>

	<!-- Basemap selector -->
	<div class="selector">
		{#if basemapsAvailable}
			<!-- Note here we cannot two way bind:var to the web-component,
            so use event instead -->
			<sl-select
				placeholder="Select a basemap"
				onsl-change={(event: SlSelectEvent) => {
					const selectedId = event.target.value;
					selectedBasemap = basemapStore.projectBasemaps?.find((basemap: Basemap) => basemap.id === selectedId) || null;
				}}
			>
				{#each basemapStore.projectBasemaps as basemap}
					{#if basemap.status === 'SUCCESS'}
						<sl-option value={basemap.id}>
							{basemap.tile_source}
							{basemap.format}
						</sl-option>
					{/if}
				{/each}
			</sl-select>
		{:else}
			<div class="no-basemaps-available">
				<div class="msg1">{m['basemaps.no_basemaps_available']()}</div>
				<div class="msg2">{m['basemaps.ask_pm']()}</div>
			</div>
		{/if}
	</div>

	<!-- Load baselayer & download to OPFS buttons -->
	{#if selectedBasemap && selectedBasemap.format === 'pmtiles'}
		<sl-button
			onclick={() => loadOnlinePmtiles(selectedBasemap?.url)}
			onkeydown={(e: KeyboardEvent) => {
				e.key === 'Enter' && loadOnlinePmtiles(selectedBasemap?.url);
			}}
			role="button"
			tabindex="0"
			size="small"
			class="button"
		>
			<sl-icon slot="prefix" name="download" class="icon"></sl-icon>
			<span>{m['basemaps.show_on_map']()}</span>
		</sl-button>

		<sl-button
			onclick={() => downloadPmtilesWithProgress()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') downloadPmtilesWithProgress();
			}}
			role="button"
			tabindex="0"
			size="small"
			class="button"
		>
			<sl-icon slot="prefix" name="download" class="icon"></sl-icon>
			<span>{m['basemaps.store_offline']()}</span>
		</sl-button>

		<!-- Offline download progress bar -->
		<div class="progress-container">
			<sl-progress-bar value={pmtilesDownloadProgress}></sl-progress-bar>
		</div>

		<!-- Download Mbtiles Button -->
	{:else if selectedBasemap && selectedBasemap.format === 'mbtiles'}
		<sl-button
			onclick={() => window.open(selectedBasemap?.url)}
			onkeydown={(e: KeyboardEvent) => {
				e.key === 'Enter' && window.open(selectedBasemap?.url);
			}}
			role="button"
			tabindex="0"
			size="small"
			class="button"
		>
			<sl-icon slot="prefix" name="download" class="icon"></sl-icon>
			<span>{m['basemaps.download_mbtiles']()}</span>
		</sl-button>
	{/if}

	{@render children?.()}
</div>
