<script lang="ts">
    import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
    import type { SlSelectEvent } from '@shoelace-style/shoelace/dist/events';
    // FIXME this is a workaround to re-import, as using hot-select
    // and hot-option prevents selection of values!
    // TODO should raise an issue in hotosm/ui about this / test further
	import '@shoelace-style/shoelace/dist/components/select/select.js';
	import '@shoelace-style/shoelace/dist/components/option/option.js';
	import '@shoelace-style/shoelace/dist/components/button/button.js';

    import type { Basemap } from '$lib/utils/basemaps';
    import { getProjectBasemapStore } from '$store/common.svelte.ts';
	import { loadOnlinePmtiles, writeOfflinePmtiles } from '$lib/utils/basemaps';

	interface Props {
        projectId: number;
		children?: Snippet;
	}

	let { projectId, children }: Props = $props();
	const basemapStore = getProjectBasemapStore();
	let selectedBasemap: Basemap | null = $state(null);

    // Reactive variables
	let basemapsAvailable: boolean = $derived(basemapStore.projectBasemaps && basemapStore.projectBasemaps.length > 0);

	onMount(() => {
        basemapStore.refreshBasemaps(projectId);
	});
</script>

<div class="flex flex-col items-center p-4 space-y-4">
    <!-- Text above the basemap selector -->
    <div class="text-center w-full">
        <div class="font-bold text-lg font-barlow-medium">
            <span class="mr-1">Manage Basemaps</span>
        </div>
    </div>

    <!-- Basemap selector -->
    <div class="flex justify-center w-full max-w-sm">
        {#if basemapsAvailable}
            <!-- Note here we cannot two way bind:var to the web-component,
            so use event instead -->
            <sl-select
                placeholder="Select a basemap"
                onsl-change={(event: SlSelectEvent) => {
                    const selectedId = event.originalTarget.value
                    selectedBasemap = basemapStore.projectBasemaps?.find((basemap: Basemap) => basemap.id === selectedId) || null
                }}
            >
                {#each basemapStore.projectBasemaps as basemap}
                {#if basemap.status === "SUCCESS"}
                    <sl-option value={basemap.id}>
                        {basemap.tile_source} {basemap.format}
                    </sl-option>
                {/if}
                {/each}
            </sl-select>
        {:else}
            <div class="text-center w-full">
                <div class="text-sm font-barlow-medium">
                    There are no basemaps available for this project.
                </div>
                <div class="text-sm font-barlow-medium pt-2">
                    Please ask the project manager to create basemaps.
                </div>
            </div>
        {/if}
    </div>

    <!-- Load baselayer & download to OPFS buttons -->
    {#if selectedBasemap && selectedBasemap.format === 'pmtiles' }
        <hot-button
            onclick={() => loadOnlinePmtiles(selectedBasemap.url)}
            onkeydown={(e: KeyboardEvent) => {
                e.key === 'Enter' && loadOnlinePmtiles(selectedBasemap.url);
            }}
            role="button"
            tabindex="0"
            size="small"
            class="secondary w-full max-w-[200px]"
        >
            <hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
            ></hot-icon>
            <span class="font-barlow-medium text-base uppercase">Show On Map</span>
        </hot-button>

        <hot-button
            onclick={() => writeOfflinePmtiles(projectId, selectedBasemap.url)}
            onkeydown={(e: KeyboardEvent) => {
                e.key === 'Enter' && writeOfflinePmtiles(projectId, selectedBasemap.url);
            }}
            role="button"
            tabindex="0"
            size="small"
            class="secondary w-full max-w-[200px]"
        >
            <hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
            ></hot-icon>
            <span class="font-barlow-medium text-base uppercase">Store Offline</span>
        </hot-button>

    <!-- Download Mbtiles Button -->
    {:else if selectedBasemap && selectedBasemap.format === 'mbtiles' }
        <hot-button
            onclick={() => window.open(selectedBasemap.url)}
            onkeydown={(e: KeyboardEvent) => {
                e.key === 'Enter' && window.open(selectedBasemap.url);
            }}
            role="button"
            tabindex="0"
            size="small"
            class="secondary w-full max-w-[200px]"
        >
            <hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
            ></hot-icon>
            <span class="font-barlow-medium text-base uppercase">Download MBTiles</span>
        </hot-button>
    {/if}

    {@render children?.()}
</div>
