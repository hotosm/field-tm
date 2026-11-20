<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { toFeatureCollection } from '../lib/geo';
  import { classify } from '../lib/engine/splitter';
  import { readJsonFile } from '../lib/io/files';

  let { planner, fromProject = false }: { planner: Planner; fromProject?: boolean } = $props();

  const featureCount = $derived(classify(planner.features).polys.length);
  let featuresInput = $state<HTMLInputElement>();
  let roadsInput = $state<HTMLInputElement>();

  async function upload(e: Event, kind: 'features' | 'roads') {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) await planner.run('Reading file', async () => planner.setData(kind, toFeatureCollection(await readJsonFile(file))));
  }
</script>

<p>
  Optional: the square grid and splitting by roads need no data. Roads, rivers and
  railways are fetched from OpenStreetMap when you split.
</p>

<h3>Features to map <small class="hint">(optional)</small></h3>
{#if fromProject}
  <p class="hint">
    These are the features your mappers will see, set in the Field-TM project setup. Change them
    there, then reopen the planner.
  </p>
  <p>
    {#if planner.features}<wa-badge variant="success">{featureCount} features</wa-badge>{:else}No features: the project starts with an empty map.{/if}
  </p>
{:else}
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
{/if}

<wa-details summary="Advanced: use your own roads" open={!!planner.roads && !planner.osmRoadsArea}>
  <p class="hint">
    Roads, rivers and railways only shape task edges; they are not mapped. They are fetched from
    OpenStreetMap for areas up to about 25 × 25 km. Upload your own lines (GeoJSON) for larger
    areas or to use a different dataset.
  </p>
  <div class="row">
    <wa-button size="s" appearance="outlined" onclick={() => roadsInput?.click()}>Upload roads</wa-button>
    <input bind:this={roadsInput} type="file" accept=".geojson,.json" onchange={(e) => upload(e, 'roads')} hidden />
    {#if planner.roads && !planner.osmRoadsArea}
      <wa-badge variant="success">{planner.roads.features.length} lines</wa-badge>
      <wa-button size="s" appearance="plain" onclick={() => planner.setData('roads', null)}>Remove</wa-button>
    {/if}
  </div>
</wa-details>
