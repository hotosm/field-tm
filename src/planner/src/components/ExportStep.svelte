<script lang="ts">
  import type { Planner } from '../lib/planner.svelte';
  import { planGeoJSON } from '../lib/exports';
  import { download } from '../lib/io/files';
  import { ApiError, loginUrl, projectUrl, saveTaskPlan } from '../lib/io/fieldtm';

  let { planner, project, returnTo }: { planner: Planner; project?: { id: number | string; name: string }; returnTo?: string } = $props();

  let saved = $state<number | null>(null);
  let authError = $state(false);
  let downloaded = $state(false);

  function downloadPlan() {
    planner.run('Preparing download', async () => {
      download(`${project ? `project-${project.id}-` : ''}task-plan.geojson`, planGeoJSON(planner.plan));
      planner.unsaved = false;
      downloaded = true;
    });
  }

  async function save() {
    if (!project) return;
    saved = null;
    authError = false;
    const res = await planner.run('Saving to Field-TM', async () => {
      try {
        return await saveTaskPlan(project.id, planner.plan);
      } catch (e) {
        if (e instanceof ApiError && e.isAuth) authError = true;
        throw e;
      }
    });
    if (res) {
      saved = res.task_count;
      planner.unsaved = false;
    }
  }
</script>

{#if !planner.tasks.length}
  <p>Split the area first.</p>
{:else}
  <p>{planner.tasks.length} tasks.</p>
  {#if project}
    <div><wa-button class="cta" variant="brand" onclick={save} disabled={!!planner.busy}>Save to Field-TM</wa-button></div>
    {#if saved != null}
      <wa-callout variant="success" size="s" role="status">Saved {saved} tasks. <a href={projectUrl(project.id)} target="_top">Return to project</a></wa-callout>
    {/if}
    {#if authError}
      <wa-callout variant="warning" size="s"><a href={loginUrl(location.pathname + location.search)} target="_top">Log in to Field-TM</a>, then save again. Your work is kept in this browser.</wa-callout>
    {/if}
  {/if}
  {#if !project}
    <wa-callout variant="brand" size="s">
      <strong>To use this in Field-TM:</strong> create a project for the same area, then upload this file
      in the Tasks section of the project page ("Or upload a task plan file"). Or open the task planner
      from the project, import this file in step 1, and save.
    </wa-callout>
  {/if}
  <div>
    <wa-button class={project ? '' : 'cta'} variant={project ? 'neutral' : 'brand'} appearance={project ? 'outlined' : 'accent'} onclick={downloadPlan}>Download task plan (GeoJSON)</wa-button>
    <p class="hint">Keep the file as a backup: you can import it again in step 1 to keep editing.</p>
  </div>
  {#if returnTo && !project}
    <div>
      <wa-button variant="brand" appearance={downloaded ? 'accent' : 'outlined'} href={returnTo} target="_top">Return to Field-TM project</wa-button>
      {#if !downloaded}<p class="hint">Download the task plan first, so you have the file to upload.</p>{/if}
    </div>
  {/if}
  <p class="hint">
    The task plan is a GeoJSON file with one polygon per task and the assignments. Select a task to download it as GPX or
    GeoJSON, or to share a link and QR code.
  </p>
  {#if planner.unsaved}
    <p class="hint">
      Drafts are kept in this browser only{planner.draftSavedAt ? ` (last saved ${planner.draftSavedAt})` : ''}.
      {project ? 'Save to Field-TM' : 'Download the task plan'} to keep your work.
    </p>
  {/if}
{/if}
