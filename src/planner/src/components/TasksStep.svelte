<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import type { Tool } from './MapView.svelte';
  import { GROUP_PATTERN } from '../lib/taskPlan';
  import { taskColour } from '../lib/colours';
  import TaskDetails from './TaskDetails.svelte';
  import Legend from './Legend.svelte';

  interface Props {
    planner: Planner;
    tool: Tool;
    multi: boolean;
    onsplit: () => void;
    /** Reopens the task's downloads popup after it was closed. */
    onactions?: () => void;
  }
  let { planner, tool = $bindable(), multi = $bindable(), onsplit, onactions }: Props = $props();

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
  <p>No tasks yet.</p>
  <wa-button size="s" variant="brand" onclick={onsplit}>Split the area</wa-button>
{:else}
  <p class="hint">Click tasks on the map to select them. Shift-click, or turn on multi-select, to select several.</p>
  <div class="row">
    <wa-switch size="s" checked={multi} onchange={(e: Event) => (multi = (e.currentTarget as HTMLInputElement).checked)}>Multi-select</wa-switch>
    <wa-button size="s" appearance="outlined" onclick={() => (planner.selected = planner.tasks.map((t) => t.properties.task_id))}>Select all</wa-button>
    <wa-button size="s" appearance="outlined" onclick={() => (planner.selected = [])} disabled={!n}>Clear selection</wa-button>
  </div>

  {#if n}
    <p><strong>{n} selected</strong></p>
    <div class="row">
      <wa-button size="s" appearance="outlined" onclick={() => planner.mergeSelected()} disabled={n < 2 || !!planner.busy}>Merge</wa-button>
      <wa-button size="s" variant={tool === 'line' ? 'brand' : 'neutral'} appearance={tool === 'line' ? 'accent' : 'outlined'} onclick={() => (tool = tool === 'line' ? 'none' : 'line')} disabled={n !== 1}>Split with line</wa-button>
      <wa-button size="s" appearance="outlined" onclick={() => (tool = 'edit')} disabled={n !== 1}>Edit shape</wa-button>
      <wa-button size="s" variant="danger" appearance="outlined" onclick={() => planner.deleteSelected()}>Delete</wa-button>
    </div>
    {#if tool === 'line'}<p class="hint">Draw a line across the task; double-click (or click the last point again) to finish.</p>{/if}
  {/if}

  {#if single}
    <TaskDetails task={single} onassign={(patch) => planner.assignSelected(patch)} />
    {#if onactions}<div><wa-button size="s" appearance="outlined" onclick={onactions}>Downloads and sharing</wa-button></div>{/if}
  {:else if n > 1}
    <form onsubmit={bulk} class="stack">
      <h3>Assign {n} tasks</h3>
      <p class="hint">Blank fields are left unchanged.</p>
      <wa-input size="s" label="Group" name="assigned_group" pattern={GROUP_PATTERN} placeholder="e.g. team-a"></wa-input>
      <wa-input size="s" label="Assigned to" name="assigned_to"></wa-input>
      <wa-input size="s" label="Comment" name="comment"></wa-input>
      <div class="row">
        <wa-button size="s" type="submit" variant="brand">Assign</wa-button>
        <wa-button size="s" appearance="outlined" onclick={() => planner.assignSelected({ assigned_group: '', assigned_to: '', comment: '', colour: '' })}>Clear assignment</wa-button>
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
          {#if t.properties.feature_count != null}<small class="count">{t.properties.feature_count} features</small>{/if}
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
  .tasklist li {
    margin: 0;
  }
  .tasklist button {
    width: 100%;
    justify-content: flex-start;
    display: flex;
    gap: 0.5rem;
    align-items: center;
    text-align: left;
    border: 0;
    border-bottom: 1px solid var(--border);
    border-radius: 0;
    background: none;
    padding: var(--wa-space-2xs) var(--wa-space-xs);
    font: inherit;
    color: inherit;
    cursor: pointer;
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
