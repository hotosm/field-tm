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
    // Jump to Tasks to edit the clicked task; the Split step keeps its selection for re-splitting.
    if (step !== 2) step = 3;
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

  // Undoing a split leaves Tasks empty: go back to Split to try again.
  function undo() {
    planner.undo();
    if (step === 3 && !planner.tasks.length) step = planner.aoi ? 2 : 0;
  }

  function onkeydown(e: KeyboardEvent) {
    if (readonly || (e.target as HTMLElement).closest('input, textarea, select')) return;
    if (e.key === 'Escape') cancelTool();
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      if (e.shiftKey) planner.redo();
      else undo();
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

  type Tab = { label: string; href?: string; clickEvent: () => void };
  const go = (href: string) => () => window.top!.location.assign(href);
  const open = (href: string) => () => window.open(href, '_blank', 'noopener');
  const tabs = $derived<Tab[]>([
    ...(project
      ? [
          { label: 'Projects', clickEvent: go('/projects') },
          { label: project.name, clickEvent: go(projectUrl(project.id)) },
        ]
      : [{ label: 'Field-TM', clickEvent: open('https://field.hotosm.org') }]),
    { label: 'Task planner', href: location.pathname, clickEvent: () => {} },
    { label: 'Docs', clickEvent: open('https://docs.field.hotosm.org') },
    { label: 'Report a bug', clickEvent: open('https://roadmap.hotosm.org/#tech-request') },
  ]);

  init();
</script>

<svelte:window {onkeydown} {onbeforeunload} />

{#snippet details(task: Task)}
  <TaskDetails {task} readonly {map} title={project?.name} />
{/snippet}

<div class="app" class:viewer={readonly}>
  {#if !readonly}
    <hot-header title="Task Planner" logo="./field-tm-logo.svg" size="s" {tabs}>
      <div slot="auth"><hot-tool-menu></hot-tool-menu></div>
      <div slot="drawer-auth"><hot-tool-menu></hot-tool-menu></div>
    </hot-header>
  {/if}

  <main>
    {#if !readonly}
      <aside class="panel">
        <nav aria-label="Steps" class="steps">
            {#each STEPS as label, i (label)}
              <wa-button
                size="s"
                variant={step === i ? 'brand' : 'neutral'}
                appearance={step === i ? 'accent' : 'outlined'}
                aria-current={step === i ? 'step' : undefined}
                onclick={() => (step = i)}>{i + 1}. {label}</wa-button
              >
            {/each}
        </nav>
        <div class="row">
          <wa-button size="s" appearance="outlined" onclick={undo} disabled={!planner.canUndo} title="Undo (Ctrl+Z)">↶ Undo</wa-button>
          <wa-button size="s" appearance="outlined" onclick={() => planner.redo()} disabled={!planner.canRedo} title="Redo (Ctrl+Shift+Z)">↷ Redo</wa-button>
          {#if project}<wa-button size="s" appearance="plain" href={projectUrl(project.id)} target="_top">Back to project</wa-button>{/if}
          {#if mode.kind === 'standalone' && mode.returnTo}<wa-button size="s" appearance="plain" href={mode.returnTo} target="_top">Return to Field-TM project</wa-button>{/if}
        </div>

        {#if draft}
          <wa-callout variant="brand" role="status">
            <div class="stack">
              <p>You have an unsaved draft from {new Date(draft.savedAt).toLocaleString()}.</p>
              <div class="row">
                <wa-button size="s" variant="brand" onclick={restoreDraft}>Restore</wa-button>
                <wa-button size="s" appearance="outlined" onclick={discardDraft}>Discard</wa-button>
              </div>
            </div>
          </wa-callout>
        {/if}
        {#if planner.error}
          <wa-callout variant="danger" role="alert">
            <div class="stack">
              <p>{planner.error}</p>
              <div><wa-button size="s" appearance="outlined" onclick={() => (planner.error = null)}>Dismiss</wa-button></div>
            </div>
          </wa-callout>
        {/if}
        {#if planner.busy}<p class="row" role="status" aria-live="polite"><wa-spinner></wa-spinner>{planner.busy}…</p>{/if}

        <section class="step">
          <h2>{STEPS[step]}</h2>
          {#if step === 0}
            <AreaStep {planner} {map} bind:tool onplan={() => (step = 3)} />
          {:else if step === 1}
            <DataStep {planner} />
          {:else if step === 2}
            <SplitStep {planner} ondone={() => (step = 3)} />
          {:else if step === 3}
            <TasksStep {planner} bind:tool bind:multi {map} title={project?.name} onsplit={() => (step = 2)} />
          {:else}
            <ExportStep {planner} project={project ?? undefined} returnTo={mode.kind === 'standalone' ? mode.returnTo : undefined} />
          {/if}
        </section>
        <p class="hint">
          <a href="https://github.com/hotosm/field-tm" target="_blank" rel="noopener">Field-TM</a> by HOT. Everything remains in your browser, unless you save to Field-TM.
        </p>
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
          <wa-button size="s" variant="brand" onclick={applyEdit} disabled={!pendingEdit}>Apply</wa-button>
          <wa-button size="s" appearance="outlined" onclick={cancelTool}>Cancel</wa-button>
        </div>
      {:else if tool !== 'none'}
        <div class="floating row"><wa-button size="s" appearance="outlined" onclick={cancelTool}>Cancel drawing</wa-button></div>
      {/if}
      {#if readonly}
        <div class="overlay stack">
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

  <wa-dialog open={!!fatal} label="Something went wrong" onwa-hide={(e: Event) => e.preventDefault()}>
    <p>{fatal?.message}</p>
    {#if fatal?.login}<wa-button slot="footer" variant="brand" href={loginUrl(location.pathname + location.search)} target="_top">Log in</wa-button>{/if}
  </wa-dialog>
</div>
