<script lang="ts">
  import type { Area } from '../lib/geo';
  import { aoiGeoJSON, aoiGPX } from '../lib/exports';
  import { download } from '../lib/io/files';
  import ActionGrid from './ActionGrid.svelte';

  let { aoi }: { aoi: Area } = $props();

  const geojson = () => download('area.geojson', aoiGeoJSON(aoi));
  const gpx = () => download('area.gpx', aoiGPX(aoi), 'application/gpx+xml');
</script>

<ActionGrid>
  <wa-button size="s" appearance="outlined" onclick={geojson} title="GeoJSON for QGIS, JOSM or other tools">GeoJSON</wa-button>
  <wa-button size="s" appearance="outlined" onclick={gpx} title="GPX outline for OsmAnd, CoMaps, Organic Maps or a GPS">GPX</wa-button>
</ActionGrid>
