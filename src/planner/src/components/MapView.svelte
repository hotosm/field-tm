<script lang="ts">
  import { untrack, type Snippet } from 'svelte';
  import type { FeatureCollection, Geometry, LineString, Polygon, Position } from 'geojson';
  import type { LngLatBoundsLike, Map, MapMouseEvent } from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { MapLibre, GeoJSONSource, FillLayer, LineLayer, SymbolLayer, Popup, NavigationControl, ScaleControl, GeolocateControl } from 'svelte-maplibre-gl';
  import { TerraDraw } from '@svelte-maplibre-gl/terradraw';
  import {
    TerraDraw as Draw,
    TerraDrawLineStringMode,
    TerraDrawPolygonMode,
    TerraDrawRectangleMode,
    TerraDrawSelectMode,
  } from 'terra-draw';
  import type { Area } from '../lib/geo';
  import { bbox } from '../lib/geo';
  import { taskColour } from '../lib/colours';
  import { addBlankImage, loadBasemap } from '../lib/basemap';
  import type { Task } from '../lib/taskPlan';

  export type Tool = 'none' | 'polygon' | 'rectangle' | 'line' | 'edit';

  interface Props {
    aoi?: Area | null;
    tasks?: Task[];
    features?: FeatureCollection | null;
    roads?: FeatureCollection | null;
    selected?: number[];
    tool?: Tool;
    /** Geometry loaded into the vertex editor when tool is 'edit'. */
    editing?: Polygon | Area | null;
    fitKey?: number;
    map?: Map;
    onselect?: (id: number | null, additive: boolean) => void;
    ondrawn?: (g: Polygon | LineString) => void;
    onedited?: (g: Polygon) => void;
    /** Popup anchored on the map; `key` remounts it when the subject changes. */
    popup?: { key: number; at: Position; content: Snippet } | null;
  }

  let {
    aoi = null, tasks = [], features = null, roads = null, selected = [], tool = 'none', editing = null,
    fitKey = 0, map = $bindable(), onselect, ondrawn, onedited, popup = null,
  }: Props = $props();

  const HOT_RED = '#d63f3f';
  const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] };

  const modes = [
    new TerraDrawPolygonMode({ styles: { fillColor: HOT_RED, outlineColor: HOT_RED, fillOpacity: 0.15 } }),
    new TerraDrawRectangleMode({ styles: { fillColor: HOT_RED, outlineColor: HOT_RED, fillOpacity: 0.15 } }),
    new TerraDrawLineStringMode({ styles: { lineStringColor: '#111111', lineStringWidth: 3 } }),
    new TerraDrawSelectMode({
      flags: {
        polygon: { feature: { draggable: false, coordinates: { draggable: true, midpoints: true, deletable: true } } },
      },
      styles: { selectedPolygonColor: HOT_RED, selectedPolygonOutlineColor: HOT_RED, selectionPointColor: HOT_RED, midPointColor: '#ffffff' },
    }),
  ];
  const MODE: Record<Tool, string> = { none: 'static', polygon: 'polygon', rectangle: 'rectangle', line: 'linestring', edit: 'select' };

  let draw = $state.raw<Draw>();

  const taskData = $derived<FeatureCollection>({
    type: 'FeatureCollection',
    features: tasks.map((t) => ({
      ...t,
      id: t.properties.task_id,
      properties: { ...t.properties, _colour: taskColour(t), _selected: selected.includes(t.properties.task_id) },
    })),
  });
  const aoiData = $derived<FeatureCollection>(aoi ? { type: 'FeatureCollection', features: [{ type: 'Feature', geometry: aoi, properties: {} }] } : EMPTY);

  const round = (g: Polygon): Polygon => ({
    type: 'Polygon',
    coordinates: g.coordinates.map((r) => r.map(([x, y]) => [Math.round(x * 1e7) / 1e7, Math.round(y * 1e7) / 1e7])),
  });

  // Load the geometry being edited into Terra Draw.
  $effect(() => {
    if (!draw) return;
    draw.clear();
    if (tool !== 'edit' || editing?.type !== 'Polygon') return;
    const id = draw.getFeatureId();
    const [res] = draw.addFeatures([{ id, type: 'Feature', geometry: round(editing), properties: { mode: 'polygon' } }]);
    if (res?.valid) draw.selectFeature(id);
    else console.warn('Cannot edit this shape:', res?.reason);
  });

  function onfinish(id: string | number, ctx: { action: string }) {
    if (!draw) return;
    const f = draw.getSnapshotFeature(id);
    if (!f) return;
    if (ctx.action === 'draw') {
      ondrawn?.(f.geometry as Polygon | LineString);
      draw.removeFeatures([id]);
    }
  }

  function onchange(ids: (string | number)[], type: string) {
    if (tool !== 'edit' || type !== 'update' || !draw) return;
    const g = draw.getSnapshotFeature(ids[0])?.geometry;
    if (g?.type === 'Polygon') onedited?.(g as Polygon);
  }

  function fit(geoms: Geometry[]) {
    if (!map || !geoms.length) return;
    map.fitBounds(bbox(geoms) as LngLatBoundsLike, { padding: 40, maxZoom: 17, duration: 0 });
  }

  $effect(() => {
    void fitKey;
    if (!map) return;
    untrack(() => fit(aoi ? [aoi] : tasks.map((t) => t.geometry)));
  });

  function onclick(e: MapMouseEvent) {
    if (tool !== 'none' || !map) return;
    const hit = map.getLayer('tasks-fill') ? map.queryRenderedFeatures(e.point, { layers: ['tasks-fill'] })[0] : undefined;
    const ev = e.originalEvent;
    onselect?.(hit ? Number(hit.properties.task_id) : null, ev.shiftKey || ev.ctrlKey || ev.metaKey);
  }

  const basemap = loadBasemap();
</script>

{#await basemap then style}
<MapLibre
  bind:map
  class="map"
  {style}
  onstyleimagemissing={(e) => map && addBlankImage(map, e.id)}
  center={[0, 20]}
  zoom={1.5}
  autoloadGlobalCss={false}
  cursor={tool === 'none' ? undefined : 'crosshair'}
  {onclick}
>
  <NavigationControl position="top-right" />
  <GeolocateControl position="top-right" />
  <ScaleControl position="bottom-left" />

  <GeoJSONSource id="features" data={features ?? EMPTY}>
    <FillLayer id="features-fill" filter={['==', ['geometry-type'], 'Polygon']} paint={{ 'fill-color': '#555', 'fill-opacity': 0.35 }} />
  </GeoJSONSource>
  <GeoJSONSource id="roads" data={roads ?? EMPTY}>
    <LineLayer id="roads-line" paint={{ 'line-color': '#333', 'line-width': 2, 'line-opacity': 0.6 }} />
  </GeoJSONSource>
  <GeoJSONSource id="aoi" data={aoiData}>
    <LineLayer id="aoi-line" paint={{ 'line-color': HOT_RED, 'line-width': 3, 'line-dasharray': [2, 1] }} />
  </GeoJSONSource>
  <GeoJSONSource id="tasks" data={taskData}>
    <FillLayer
      id="tasks-fill"
      paint={{ 'fill-color': ['get', '_colour'], 'fill-opacity': ['case', ['get', '_selected'], 0.55, 0.25] }}
    />
    <LineLayer
      id="tasks-line"
      paint={{
        'line-color': ['case', ['get', '_selected'], '#111', ['get', '_colour']],
        'line-width': ['case', ['get', '_selected'], 3, 1.5],
      }}
    />
    <SymbolLayer
      id="tasks-label"
      layout={{ 'text-field': ['to-string', ['get', 'task_id']], 'text-font': ['Noto Sans Bold'], 'text-size': 13 }}
      paint={{ 'text-color': '#111', 'text-halo-color': '#fff', 'text-halo-width': 1.5 }}
    />
  </GeoJSONSource>

  {#if popup}
    {#key popup.key}
      <Popup lnglat={popup.at as [number, number]} class="task-popup" maxWidth="16rem" closeButton={false} closeOnClick={false}>
        {@render popup.content()}
      </Popup>
    {/key}
  {/if}

  <TerraDraw mode={MODE[tool]} {modes} bind:draw {onfinish} {onchange} />
</MapLibre>
{/await}
