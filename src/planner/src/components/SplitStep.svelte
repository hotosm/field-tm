<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { classify, type SplitAlgorithm } from '../lib/engine/splitter';
  import { estimateTasks, gridSize, recommend, MAX_TASKS } from '../lib/recommend';

  let { planner, ondone }: { planner: Planner; ondone?: () => void } = $props();

  const data = $derived(classify(planner.features, planner.roads));
  const available = $derived<{ id: SplitAlgorithm; label: string; help: string; ok: boolean }[]>([
    { id: 'DIVIDE_BY_SQUARE', label: 'Square grid', help: 'Equal squares. Needs no data.', ok: true },
    { id: 'SPLIT_BY_ROADS', label: 'By roads', help: 'Blocks bounded by main roads, rivers and railways.', ok: data.lines.length > 0 },
    { id: 'AVG_BUILDING_VORONOI', label: 'By number of buildings', help: 'Groups nearby buildings into tasks of similar size.', ok: data.polys.length > 0 },
  ]);

  const rec = $derived(planner.aoi ? recommend(planner.aoi, data.polys.length) : null);
  let algorithm = $state<SplitAlgorithm>('DIVIDE_BY_SQUARE');
  let cellSize = $state(500);
  let numBuildings = $state(50);
  let onlySelected = $state(false);

  // Adopt the recommendation whenever the inputs change.
  $effect(() => {
    if (!rec) return;
    algorithm = rec.algorithm;
    if (planner.aoi) cellSize = gridSize(planner.aoi);
    if (rec.params.num_buildings) numBuildings = rec.params.num_buildings;
  });

  const params = $derived(algorithm === 'DIVIDE_BY_SQUARE' ? { cell_size: cellSize } : algorithm === 'AVG_BUILDING_VORONOI' ? { num_buildings: numBuildings } : {});
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
  <fieldset>
    <legend>Method</legend>
    {#each available as a (a.id)}
      <label class="choice" class:disabled={!a.ok}>
        <input type="radio" name="algorithm" value={a.id} bind:group={algorithm} disabled={!a.ok} />
        <span><strong>{a.label}</strong><br /><small>{a.ok ? a.help : a.id === 'SPLIT_BY_ROADS' ? 'Add roads in step 2.' : 'Upload features in step 2.'}</small></span>
      </label>
    {/each}
  </fieldset>

  {#if algorithm === 'DIVIDE_BY_SQUARE'}
    <label>Square size (metres) <input type="number" min="10" max="100000" step="10" bind:value={cellSize} /></label>
  {:else if algorithm === 'AVG_BUILDING_VORONOI'}
    <label>Buildings per task <input type="number" min="1" max="10000" bind:value={numBuildings} /></label>
  {/if}
  {#if estimate}
    <p class:warn={estimate > MAX_TASKS}>About {estimate} tasks{estimate > MAX_TASKS ? ' — consider larger tasks' : ''}.</p>
  {/if}

  {#if planner.selected.length}
    <label class="row"><input type="checkbox" bind:checked={onlySelected} /> Only re-split the {planner.selected.length} selected task(s)</label>
  {/if}
  <button type="button" class="primary" onclick={go} disabled={!!planner.busy}>
    {planner.tasks.length ? 'Split again' : 'Split'}
  </button>
  {#if planner.tasks.length && !onlySelected}<p class="hint">Splitting again replaces all tasks. You can undo.</p>{/if}
{/if}

<style>
  .choice {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
    padding: 0.3rem 0;
  }
  .disabled {
    opacity: 0.55;
  }
  .warn {
    color: var(--warn);
  }
</style>
