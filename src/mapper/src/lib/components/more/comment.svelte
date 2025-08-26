<script lang="ts">
	import '$styles/comment.css';
	import Editor from '$lib/components/editor/editor.svelte';
	import { commentTask } from '$lib/db/events';
	import type { TaskEventType } from '$lib/types';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { m } from '$translations/messages.js';
	import { projectStatus as projectStatusType } from '$constants/enums';

	interface Props {
		comments: TaskEventType[];
		projectId: any;
		projectStatus: projectStatusType;
	}

	const { comments, projectId, projectStatus }: Props = $props();

	let currentComment: string = $state('');
	let editorRef: any = $state(undefined);

	const taskStore = getTaskStore();
</script>

<div class="comments">
	<div class={`comments-content ${taskStore.selectedTaskIndex ? 'selected' : 'not-selected'}`}>
		{#if comments?.length === 0}
			<div class="no-comments">
				<p>
					{taskStore?.selectedTaskIndex
						? `${m['comment.no_comments_yet_on_task']()} ${taskStore?.selectedTaskIndex}`
						: m['comment.no_comments_yet']()}
				</p>
			</div>
		{:else}
			{#each comments as comment (comment?.event_id)}
				<div class="comment">
					<div class="wrapper">
						<sl-icon name="person-fill" class="icon"></sl-icon>
						<div class="details">
							<p class="username">{comment?.username}</p>
							<div class="meta">
								<p class="task-id">#{comment?.task_id}</p>
								<div class="history">
									<sl-icon name="clock-history" class="icon"></sl-icon>
									<p class="created-at">
										<span>
											{comment?.created_at?.split(' ')[0]}
										</span>
										<span>
											{comment?.created_at?.split(' ')[1]?.split('.')[0]}
										</span>
									</p>
								</div>
							</div>
						</div>
					</div>
					<Editor editable={false} content={comment?.comment as string} />
				</div>
			{/each}
		{/if}
	</div>
	{#if taskStore.selectedTaskId && projectStatus === projectStatusType.PUBLISHED}
		<div class="add-comment">
			<Editor
				editable={true}
				content=""
				setEditorHtmlContent={(editorText: string) => {
					currentComment = editorText;
				}}
				setEditorRef={(editor) => {
					editorRef = editor;
				}}
			/>
			<div class="wrapper">
				<sl-button
					onclick={() => {
						editorRef?.commands.clearContent(true);
					}}
					onkeydown={() => {}}
					role="button"
					tabindex="0"
					variant="default"
					size="small"
					class="button-clear"
				>
					<span>{m['comment.clear']()}</span>
				</sl-button>
				<sl-button
					variant="primary"
					size="small"
					class="button-comment"
					onclick={() => {
						if (taskStore.selectedTaskId) commentTask(projectId, taskStore.selectedTaskId, currentComment);
						editorRef?.commands.clearContent(true);
					}}
					onkeydown={() => {}}
					role="button"
					tabindex="0"><span>{m['comment.comment']()}</span></sl-button
				>
			</div>
		</div>
	{/if}
</div>
