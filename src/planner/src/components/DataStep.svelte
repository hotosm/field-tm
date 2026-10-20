<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { bbox, toFeatureCollection } from '../lib/geo';
  import { classify } from '../lib/engine/splitter';
  import { readJsonFile } from '../lib/io/files';
  import { fetchRoads } from '../lib/io/postpass';

  let { planner }: { planner: Planner } = $props();

  const MAX_BBOX_DEG2 = 0.05; // roughly 25 x 25 km near the equator
  const featureCount = $derived(classify(planner.features).polys.length);
  let featuresInput = $state<HTMLInputElement>();
  let roadsInput = $state<HTMLInputElement>();

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

<p>
  Both are optional: the square grid needs no data. Add data to unlock the other
  ways to split in the next step.
</p>

<h3>Features to map <small class="hint">(optional)</small></h3>
<p class="hint">
  Lets you split so each task has about the same number of features to map:
  buildings, points (e.g. water points, shops) or lines. Upload them as
  GeoJSON. Download them for your area from
  <a href="https://export.hotosm.org" target="_blank" rel="noopener">export.hotosm.org</a>.
</p>
<div class="row">
  <wa-button size="s" appearance="outlined" onclick={() => featuresInput?.click()}>Upload features</wa-button>
  <input bind:this={featuresInput} type="file" accept=".geojson,.json" onchange={(e) => upload(e, 'features')} hidden />
  {#if planner.features}
    <wa-badge variant="success">{featureCount} features</wa-badge>
    <wa-button size="s" appearance="plain" onclick={() => planner.setData('features', null)}>Remove</wa-button>
  {/if}
</div>
<p class="hint"><strong>Enables splitting by number of features</strong>.</p>

<h3>Roads, rivers and railways <small class="hint">(recommended)</small></h3>
<p class="hint">
  Used only to draw task edges, so mappers don't have to cross a main road,
  river or railway inside one task. They are not mapped.
</p>
<div class="row">
  <wa-button size="s" variant="brand" onclick={fetchOsm} disabled={!planner.aoi || !!planner.busy}>Get them from OpenStreetMap</wa-button>
  <wa-button size="s" appearance="outlined" onclick={() => roadsInput?.click()}>Upload a file</wa-button>
  <input bind:this={roadsInput} type="file" accept=".geojson,.json" onchange={(e) => upload(e, 'roads')} hidden />
  {#if planner.roads}
    <wa-badge variant="success">{planner.roads.features.length} lines</wa-badge>
    <wa-button size="s" appearance="plain" onclick={() => planner.setData('roads', null)}>Remove</wa-button>
  {/if}
</div>
{#if !planner.aoi}<p class="hint">Draw or upload the area in step 1 first.</p>{/if}
<p class="hint">
  Unlocks: <strong>By roads</strong>. Also makes feature-based tasks follow
  roads.
</p>
{#if planner.roads}
  <p class="hint">
    Road data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>, via the <a href="https://postpass.geofabrik.de" target="_blank" rel="noopener">PostPass API</a>.
  </p>
{/if}
