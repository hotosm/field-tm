<script lang="ts">
  import type { LineString, Polygon } from 'geojson';
  import type { Map } from 'maplibre-gl';
  import MapView, { type Tool } from './components/MapView.svelte';
  import AreaStep from './components/AreaStep.svelte';
  import DataStep from './components/DataStep.svelte';
  import SplitStep from './components/SplitStep.svelte';
  import TasksStep from './components/TasksStep.svelte';
  import ExportStep from './components/ExportStep.svelte';
  import TaskDetails from './components/TaskDetails.svelte';
  import Legend from './components/Legend.svelte';
  import { Planner } from './lib/planner.svelte';
  import { parseMode } from './lib/urlParams';
  import { clearDraft, loadDraft, type Draft } from './lib/draft';
  import { toArea, toFeatureCollection } from './lib/geo';
  import { fetchJson } from './lib/io/files';
  import { ApiError, getPlannerInput, loginUrl, projectUrl } from './lib/io/fieldtm';
  import { parse, type Task } from './lib/taskPlan';

  const mode = parseMode(location.search, location.hash);
  const readonly = mode.kind === 'task' || (mode.kind === 'fieldtm' && mode.view);
  const planner = new Planner(mode.kind === 'fieldtm' ? `project-${mode.project}` : 'standalone');

  const STEPS = ['Area', 'Data', 'Split', 'Tasks', mode.kind === 'fieldtm' ? 'Save' : 'Export'] as const;
  let step = $state(0);
  let tool = $state<Tool>('none');
  let multi = $state(false);
  let map = $state.raw<Map>();
  let project = $state<{ id: number; name: string } | null>(null);
  let fatal = $state<{ message: string; login?: boolean } | null>(null);
  let draft = $state.raw<Draft | null>(null);
  let pendingEdit = $state.raw<Polygon | null>(null);

  const viewed = $derived(planner.selectedTasks.length === 1 ? planner.selectedTasks[0] : undefined);
  const editing = $derived(
    tool !== 'edit' ? null : step === 0 ? planner.aoi : (planner.selectedTasks[0]?.geometry ?? null),
  );

  async function init() {
    try {
      if (mode.kind === 'task') {
        planner.load({ plan: { type: 'FeatureCollection', task_plan_version: 1, algorithm: 'MANUAL', params: {}, features: [mode.task] } });
        planner.selected = [mode.task.properties.task_id];
      } else if (mode.kind === 'fieldtm') {
        const input = await getPlannerInput(mode.project);
        project = input.project;
        document.title = `${input.project.name} · Task Planner`;
        const plan = input.task_plan?.features.length ? parse(input.task_plan) : null;
        planner.load({ aoi: toArea(input.aoi), features: input.features, plan });
        if (plan) step = 3;
        if (!mode.view) offerDraft();
      } else {
        const get = async (url?: string) => (url ? toFeatureCollection(await fetchJson(url)) : null);
        if (mode.aoi || mode.features || mode.roads) {
          const [aoi, features, roads] = await Promise.all([get(mode.aoi), get(mode.features), get(mode.roads)]);
          planner.load({ aoi: aoi ? toArea(aoi) : null, features, roads });
          step = aoi ? 2 : 0;
        }
        offerDraft();
      }
    } catch (e) {
      const login = e instanceof ApiError && e.isAuth;
      fatal = { message: e instanceof Error ? e.message : String(e), login };
    }
  }

  function offerDraft() {
    const d = loadDraft(planner.scope);
    if (d && (d.plan?.features.length || d.aoi)) draft = d;
  }

  function restoreDraft() {
    if (!draft) return;
    const plan = draft.plan ? parse(draft.plan) : null;
    planner.load({ ...draft, features: draft.features ?? planner.features, roads: draft.roads ?? planner.roads, plan });
    planner.unsaved = true;
    step = plan ? 3 : draft.aoi ? 2 : 0;
    draft = null;
  }

  function discardDraft() {
    clearDraft(planner.scope);
    draft = null;
  }

  function onselect(id: number | null, additive: boolean) {
    if (readonly) {
      planner.selected = id == null ? [] : [id];
      return;
    }
    if (id == null) {
      if (!additive && !multi) planner.selected = [];
      return;
    }
    planner.toggleSelect(id, additive || multi);
    if (step < 2) step = 3;
  }

  function ondrawn(g: Polygon | LineString) {
    if (g.type === 'Polygon' && (tool === 'polygon' || tool === 'rectangle')) {
      planner.commit({ aoi: g, tasks: [] }, []);
    } else if (g.type === 'LineString' && tool === 'line') {
      planner.splitSelectedByLine(g);
    }
    tool = 'none';
  }

  function applyEdit() {
    if (pendingEdit) {
      if (step === 0) planner.commit({ aoi: pendingEdit, tasks: [] }, []);
      else if (planner.selected.length === 1) planner.updateGeometry(planner.selected[0], pendingEdit);
    }
    cancelTool();
  }

  function cancelTool() {
    tool = 'none';
    pendingEdit = null;
  }

  function onkeydown(e: KeyboardEvent) {
    if (readonly || (e.target as HTMLElement).closest('input, textarea, select')) return;
    if (e.key === 'Escape') cancelTool();
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      if (e.shiftKey) planner.redo();
      else planner.undo();
    }
  }

  function onbeforeunload(e: BeforeUnloadEvent) {
    if (!readonly && planner.unsaved && planner.tasks.length) e.preventDefault();
  }

  // Leaving a step cancels any drawing tool.
  $effect(() => {
    void step;
    cancelTool();
  });

  init();
</script>

<svelte:window {onkeydown} {onbeforeunload} />

{#snippet details(task: Task)}
  <TaskDetails {task} readonly />
{/snippet}

<div class="app" class:viewer={readonly}>
  {#if !readonly}
    <header class="topbar">
      <h1>Task Planner{#if project}<span class="project"> · {project.name}</span>{/if}</h1>
      <div class="row">
        {#if project}<a class="button" href={projectUrl(project.id)} target="_top">Back to project</a>{/if}
        <button type="button" onclick={() => planner.undo()} disabled={!planner.canUndo} title="Undo (Ctrl+Z)">Undo</button>
        <button type="button" onclick={() => planner.redo()} disabled={!planner.canRedo} title="Redo (Ctrl+Shift+Z)">Redo</button>
      </div>
    </header>
  {/if}

  <main>
    {#if !readonly}
      <aside class="panel">
        <nav aria-label="Steps">
          <ol class="steps">
            {#each STEPS as label, i (label)}
              <li><button type="button" aria-current={step === i ? 'step' : undefined} onclick={() => (step = i)}>{i + 1}. {label}</button></li>
            {/each}
          </ol>
        </nav>

        {#if draft}
          <div class="banner" role="status">
            <p>You have an unsaved draft from {new Date(draft.savedAt).toLocaleString()}.</p>
            <div class="row"><button type="button" class="primary" onclick={restoreDraft}>Restore</button><button type="button" onclick={discardDraft}>Discard</button></div>
          </div>
        {/if}
        {#if planner.error}
          <div class="banner error" role="alert">
            <p>{planner.error}</p>
            <button type="button" onclick={() => (planner.error = null)}>Dismiss</button>
          </div>
        {/if}
        {#if planner.busy}<p class="busy" role="status" aria-live="polite"><span class="spinner"></span>{planner.busy}…</p>{/if}

        <section class="step">
          <h2>{STEPS[step]}</h2>
          {#if step === 0}
            <AreaStep {planner} {map} bind:tool />
          {:else if step === 1}
            <DataStep {planner} />
          {:else if step === 2}
            <SplitStep {planner} ondone={() => (step = 3)} />
          {:else if step === 3}
            <TasksStep {planner} bind:tool bind:multi />
          {:else}
            <ExportStep {planner} project={project ?? undefined} />
          {/if}
        </section>
        <footer class="hint">
          <a href="https://github.com/hotosm/field-tm" target="_blank" rel="noopener">Field-TM</a> by HOT. Runs in your browser; nothing is uploaded unless you save to Field-TM.
        </footer>
      </aside>
    {/if}

    <div class="mapwrap">
      <MapView
        aoi={planner.aoi}
        tasks={planner.tasks}
        features={readonly ? null : planner.features}
        roads={readonly ? null : planner.roads}
        selected={planner.selected}
        {tool}
        {editing}
        fitKey={planner.fitKey}
        bind:map
        {onselect}
        {ondrawn}
        onedited={(g) => (pendingEdit = g)}
      />
      {#if tool === 'edit'}
        <div class="floating row">
          <span>Drag points to reshape. Click a point to delete it.</span>
          <button type="button" class="primary" onclick={applyEdit} disabled={!pendingEdit}>Apply</button>
          <button type="button" onclick={cancelTool}>Cancel</button>
        </div>
      {:else if tool !== 'none'}
        <div class="floating row"><button type="button" onclick={cancelTool}>Cancel drawing</button></div>
      {/if}
      {#if readonly}
        <div class="overlay">
          {#if mode.kind === 'task'}
            <p class="hint">Shared task. <a href={location.pathname}>Open the Task Planner</a></p>
          {:else if !planner.tasks.length && !fatal}
            <p>No tasks yet.</p>
          {/if}
          <Legend tasks={planner.tasks} />
          {#if viewed}{@render details(viewed)}{:else if planner.tasks.length}<p class="hint">Click a task for details and downloads.</p>{/if}
        </div>
      {/if}
    </div>
  </main>

  {#if fatal}
    <div class="modal" role="alertdialog" aria-labelledby="fatal-msg">
      <p id="fatal-msg">{fatal.message}</p>
      {#if fatal.login}<a class="button primary" href={loginUrl(location.pathname + location.search)} target="_top">Log in</a>{/if}
    </div>
  {/if}
</div>
