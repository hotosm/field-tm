<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { isAreaTask } from '../lib/taskPlan';
  import { classify, SKELETON_MAX_FEATURES, type SplitAlgorithm } from '../lib/engine/splitter';
  import { bbox } from '../lib/geo';
  import { canFetchRoads } from '../lib/io/postpass';
  import { dropEmptyByDefault, estimateTasks, gridSize, recommend, MAX_TASKS, ROUTE_LENGTH_M } from '../lib/recommend';

  /** The Field-TM project, or undefined when planning standalone (every method offered). */
  let { planner, project, ondone }: { planner: Planner; project?: { field_mapping_app: string | null }; ondone?: () => void } = $props();
  const fromProject = $derived(!!project);
  // Route tasks are lines, which only street imagery apps can use. ODK and QField need areas.
  const streetImagery = $derived(project?.field_mapping_app === 'Panoramax');
  const routesAllowed = $derived(!project || streetImagery);

  type Method = { id: SplitAlgorithm; label: string; help: string; ok: boolean };
  const data = $derived(classify(planner.features, planner.currentRoads));
  // Too large for PostPass and no roads supplied: nothing to guide task edges.
  const noRoads = $derived(!data.lines.length && !!planner.aoi && !canFetchRoads(bbox(planner.aoi)));
  const areaMethods = $derived<Method[]>([
    { id: 'DIVIDE_BY_SQUARE', label: 'Square grid', help: 'Equal squares. Needs no data.', ok: true },
    { id: 'SPLIT_BY_ROADS', label: 'By roads', help: 'Blocks bounded by streets, rivers and railways. Suits walking around each block.', ok: !noRoads },
    { id: 'AVG_BUILDING_SKELETON', label: 'Similar-sized tasks, following streets', help: 'Groups nearby features; task edges run along streets and gaps between features. Takes a little longer.', ok: data.polys.length > 0 && data.polys.length <= SKELETON_MAX_FEATURES },
    { id: 'AVG_BUILDING_VORONOI', label: 'Similar-sized tasks, quick', help: 'Groups nearby features fast; edges can cut between features. Best for very large areas.', ok: data.polys.length > 0 },
  ]);
  const routeMethods = $derived<Method[]>([
    { id: 'SPLIT_INTO_ROUTES', label: 'Street routes', help: 'Only for capturing street-level imagery, e.g. with Panoramax. Each task is a group of connected streets and paths to walk or drive along. To map or edit features, including roads, use an area method.', ok: !noRoads },
  ]);
  function unavailable(id: SplitAlgorithm): string {
    if (id === 'SPLIT_BY_ROADS' || id === 'SPLIT_INTO_ROUTES') return 'The area is too large to fetch roads from OpenStreetMap. Upload your own in step 2.';
    if (data.polys.length > SKELETON_MAX_FEATURES) return `Only for up to ${SKELETON_MAX_FEATURES} features.`;
    return fromProject ? 'Add features to map in the Field-TM project setup.' : 'Add features to map in step 2.';
  }

  const rec = $derived(planner.aoi ? recommend(planner.aoi, data.polys.length, data.lines.length, streetImagery && !noRoads) : null);
  let algorithm = $state<SplitAlgorithm>('DIVIDE_BY_SQUARE');
  let cellSize = $state(500);
  let routeKm = $state(ROUTE_LENGTH_M / 1000);
  let numFeatures = $state(50);
  let byCount = $state(false);
  let numTasks = $state(10);
  let mainRoadsOnly = $state(false);
  let onlySelected = $state(false);
  // Resets when the method changes; the checkbox can still override it.
  let dropEmpty = $derived(dropEmptyByDefault(algorithm));
  const byFeatures = $derived(algorithm === 'AVG_BUILDING_VORONOI' || algorithm === 'AVG_BUILDING_SKELETON');
  const byRoutes = $derived(algorithm === 'SPLIT_INTO_ROUTES');
  const selectedAreas = $derived(planner.selectedTasks.filter(isAreaTask).length);

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
    ...(byRoutes ? { route_length: routeKm * 1000 } : {}),
    ...(byFeatures ? (byCount ? { num_enumerators: numTasks } : { num_buildings: numFeatures }) : {}),
    ...(data.polys.length && !byRoutes && !(byFeatures && byCount) ? { drop_empty: dropEmpty } : {}),
  });
  const estimate = $derived(planner.aoi ? estimateTasks(planner.aoi, algorithm, params, data.polys.length) : null);

  async function go() {
    if (onlySelected && selectedAreas) await planner.resplitSelected(algorithm, params);
    else await planner.split(algorithm, params);
    if (!planner.error) ondone?.();
  }
</script>

{#if !planner.aoi}
  <p>Set the area first.</p>
{:else}
  {#if rec}<p class="hint">Recommended: {rec.note}</p>{/if}
  {#snippet methods(legend: string, list: Method[])}
    <fieldset class="stack">
      <legend>{legend}</legend>
      {#each list as a (a.id)}
        <label class="choice" class:disabled={!a.ok}>
          <input type="radio" name="algorithm" value={a.id} bind:group={algorithm} disabled={!a.ok} />
          <span><strong>{a.label}</strong>{#if rec?.algorithm === a.id} <wa-badge variant="success" pill>Recommended</wa-badge>{/if}<br /><small>{a.ok ? a.help : unavailable(a.id)}</small></span>
        </label>
      {/each}
    </fieldset>
  {/snippet}
  {@render methods('Areas: map buildings and points', areaMethods)}
  {#if routesAllowed}{@render methods('Routes: capture street-level imagery', routeMethods)}{/if}

  {#if algorithm === 'DIVIDE_BY_SQUARE'}
    <wa-input label="Square size (metres)" type="number" min="10" max="100000" step="10" value={String(cellSize)} oninput={(e: Event) => (cellSize = Number((e.currentTarget as HTMLInputElement).value))}></wa-input>
  {:else if algorithm === 'SPLIT_BY_ROADS'}
    <wa-checkbox checked={mainRoadsOnly} onchange={(e: Event) => (mainRoadsOnly = (e.currentTarget as HTMLInputElement).checked)}>Main roads only</wa-checkbox>
    <p class="hint">Ignores residential and other minor streets, for bigger blocks.</p>
  {:else if byRoutes}
    <wa-input label="Target street length per task (km)" hint="About 0.5 km is 10 minutes on foot. Some tasks run longer to include short side streets, and mappers may retrace streets to get between them." type="number" min="0.1" max="100" step="0.1" value={String(routeKm)} oninput={(e: Event) => (routeKm = Number((e.currentTarget as HTMLInputElement).value))}></wa-input>
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
  {#if byFeatures && noRoads}
    <wa-callout variant="warning" size="s">
      The area is too large to fetch roads from OpenStreetMap, so task edges won't follow streets,
      rivers or railways. Upload your own roads in step 2.
    </wa-callout>
  {/if}
  {#if estimate}
    <p class:warn={estimate > MAX_TASKS}>About {estimate} tasks{estimate > MAX_TASKS ? ' - consider larger tasks' : ''}.</p>
  {/if}

  {#if data.polys.length && !byRoutes && !(byFeatures && byCount)}
    <wa-checkbox checked={dropEmpty} onchange={(e: Event) => (dropEmpty = (e.currentTarget as HTMLInputElement).checked)}>Remove tasks with nothing to map</wa-checkbox>
    <p class="hint">Untick to keep them, e.g. if mappers should add missing features there.</p>
  {/if}
  {#if selectedAreas}
    <wa-checkbox checked={onlySelected} onchange={(e: Event) => (onlySelected = (e.currentTarget as HTMLInputElement).checked)}>Only re-split the {selectedAreas} selected area task(s)</wa-checkbox>
  {/if}
  <div>
    <wa-button class="cta" variant="brand" onclick={go} disabled={!!planner.busy} loading={!!planner.busy}>
      {planner.tasks.length ? 'Split again' : 'Split'}
    </wa-button>
  </div>
  {#if planner.tasks.length && !onlySelected}<p class="hint">Splitting again replaces all tasks. You can undo.</p>{/if}
  {#if planner.osmRoadsArea}
    <p class="hint">
      Road data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>, via the <a href="https://postpass.geofabrik.de" target="_blank" rel="noopener">PostPass API</a>.
    </p>
  {/if}
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
