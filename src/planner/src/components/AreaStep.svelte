<script lang="ts">
  import type { Map } from 'maplibre-gl';
  import type { Planner } from '../lib/planner.svelte';
  import type { Tool } from './MapView.svelte';
  import { areaM2, squareAround, toArea } from '../lib/geo';
  import { readJsonFile } from '../lib/io/files';
  import { isTaskPlan, parse } from '../lib/taskPlan';

  let { planner, map, tool = $bindable(), onplan }: { planner: Planner; map?: Map; tool: Tool; onplan?: () => void } = $props();

  let size = $state(1000);
  let fileInput = $state<HTMLInputElement>();
  let planInput = $state<HTMLInputElement>();
  const km2 = $derived(planner.aoi ? areaM2(planner.aoi) / 1e6 : 0);

  function importPlan(json: unknown) {
    const plan = parse(json);
    planner.load({ aoi: toArea(plan), plan, features: planner.features, roads: planner.roads });
    planner.unsaved = true;
    onplan?.();
  }

  /** An area file, or a task plan (detected) to keep editing. */
  async function upload(e: Event, asPlan: boolean) {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    await planner.run('Reading file', async () => {
      const json = await readJsonFile(file);
      if (asPlan || isTaskPlan(json)) return importPlan(json);
      planner.commit({ aoi: toArea(json), tasks: [] }, []);
      planner.fitKey++;
    });
  }

  function square() {
    const c = map?.getCenter();
    if (!c) return;
    planner.commit({ aoi: squareAround([c.lng, c.lat], size), tasks: [] }, []);
    planner.fitKey++;
  }
</script>

<p>Draw the area to map, upload it, or start with a square around the map centre.</p>
<div class="row">
  <wa-button size="s" variant={tool === 'polygon' ? 'brand' : 'neutral'} appearance={tool === 'polygon' ? 'accent' : 'outlined'} onclick={() => (tool = tool === 'polygon' ? 'none' : 'polygon')}>Draw polygon</wa-button>
  <wa-button size="s" variant={tool === 'rectangle' ? 'brand' : 'neutral'} appearance={tool === 'rectangle' ? 'accent' : 'outlined'} onclick={() => (tool = tool === 'rectangle' ? 'none' : 'rectangle')}>Draw rectangle</wa-button>
  <wa-button size="s" appearance="outlined" onclick={() => fileInput?.click()}>Upload area</wa-button>
  <input bind:this={fileInput} type="file" accept=".geojson,.json,application/geo+json,application/json" onchange={(e) => upload(e, false)} hidden />
</div>
{#if tool === 'polygon'}<p class="hint">Click to add points; click the first point to finish.</p>{/if}
{#if tool === 'rectangle'}<p class="hint">Click two opposite corners.</p>{/if}
<div class="row">
  <wa-button size="s" appearance="outlined" onclick={square}>Square around map centre</wa-button>
  <wa-select size="s" value={String(size)} onchange={(e: Event) => (size = Number((e.currentTarget as HTMLSelectElement).value))} aria-label="Square size" style="width: 7rem">
    <wa-option value="500">500 m</wa-option>
    <wa-option value="1000">1 km</wa-option>
    <wa-option value="2000">2 km</wa-option>
    <wa-option value="5000">5 km</wa-option>
  </wa-select>
</div>

<h3>Or continue a task plan</h3>
<p class="hint">
  Import a task plan you downloaded earlier (e.g. a backup) to edit it and
  download it again. Its tasks, teams and comments are kept.
</p>
<div class="row">
  <wa-button size="s" appearance="outlined" onclick={() => planInput?.click()}>Import task plan</wa-button>
  <input bind:this={planInput} type="file" accept=".geojson,.json,application/geo+json,application/json" onchange={(e) => upload(e, true)} hidden />
</div>

{#if planner.aoi}
  <p><strong>Area:</strong> {km2 < 1 ? `${Math.round(km2 * 100) / 100}` : Math.round(km2 * 10) / 10} km²</p>
  <div class="row">
    <wa-button size="s" appearance="outlined" disabled={planner.aoi.type !== 'Polygon'} onclick={() => (tool = 'edit')}>Edit shape</wa-button>
    <wa-button size="s" variant="danger" appearance="outlined" onclick={() => planner.commit({ aoi: null, tasks: [] }, [])}>Clear area</wa-button>
  </div>
{/if}
