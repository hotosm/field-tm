<script lang="ts">
  import type { Task } from '../lib/taskPlan';
  import { GROUP_PATTERN } from '../lib/taskPlan';
  import { taskGeoJSON, taskGPX } from '../lib/exports';
  import { download } from '../lib/io/files';
  import { shareUrl } from '../lib/share';
  import { groupColour } from '../lib/colours';
  import type { Assignment } from '../lib/planEdit';
  import QrCode from './QrCode.svelte';
  import type { Map } from 'maplibre-gl';
  import { printTask } from '../lib/print';

  interface Props {
    task: Task;
    readonly?: boolean;
    /** Needed to print the task map. */
    map?: Map;
    title?: string;
    onassign?: (patch: Assignment) => void;
  }
  let { task, readonly = false, map, title, onassign }: Props = $props();

  const p = $derived(task.properties);
  const link = $derived(shareUrl(task, location.href));
  const shownColour = $derived(p.colour ?? groupColour(p.assigned_group));
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

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {
      /* clipboard blocked; the link is still selectable */
    }
  }

  function save(e: SubmitEvent) {
    e.preventDefault();
    const f = new FormData(e.currentTarget as HTMLFormElement);
    const colour = String(f.get('colour'));
    onassign?.({
      assigned_group: String(f.get('assigned_group') ?? ''),
      assigned_to: String(f.get('assigned_to') ?? ''),
      comment: String(f.get('comment') ?? ''),
      // Store a colour only when the user picked one; otherwise it follows the group.
      colour: colour.toLowerCase() === shownColour.toLowerCase() ? (p.colour ?? '') : colour,
    });
  }
</script>

<section class="stack" aria-label="Task {p.task_id}">
  <h3>Task {p.task_id}</h3>
  {#if p.feature_count != null}<p class="hint">{p.feature_count} features</p>{/if}

  {#if readonly}
    <dl>
      {#if p.assigned_group}<dt>Group</dt><dd>{p.assigned_group}</dd>{/if}
      {#if p.assigned_to}<dt>Assigned to</dt><dd>{p.assigned_to}</dd>{/if}
      {#if p.comment}<dt>Comment</dt><dd>{p.comment}</dd>{/if}
    </dl>
  {:else}
    {#key task}
      <form onsubmit={save} class="stack">
        <wa-input size="s" label="Group" name="assigned_group" value={p.assigned_group ?? ''} pattern={GROUP_PATTERN} placeholder="e.g. team-a"></wa-input>
        <wa-input size="s" label="Assigned to" name="assigned_to" value={p.assigned_to ?? ''} placeholder="Name or username"></wa-input>
        <wa-textarea size="s" label="Comment" name="comment" rows="2" value={p.comment ?? ''}></wa-textarea>
        <wa-color-picker size="s" label="Colour" name="colour" value={shownColour}></wa-color-picker>
        <div><wa-button size="s" type="submit" variant="brand">Save task</wa-button></div>
      </form>
    {/key}
  {/if}

  <h4>Use this task</h4>
  <ul class="uses">
    <li>
      <span><strong>Navigate</strong><small>GPX for OsmAnd, CoMaps, Organic Maps or a GPS</small></span>
      <wa-button size="s" appearance="outlined" onclick={() => download(`task-${p.task_id}.gpx`, taskGPX(task), 'application/gpx+xml')}>Download GPX</wa-button>
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
      <wa-button size="s" appearance="outlined" onclick={() => download(`task-${p.task_id}.geojson`, taskGeoJSON(task))}>Download GeoJSON</wa-button>
    </li>
  </ul>
  {#if printError}<wa-callout variant="warning" size="s">{printError}</wa-callout>{/if}
  {#if showQr}<QrCode text={link} />{/if}
</section>

<style>
  h3,
  h4 {
    margin: 0;
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
  dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--wa-space-2xs) var(--wa-space-s);
    margin: 0;
  }
  dt {
    font-weight: 600;
  }
  dd {
    margin: 0;
  }
</style>
