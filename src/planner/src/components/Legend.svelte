<script lang="ts">
  import { legend } from '../lib/colours';
  import type { Task } from '../lib/taskPlan';

  let { tasks }: { tasks: Task[] } = $props();
  const items = $derived(legend(tasks));
</script>

{#if items.length}
  <ul class="legend" aria-label="Task groups">
    {#each items as item (item.group)}
      <li><span class="swatch" style:background={item.colour}></span>{item.group || 'Unassigned'} ({item.count})</li>
    {/each}
  </ul>
{/if}

<style>
  .legend {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 0.75rem;
    font-size: 0.85rem;
  }
  .swatch {
    display: inline-block;
    width: 0.9rem;
    height: 0.9rem;
    border-radius: 2px;
    margin-right: 0.3rem;
    vertical-align: -0.1rem;
    opacity: 0.8;
  }
</style>
