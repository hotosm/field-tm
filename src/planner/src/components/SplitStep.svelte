<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { classify, SKELETON_MAX_FEATURES, type SplitAlgorithm } from '../lib/engine/splitter';
  import { dropEmptyByDefault, estimateTasks, gridSize, recommend, MAX_TASKS } from '../lib/recommend';

  let { planner, ondone }: { planner: Planner; ondone?: () => void } = $props();

  const data = $derived(classify(planner.features, planner.roads));
  const available = $derived<{ id: SplitAlgorithm; label: string; help: string; ok: boolean }[]>([
    { id: 'DIVIDE_BY_SQUARE', label: 'Square grid', help: 'Equal squares. Needs no data.', ok: true },
    { id: 'SPLIT_BY_ROADS', label: 'By roads', help: 'Blocks bounded by streets, rivers and railways. Suits walking or street imagery routes.', ok: data.lines.length > 0 },
    { id: 'AVG_BUILDING_SKELETON', label: 'Similar-sized tasks, following streets', help: 'Groups nearby features; task edges run along streets and gaps between features. Takes a little longer.', ok: data.polys.length > 0 && data.polys.length <= SKELETON_MAX_FEATURES },
    { id: 'AVG_BUILDING_VORONOI', label: 'Similar-sized tasks, quick', help: 'Groups nearby features fast; edges can cut between features. Best for very large areas.', ok: data.polys.length > 0 },
  ]);
  const unavailable = (id: SplitAlgorithm) =>
    id === 'SPLIT_BY_ROADS' ? 'Add roads, rivers and railways in step 2.' : data.polys.length > SKELETON_MAX_FEATURES ? `Only for up to ${SKELETON_MAX_FEATURES} features.` : 'Add features to map in step 2.';

  const rec = $derived(planner.aoi ? recommend(planner.aoi, data.polys.length, data.lines.length) : null);
  let algorithm = $state<SplitAlgorithm>('DIVIDE_BY_SQUARE');
  let cellSize = $state(500);
  let numFeatures = $state(50);
  let byCount = $state(false);
  let numTasks = $state(10);
  let mainRoadsOnly = $state(false);
  let onlySelected = $state(false);
  // Resets when the method changes; the checkbox can still override it.
  let dropEmpty = $derived(dropEmptyByDefault(algorithm));
  const byFeatures = $derived(algorithm === 'AVG_BUILDING_VORONOI' || algorithm === 'AVG_BUILDING_SKELETON');

  // Adopt the recommendation whenever the inputs change.
  $effect(() => {
    if (!rec) return;
    algorithm = rec.algorithm;
    if (planner.aoi) cellSize = gridSize(planner.aoi);
    if (rec.params.num_buildings) {
      numFeatures = rec.params.num_buildings;
      numTasks = Math.ceil(data.polys.length / numFeatures);
    }
  });

  const params = $derived({
    ...(algorithm === 'DIVIDE_BY_SQUARE' ? { cell_size: cellSize } : {}),
    ...(algorithm === 'SPLIT_BY_ROADS' ? { include_minor_roads: !mainRoadsOnly } : {}),
    ...(byFeatures ? (byCount ? { num_enumerators: numTasks } : { num_buildings: numFeatures }) : {}),
    ...(data.polys.length && !(byFeatures && byCount) ? { drop_empty: dropEmpty } : {}),
  });
  const estimate = $derived(planner.aoi ? estimateTasks(planner.aoi, algorithm, params, data.polys.length) : null);

  async function go() {
    if (onlySelected && planner.selected.length) await planner.resplitSelected(algorithm, params);
    else await planner.split(algorithm, params);
    if (!planner.error) ondone?.();
  }
</script>

{#if !planner.aoi}
  <p>Set the area first.</p>
{:else}
  {#if rec}<p class="hint">Recommended: {rec.note}</p>{/if}
  <fieldset class="stack">
    <legend>Method</legend>
    {#each available as a (a.id)}
      <label class="choice" class:disabled={!a.ok}>
        <input type="radio" name="algorithm" value={a.id} bind:group={algorithm} disabled={!a.ok} />
        <span><strong>{a.label}</strong>{#if rec?.algorithm === a.id} <wa-badge variant="success" pill>Recommended</wa-badge>{/if}<br /><small>{a.ok ? a.help : unavailable(a.id)}</small></span>
      </label>
    {/each}
  </fieldset>

  {#if algorithm === 'DIVIDE_BY_SQUARE'}
    <wa-input label="Square size (metres)" type="number" min="10" max="100000" step="10" value={String(cellSize)} oninput={(e: Event) => (cellSize = Number((e.currentTarget as HTMLInputElement).value))}></wa-input>
  {:else if algorithm === 'SPLIT_BY_ROADS'}
    <wa-checkbox checked={mainRoadsOnly} onchange={(e: Event) => (mainRoadsOnly = (e.currentTarget as HTMLInputElement).checked)}>Main roads only</wa-checkbox>
    <p class="hint">Ignores residential and other minor streets, for bigger blocks.</p>
  {:else if byFeatures}
    <div class="row">
      <label><input type="radio" name="size-by" checked={!byCount} onchange={() => (byCount = false)} /> Features per task</label>
      <label><input type="radio" name="size-by" checked={byCount} onchange={() => (byCount = true)} /> Number of tasks</label>
    </div>
    {#if byCount}
      <wa-input label="Number of tasks" hint="E.g. one per mapper or team." type="number" min="1" max={String(data.polys.length)} value={String(numTasks)} oninput={(e: Event) => (numTasks = Number((e.currentTarget as HTMLInputElement).value))}></wa-input>
    {:else}
      <wa-input label="Features per task" type="number" min="1" max="10000" value={String(numFeatures)} oninput={(e: Event) => (numFeatures = Number((e.currentTarget as HTMLInputElement).value))}></wa-input>
    {/if}
  {/if}
  {#if estimate}
    <p class:warn={estimate > MAX_TASKS}>About {estimate} tasks{estimate > MAX_TASKS ? ' - consider larger tasks' : ''}.</p>
  {/if}

  {#if data.polys.length && !(byFeatures && byCount)}
    <wa-checkbox checked={dropEmpty} onchange={(e: Event) => (dropEmpty = (e.currentTarget as HTMLInputElement).checked)}>Remove tasks with nothing to map</wa-checkbox>
    <p class="hint">Untick to keep them, e.g. if mappers should add missing features there.</p>
  {/if}
  {#if planner.selected.length}
    <wa-checkbox checked={onlySelected} onchange={(e: Event) => (onlySelected = (e.currentTarget as HTMLInputElement).checked)}>Only re-split the {planner.selected.length} selected task(s)</wa-checkbox>
  {/if}
  <div>
    <wa-button class="cta" variant="brand" onclick={go} disabled={!!planner.busy} loading={!!planner.busy}>
      {planner.tasks.length ? 'Split again' : 'Split'}
    </wa-button>
  </div>
  {#if planner.tasks.length && !onlySelected}<p class="hint">Splitting again replaces all tasks. You can undo.</p>{/if}
{/if}

<style>
  fieldset {
    margin: 0;
    border: 1px solid var(--border);
    border-radius: var(--wa-border-radius-m);
  }
  .choice {
    display: flex;
    gap: var(--wa-space-xs);
    align-items: flex-start;
  }
  .row {
    display: flex;
    gap: var(--wa-space-m);
  }
  .disabled {
    opacity: 0.55;
  }
  .warn {
    color: var(--wa-color-warning-on-quiet);
  }
</style>
