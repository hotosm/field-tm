<script lang="ts">
	import Editor from '$lib/components/editor/editor.svelte';
	import Comment from '$lib/components/more/comment.svelte';
	import Activities from '$lib/components/more/activities.svelte';
	import ProjectInfo from '$lib/components/more/project-info.svelte';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import type { ProjectData, TaskEventType } from '$lib/types';
	import { m } from "$translations/messages.js";

	type stackType = '' | 'Comment' | 'Instructions' | 'Activities' | 'Project Information';

	const stackGroup: { icon: string; title: stackType }[] = [
		{
			icon: 'info-circle',
			title: m['stack_group.project_information'](),
		},
		{
			icon: 'chat',
			title: m['stack_group.comment'](),
		},
		{
			icon: 'description',
			title: m['stack_group.instructions'](),
		},
		{
			icon: 'list-ul',
			title: m['stack_group.activities'](),
		},
	];

	type Props = {
		projectData: ProjectData;
		zoomToTask: (taskId: number) => void;
	};

	let { projectData, zoomToTask }: Props = $props();
	const taskStore = getTaskStore();

	let activeStack: stackType = $state('');
	let taskEvents: TaskEventType[] = $state([]);
	let comments: TaskEventType[] = $state([]);

	$effect(() => {
		if (!(taskStore?.events?.length > 0)) return;

		// if a task is selected, then apply filter to the events list
		if (taskStore?.selectedTaskId) {
			taskEvents = taskStore?.events?.filter(
				(event: TaskEventType) => event.event !== 'COMMENT' && event.task_id === taskStore?.selectedTaskId,
			);
			comments = taskStore?.events?.filter(
				(event: TaskEventType) =>
					event.event === 'COMMENT' &&
					event.task_id === taskStore?.selectedTaskId &&
					!event.comment?.includes('-SUBMISSION_INST-') &&
					!event.comment?.startsWith('#submissionId:uuid:'),
			);
		} else {
			taskEvents = taskStore?.events?.filter((event: TaskEventType) => event.event !== 'COMMENT');
			comments = taskStore?.events?.filter(
				(event: TaskEventType) =>
					event.event === 'COMMENT' &&
					event.task_id === taskStore?.selectedTaskId &&
					!event.comment?.includes('-SUBMISSION_INST-') &&
					!event.comment?.startsWith('#submissionId:uuid:'),
			);
		}
	});
</script>

<div class={`font-barlow font-medium ${activeStack === 'Comment' ? 'h-full' : 'h-fit'}`}>
	{#if activeStack === ''}
		{#each stackGroup as stack}
			<div
				class="group flex items-center justify-between hover:bg-red-50 rounded-md p-2 duration-200 cursor-pointer"
				onclick={() => (activeStack = stack.title)}
				onkeydown={(e) => {
					if (e.key === 'Enter') activeStack = stack.title;
				}}
				tabindex="0"
				role="button"
			>
				<div class="flex items-center gap-3">
					<hot-icon name={stack.icon} class="text-[1.25rem]"></hot-icon>
					<p>{stack.title}</p>
				</div>
				<hot-icon name="chevron-right" class="text-[1rem] group-hover:translate-x-1 duration-200"></hot-icon>
			</div>
		{/each}
	{/if}

	<!-- header -->
	{#if activeStack !== ''}
		<div class="flex items-center gap-x-2 sticky -top-1 bg-white pb-2 z-50">
			<hot-icon
				name="chevron-left"
				class="text-[1rem] hover:-translate-x-[2px] duration-200 cursor-pointer text-[1.125rem] text-black hover:text-red-600 duration-200"
				onclick={() => (activeStack = '')}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') activeStack = '';
				}}
				tabindex="0"
				role="button"
			></hot-icon>
			<p class="text-[1.125rem] font-semibold">{activeStack}</p>
		</div>
	{/if}

	<!-- body -->
	{#if activeStack === 'Comment'}
		<Comment {comments} projectId={projectData?.id} />
	{/if}
	{#if activeStack === 'Instructions'}
		{#if projectData?.per_task_instructions}
			<Editor editable={false} content={projectData?.per_task_instructions} />
		{:else}
			<div class="flex justify-center mt-10">
				<p class="text-[#484848] text-base">{m['index.no_instructions']()}</p>
			</div>
		{/if}
	{/if}
	{#if activeStack === 'Activities'}
		<Activities {taskEvents} {zoomToTask} />
	{/if}
	{#if activeStack === 'Project Information'}<ProjectInfo {projectData} />{/if}
</div>
