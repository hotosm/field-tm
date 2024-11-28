<script lang="ts">
    import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
    import type { UUID } from 'crypto';
    import type { SlSelectEvent } from '@shoelace-style/shoelace/dist/events';
    // FIXME this is a workaround to re-import, as using hot-select
    // and hot-option prevents selection of values!
    // TODO should raise an issue in hotosm/ui about this / test further
	import '@shoelace-style/shoelace/dist/components/select/select.js';
	import '@shoelace-style/shoelace/dist/components/option/option.js';

    import type { Basemap } from '$lib/utils/basemaps';
    import { getProjectBasemapStore } from '$store/common.svelte.ts';
	import { downloadMbtiles, loadOnlinePmtiles, writeOfflinePmtiles } from '$lib/utils/basemaps';

	interface Props {
        projectId: number;
		children?: Snippet;
	}

	let { projectId, children }: Props = $props();
	const basemapStore = getProjectBasemapStore();

    let selectedBasemapId: UUID | null = $state(null);

    // Reactive variables
	let basemapsAvailable: boolean = $derived(basemapStore.projectBasemaps && basemapStore.projectBasemaps.length > 0);
	let selectedBasemap: Basemap | null = $derived(basemapStore.projectBasemaps?.find((basemap: Basemap) => basemap.id === selectedBasemapId) || null);

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
                    const selection = event.originalTarget.value
                    selectedBasemapId = selection;
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
    {#if selectedBasemap?.format === 'pmtiles' }
        <sl-button
            onclick={() => loadOnlinePmtiles(selectedBasemap)}
            onkeydown={(e: KeyboardEvent) => {
                e.key === 'Enter' && loadOnlinePmtiles(selectedBasemap);
            }}
            role="button"
            tabindex="0"
            size="small"
            class="secondary w-full max-w-[200px]"
        >
            <hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
            ></hot-icon>
            <span class="font-barlow-medium text-base uppercase">Show On Map</span>
        </sl-button>

        <sl-button
            onclick={() => writeOfflinePmtiles(projectId, selectedBasemapId)}
            onkeydown={(e: KeyboardEvent) => {
                e.key === 'Enter' && writeOfflinePmtiles(projectId, selectedBasemapId);
            }}
            role="button"
            tabindex="0"
            size="small"
            class="secondary w-full max-w-[200px]"
        >
            <hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
            ></hot-icon>
            <span class="font-barlow-medium text-base uppercase">Store Offline</span>
        </sl-button>

    <!-- Download Mbtiles Button -->
    {:else if selectedBasemap?.format === 'mbtiles' }
        <sl-button
            onclick={() => downloadMbtiles(projectId, selectedBasemapId)}
            onkeydown={(e: KeyboardEvent) => {
                e.key === 'Enter' && downloadMbtiles(projectId, selectedBasemapId);
            }}
            role="button"
            tabindex="0"
            size="small"
            class="secondary w-full max-w-[200px]"
        >
            <hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"
            ></hot-icon>
            <span class="font-barlow-medium text-base uppercase">Download MBTiles</span>
        </sl-button>
    {/if}

    {@render children?.()}
</div>
