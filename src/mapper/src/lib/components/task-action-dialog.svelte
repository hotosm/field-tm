<script lang="ts">
    import { mapTask, finishTask, resetTask } from '$lib/db/events';
    interface Props {
        state: string;
        projectId: number;
        taskId: number;
    }

    let { state, projectId, taskId }: Props = $props();

    const actions = {
        UNLOCKED_TO_MAP: { label: 'MAP', color: 'green', icon: 'play', action: () => mapTask(projectId, taskId) },
        LOCKED_FOR_MAPPING: { label: 'FINISH', color: 'blue', icon: 'stop', action: () => finishTask(projectId, taskId) },
        UNLOCKED_TO_VALIDATE: { label: 'RESET', color: 'yellow', icon: 'arrow-counterclockwise', action: () => resetTask(projectId, taskId) },
    };
</script>

{#if actions[state]}
    <sl-tooltip content={actions[state].label}>
        <hot-icon-button
            name={actions[state].icon}
            class="fixed top-30 left-1/2 transform -translate-x-1/2 text-5xl z-10 bg-{actions[state].color}-500 text-white rounded-full p-1"
            label={actions[state].label}
            onclick={actions[state].action}
        ></hot-icon-button>
    </sl-tooltip>
{/if}
