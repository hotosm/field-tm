<script lang="ts">
  import type { Map } from 'maplibre-gl';
  import type { Planner } from '../lib/planner.svelte';
  import type { Tool } from './MapView.svelte';
  import { areaM2, squareAround, toArea } from '../lib/geo';
  import { readJsonFile } from '../lib/io/files';
  import { parse } from '../lib/taskPlan';

  let { planner, map, tool = $bindable() }: { planner: Planner; map?: Map; tool: Tool } = $props();

  let size = $state(1000);
  let fileInput = $state<HTMLInputElement>();
  const km2 = $derived(planner.aoi ? areaM2(planner.aoi) / 1e6 : 0);

  async function upload(e: Event) {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    await planner.run('Reading file', async () => {
      const json = (await readJsonFile(file)) as { task_plan_version?: number };
      if (json.task_plan_version) {
        const plan = parse(json);
        planner.load({ aoi: toArea(plan), plan, features: planner.features, roads: planner.roads });
      } else {
        planner.commit({ aoi: toArea(json), tasks: [] }, []);
        planner.fitKey++;
      }
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
  <wa-button size="small" variant={tool === 'polygon' ? 'brand' : 'neutral'} appearance={tool === 'polygon' ? 'accent' : 'outlined'} onclick={() => (tool = tool === 'polygon' ? 'none' : 'polygon')}>Draw polygon</wa-button>
  <wa-button size="small" variant={tool === 'rectangle' ? 'brand' : 'neutral'} appearance={tool === 'rectangle' ? 'accent' : 'outlined'} onclick={() => (tool = tool === 'rectangle' ? 'none' : 'rectangle')}>Draw rectangle</wa-button>
  <wa-button size="small" appearance="outlined" onclick={() => fileInput?.click()}>Upload GeoJSON</wa-button>
  <input bind:this={fileInput} type="file" accept=".geojson,.json,application/geo+json,application/json" onchange={upload} hidden />
</div>
{#if tool === 'polygon'}<p class="hint">Click to add points; click the first point to finish.</p>{/if}
{#if tool === 'rectangle'}<p class="hint">Click two opposite corners.</p>{/if}
<div class="row">
  <wa-button size="small" appearance="outlined" onclick={square}>Square around map centre</wa-button>
  <wa-select size="small" value={String(size)} onchange={(e: Event) => (size = Number((e.currentTarget as HTMLSelectElement).value))} aria-label="Square size" style="width: 7rem">
    <wa-option value="500">500 m</wa-option>
    <wa-option value="1000">1 km</wa-option>
    <wa-option value="2000">2 km</wa-option>
    <wa-option value="5000">5 km</wa-option>
  </wa-select>
</div>
<p class="hint">You can also upload a saved task plan to keep working on it.</p>

{#if planner.aoi}
  <p><strong>Area:</strong> {km2 < 1 ? `${Math.round(km2 * 100) / 100}` : Math.round(km2 * 10) / 10} km²</p>
  <div class="row">
    <wa-button size="small" appearance="outlined" disabled={planner.aoi.type !== 'Polygon'} onclick={() => (tool = 'edit')}>Edit shape</wa-button>
    <wa-button size="small" variant="danger" appearance="outlined" onclick={() => planner.commit({ aoi: null, tasks: [] }, [])}>Clear area</wa-button>
  </div>
{/if}
