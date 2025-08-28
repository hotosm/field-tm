<script lang="ts">
	import '$styles/more.css';
	import Editor from '$lib/components/editor/editor.svelte';
	import Comment from '$lib/components/more/comment.svelte';
	import Activities from '$lib/components/more/activities.svelte';
	import ProjectInfo from '$lib/components/more/project-info.svelte';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import type { APIProject, TaskEventType } from '$lib/types';
	import { m } from '$translations/messages.js';

	type stackType = '' | 'comment' | 'instructions' | 'activities' | 'project-info';

	type stackGroupType = {
		id: stackType;
		icon: string;
		title: string;
	};

	type Props = {
		projectData: APIProject;
		zoomToTask: (taskId: number) => void;
	};

	let { projectData, zoomToTask }: Props = $props();
	const taskStore = getTaskStore();

	const stackGroup: stackGroupType[] = [
		{
			id: 'project-info',
			icon: 'info-circle',
			title: m['stack_group.project_information'](),
		},
		{
			id: 'comment',
			icon: 'chat',
			title: m['stack_group.comment'](),
		},
		{
			id: 'instructions',
			icon: 'description',
			title: m['stack_group.instructions'](),
		},
		{
			id: 'activities',
			icon: 'list-ul',
			title: m['stack_group.activities'](),
		},
	];

	let activeStack: stackType = $state('');
	let activeStackTitle: string = $state('');
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

<div class={`more ${activeStack === 'comment' ? 'more-comment' : 'more-no-comment'}`}>
	{#if activeStack === ''}
		{#each stackGroup as stack}
			<div
				class="stack"
				onclick={() => {
					activeStack = stack.id;
					activeStackTitle = stack.title;
				}}
				onkeydown={(e) => {
					if (e.key === 'Enter') {
						activeStack = stack.id;
						activeStackTitle = stack.title;
					}
				}}
				tabindex="0"
				role="button"
			>
				<div class="icon-title">
					<sl-icon name={stack.icon} class="icon"></sl-icon>
					<p>{stack.title}</p>
				</div>
				<sl-icon name="chevron-right" class="icon-next"></sl-icon>
			</div>
		{/each}
	{/if}

	<!-- header -->
	{#if activeStack !== ''}
		<div class="active-stack-header">
			<sl-icon
				name="chevron-left"
				class="icon"
				onclick={() => {
					activeStack = '';
					activeStackTitle = '';
				}}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						activeStack = '';
						activeStackTitle = '';
					}
				}}
				tabindex="0"
				role="button"
			></sl-icon>
			<p class="title">{activeStackTitle}</p>
		</div>
	{/if}

	<!-- body -->
	{#if activeStack === 'comment'}
		<Comment {comments} projectId={projectData?.id} projectStatus={projectData.status} />
	{/if}
	{#if activeStack === 'instructions'}
		{#if projectData?.per_task_instructions}
			<Editor editable={false} content={projectData?.per_task_instructions} />
		{:else}
			<div class="active-stack-instructions">
				<p>{m['index.no_instructions']()}</p>
			</div>
		{/if}
	{/if}
	{#if activeStack === 'activities'}
		<Activities {taskEvents} {zoomToTask} />
	{/if}
	{#if activeStack === 'project-info'}<ProjectInfo {projectData} />{/if}
</div>
