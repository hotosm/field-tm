<script lang="ts">
  import type { Task } from '../lib/taskPlan';
  import { GROUP_PATTERN } from '../lib/taskPlan';
  import { taskGeoJSON, taskGPX } from '../lib/exports';
  import { download } from '../lib/io/files';
  import { shareUrl } from '../lib/share';
  import { groupColour } from '../lib/colours';
  import type { Assignment } from '../lib/planEdit';
  import QrCode from './QrCode.svelte';

  interface Props {
    task: Task;
    readonly?: boolean;
    onassign?: (patch: Assignment) => void;
  }
  let { task, readonly = false, onassign }: Props = $props();

  const p = $derived(task.properties);
  const link = $derived(shareUrl(task, location.href));
  const shownColour = $derived(p.colour ?? groupColour(p.assigned_group));
  let showQr = $state(false);
  let copied = $state(false);

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
      colour: colour === shownColour ? (p.colour ?? '') : colour,
    });
  }
</script>

<section class="task" aria-label="Task {p.task_id}">
  <h3>Task {p.task_id}</h3>
  {#if p.building_count != null}<p class="hint">{p.building_count} buildings</p>{/if}

  {#if readonly}
    <dl>
      {#if p.assigned_group}<dt>Group</dt><dd>{p.assigned_group}</dd>{/if}
      {#if p.assigned_to}<dt>Assigned to</dt><dd>{p.assigned_to}</dd>{/if}
      {#if p.comment}<dt>Comment</dt><dd>{p.comment}</dd>{/if}
    </dl>
  {:else}
    {#key task}
      <form onsubmit={save} class="stack">
        <label>Group <input name="assigned_group" value={p.assigned_group ?? ''} pattern={GROUP_PATTERN} placeholder="e.g. team-a" /></label>
        <label>Assigned to <input name="assigned_to" value={p.assigned_to ?? ''} placeholder="Name or username" /></label>
        <label>Comment <textarea name="comment" rows="2">{p.comment ?? ''}</textarea></label>
        <label class="row">Colour <input type="color" name="colour" value={shownColour} /></label>
        <button type="submit" class="primary">Save task</button>
      </form>
    {/key}
  {/if}

  <div class="row wrap">
    <button type="button" onclick={() => download(`task-${p.task_id}.geojson`, taskGeoJSON(task))}>GeoJSON</button>
    <button type="button" onclick={() => download(`task-${p.task_id}.gpx`, taskGPX(task), 'application/gpx+xml')}>GPX</button>
    <button type="button" onclick={copy}>{copied ? 'Copied' : 'Copy link'}</button>
    <button type="button" onclick={() => (showQr = !showQr)} aria-expanded={showQr}>QR code</button>
  </div>
  {#if showQr}<QrCode text={link} />{/if}
</section>

<style>
  dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.2rem 0.75rem;
    margin: 0.5rem 0;
  }
  dt {
    font-weight: 600;
  }
  dd {
    margin: 0;
  }
</style>
