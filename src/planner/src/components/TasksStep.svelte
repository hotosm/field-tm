<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import type { Tool } from './MapView.svelte';
  import { GROUP_PATTERN } from '../lib/taskPlan';
  import { taskColour } from '../lib/colours';
  import TaskDetails from './TaskDetails.svelte';
  import Legend from './Legend.svelte';

  let { planner, tool = $bindable(), multi = $bindable() }: { planner: Planner; tool: Tool; multi: boolean } = $props();

  const n = $derived(planner.selected.length);
  const single = $derived(n === 1 ? planner.selectedTasks[0] : undefined);

  function bulk(e: SubmitEvent) {
    e.preventDefault();
    const f = new FormData(e.currentTarget as HTMLFormElement);
    const v = (k: string) => String(f.get(k) ?? '').trim() || undefined; // blank = keep
    planner.assignSelected({ assigned_group: v('assigned_group'), assigned_to: v('assigned_to'), comment: v('comment') });
  }
</script>

{#if !planner.tasks.length}
  <p>Split the area first.</p>
{:else}
  <p class="hint">Click tasks on the map to select them. Shift-click, or turn on multi-select, to select several.</p>
  <div class="row wrap">
    <label class="row"><input type="checkbox" bind:checked={multi} /> Multi-select</label>
    <button type="button" onclick={() => (planner.selected = planner.tasks.map((t) => t.properties.task_id))}>Select all</button>
    <button type="button" onclick={() => (planner.selected = [])} disabled={!n}>Clear selection</button>
  </div>

  {#if n}
    <p><strong>{n} selected</strong></p>
    <div class="row wrap">
      <button type="button" onclick={() => planner.mergeSelected()} disabled={n < 2 || !!planner.busy}>Merge</button>
      <button type="button" aria-pressed={tool === 'line'} onclick={() => (tool = tool === 'line' ? 'none' : 'line')} disabled={n !== 1}>Split with line</button>
      <button type="button" onclick={() => (tool = 'edit')} disabled={n !== 1}>Edit shape</button>
      <button type="button" class="danger" onclick={() => planner.deleteSelected()}>Delete</button>
    </div>
    {#if tool === 'line'}<p class="hint">Draw a line across the task; double-click (or click the last point again) to finish.</p>{/if}
  {/if}

  {#if single}
    <TaskDetails task={single} onassign={(patch) => planner.assignSelected(patch)} />
  {:else if n > 1}
    <form onsubmit={bulk} class="stack">
      <h3>Assign {n} tasks</h3>
      <p class="hint">Blank fields are left unchanged.</p>
      <label>Group <input name="assigned_group" pattern={GROUP_PATTERN} placeholder="e.g. team-a" /></label>
      <label>Assigned to <input name="assigned_to" /></label>
      <label>Comment <input name="comment" /></label>
      <div class="row wrap">
        <button type="submit" class="primary">Assign</button>
        <button type="button" onclick={() => planner.assignSelected({ assigned_group: '', assigned_to: '', comment: '', colour: '' })}>Clear assignment</button>
      </div>
    </form>
  {/if}

  <h3>Tasks ({planner.tasks.length})</h3>
  <Legend tasks={planner.tasks} />
  <ul class="tasklist">
    {#each planner.tasks as t (t.properties.task_id)}
      {@const id = t.properties.task_id}
      <li>
        <button type="button" class:selected={planner.selected.includes(id)} onclick={(e) => planner.toggleSelect(id, multi || e.shiftKey)}>
          <span class="swatch" style:background={taskColour(t)}></span>
          {id}
          <small>{[t.properties.assigned_group, t.properties.assigned_to].filter(Boolean).join(' · ')}</small>
          {#if t.properties.building_count != null}<small class="count">{t.properties.building_count} bldg</small>{/if}
        </button>
      </li>
    {/each}
  </ul>
{/if}

<style>
  .tasklist {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 16rem;
    overflow: auto;
  }
  .tasklist button {
    width: 100%;
    display: flex;
    gap: 0.5rem;
    align-items: center;
    text-align: left;
    border: 0;
    border-bottom: 1px solid var(--border);
    border-radius: 0;
    background: none;
  }
  .tasklist button.selected {
    background: var(--selected);
  }
  .count {
    margin-left: auto;
  }
  .swatch {
    width: 0.8rem;
    height: 0.8rem;
    border-radius: 2px;
    flex: none;
  }
</style>
