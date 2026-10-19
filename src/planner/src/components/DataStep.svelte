<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { bbox, countBuildings, toFeatureCollection } from '../lib/geo';
  import { readJsonFile } from '../lib/io/files';
  import { fetchRoads } from '../lib/io/overpass';

  let { planner }: { planner: Planner } = $props();

  const MAX_BBOX_DEG2 = 0.05; // roughly 25 x 25 km near the equator
  const buildings = $derived(countBuildings(planner.features));

  async function upload(e: Event, kind: 'features' | 'roads') {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) await planner.run('Reading file', async () => planner.setData(kind, toFeatureCollection(await readJsonFile(file))));
  }

  async function fetchOsm() {
    if (!planner.aoi) return;
    const b = bbox(planner.aoi);
    if ((b[2] - b[0]) * (b[3] - b[1]) > MAX_BBOX_DEG2) {
      planner.error = 'The area is too large to fetch roads from OSM. Upload a roads file instead.';
      return;
    }
    await planner.run('Fetching roads from OpenStreetMap', async () => planner.setData('roads', await fetchRoads(b)));
  }
</script>

<p>Optional. Data lets you split by buildings or roads.</p>

<h3>Features to map</h3>
<p class="hint">
  Buildings or other polygons as GeoJSON. Get OSM data for your area from
  <a href="https://export.hotosm.org" target="_blank" rel="noopener">export.hotosm.org</a>.
</p>
<div class="row wrap">
  <label class="button">Upload features<input type="file" accept=".geojson,.json" onchange={(e) => upload(e, 'features')} hidden /></label>
  {#if planner.features}
    <span>{buildings} polygons</span>
    <button type="button" onclick={() => planner.setData('features', null)}>Remove</button>
  {/if}
</div>

<h3>Roads</h3>
<p class="hint">Main roads, rivers and railways become task boundaries.</p>
<div class="row wrap">
  <label class="button">Upload roads<input type="file" accept=".geojson,.json" onchange={(e) => upload(e, 'roads')} hidden /></label>
  <button type="button" onclick={fetchOsm} disabled={!planner.aoi || !!planner.busy}>Fetch roads from OSM</button>
  {#if planner.roads}
    <span>{planner.roads.features.length} lines</span>
    <button type="button" onclick={() => planner.setData('roads', null)}>Remove</button>
  {/if}
</div>
{#if !planner.aoi}<p class="hint">Set the area first to fetch roads.</p>{/if}
<p class="hint">Road data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>, via the Overpass API.</p>
