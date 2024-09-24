<script lang="ts">
  import '@hotosm/ui/dist/hotosm-ui';
  import { createEventDispatcher } from 'svelte';
  import type { Task_history } from '$lib/migrations';

  export let record: Task_history;
  export let highlight: boolean;

  const dispatch = createEventDispatcher();

  // Style for highlighted task
  const highlightedStyle = highlight ? 'bg-[var(--hot-secondary-light)]' : '';

  // Dispatch zoomToTask event
  function handleZoomToTask() {
    dispatch('zoomToTask', { taskId: record.task_id });
  }

  // Format date utility function
  function formatDate(dateString: string) {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return { date: 'Invalid date', time: '' };
    }
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
  }
</script>

<sl-card class={`flex gap-2 items-center justify-between px-1 border-b-[2px] border-white py-3 ${highlightedStyle}`}>
  <!-- Profile Image or Default Icon -->
  <div class="flex items-center">
    <div class="w-[2.81rem] h-[2.81rem] border rounded-full overflow-hidden mr-4">
      {#if record?.profile_img}
        <img src={record.profile_img} alt="Profile Picture" />
      {:else}
        <div class="w-full h-full flex justify-center items-center bg-white">
          <sl-icon name="person" class="text-[30px] text-green-600"></sl-icon>
        </div>
      {/if}
    </div>

    <!-- Action Text and Task ID -->
    <div class="text-base">
      <span class="text-[#555555] font-medium font-archivo">
        {record?.action} by {record.action_text?.split(' ').at(-1)}
      </span>
      
      <!-- Date and Time -->
      <div class="flex items-center justify-between mt-2">
        <p class="font-archivo text-sm text-[#7A7676]">#{record?.task_id}</p>
        <div class="flex items-center font-archivo text-sm text-[#7A7676] ml-2">
          <sl-icon name="clock" class="text-[20px] mr-2"></sl-icon>
          {#if record?.action_date}
            {@const formattedDate = formatDate(record.action_date)}
            <span class="mr-2">{formattedDate.date}</span>
            <span>{formattedDate.time}</span>
          {:else}
            <span>No date available</span>
          {/if}
        </div>
      </div>
    </div>

    <!-- Zoom to Task Icon -->
    <div title="Zoom to Task" on:click={(e) => { e.stopPropagation(); handleZoomToTask() }}>
      <sl-icon name="map" class="text-[#9B9999] hover:text-[#555555] cursor-pointer text-[20px]"></sl-icon>
    </div>
  </div>
</sl-card>

<style>
  /* TODO replace with font for hotosm/ui shoelace css */
  @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@200;400;600&display=swap');
  
  .font-archivo {
    font-family: 'Archivo', sans-serif;
  }
</style>
