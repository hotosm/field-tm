<script lang="ts">
  import type { Map } from 'maplibre-gl';
  import type { Task } from '../lib/taskPlan';
  import { taskGeoJSON, taskGPX } from '../lib/exports';
  import { download } from '../lib/io/files';
  import { shareUrl } from '../lib/share';
  import { printTask } from '../lib/print';
  import QrCode from './QrCode.svelte';

  interface Props {
    task: Task;
    /** Needed to print the task map. */
    map?: Map;
    title?: string;
    /** Buttons only, with descriptions as tooltips (for the map popup). */
    compact?: boolean;
  }
  let { task, map, title, compact = false }: Props = $props();

  const p = $derived(task.properties);
  const link = $derived(shareUrl(task, location.href));
  let showQr = $state(false);
  let copied = $state(false);
  let printError = $state<string | null>(null);

  async function print() {
    if (!map) return;
    printError = null;
    try {
      await printTask(map, task, title);
    } catch (e) {
      printError = e instanceof Error ? e.message : String(e);
    }
  }

  const gpx = () => download(`task-${p.task_id}.gpx`, taskGPX(task), 'application/gpx+xml');
  const geojson = () => download(`task-${p.task_id}.geojson`, taskGeoJSON(task));

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {
      /* clipboard blocked; the link is still selectable */
    }
  }
</script>

{#if compact}
  <div class="grid">
    <wa-button size="s" appearance="outlined" onclick={gpx} title="GPX for OsmAnd, CoMaps, Organic Maps or a GPS">GPX</wa-button>
    <wa-button size="s" appearance="outlined" onclick={geojson} title="GeoJSON for QGIS, JOSM or other tools">GeoJSON</wa-button>
    {#if map}<wa-button size="s" appearance="outlined" onclick={print} title="Paper map for the field (save as PDF)">Print / PDF</wa-button>{/if}
    <wa-button size="s" appearance="outlined" onclick={copy} title="Link to open the task on a phone">{copied ? 'Copied' : 'Copy link'}</wa-button>
    <wa-button size="s" appearance="outlined" onclick={() => (showQr = !showQr)} aria-expanded={showQr}>QR code</wa-button>
  </div>
{:else}
  <ul class="uses">
    <li>
      <span><strong>Navigate</strong><small>GPX for OsmAnd, CoMaps, Organic Maps or a GPS</small></span>
      <wa-button size="s" appearance="outlined" onclick={gpx}>Download GPX</wa-button>
    </li>
    {#if map}
      <li>
        <span><strong>Print</strong><small>Paper map for the field (save as PDF)</small></span>
        <wa-button size="s" appearance="outlined" onclick={print}>Print / PDF</wa-button>
      </li>
    {/if}
    <li>
      <span><strong>Share</strong><small>Link or QR code to open on a phone</small></span>
      <span class="row">
        <wa-button size="s" appearance="outlined" onclick={copy}>{copied ? 'Copied' : 'Copy link'}</wa-button>
        <wa-button size="s" appearance="outlined" onclick={() => (showQr = !showQr)} aria-expanded={showQr}>QR code</wa-button>
      </span>
    </li>
    <li>
      <span><strong>GIS</strong><small>GeoJSON for QGIS, JOSM or other tools</small></span>
      <wa-button size="s" appearance="outlined" onclick={geojson}>Download GeoJSON</wa-button>
    </li>
  </ul>
{/if}
{#if printError}<wa-callout variant="warning" size="s">{printError}</wa-callout>{/if}
{#if showQr}<QrCode text={link} />{/if}

<style>
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--wa-space-2xs);
  }
  .uses {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: var(--wa-space-xs);
  }
  .uses li {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: var(--wa-space-xs);
  }
  .uses small {
    display: block;
    color: var(--wa-color-text-quiet);
  }
</style>
