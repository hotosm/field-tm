<script lang="ts">
	import Editor from '$lib/components/editor/editor.svelte';
	import { commentTask } from '$lib/db/events';
	import type { TaskEventType } from '$lib/types';
	import { getTaskStore } from '$store/tasks.svelte.ts';

	interface Props {
		comments: TaskEventType[];
		projectId: any;
	}

	const { comments, projectId }: Props = $props();

	let currentComment: string = $state('');
	let editorRef: any = $state(undefined);

	const taskStore = getTaskStore();
</script>

<div class="h-[calc(100%-2.25rem)] sm:h-[calc(100%-2.6rem)]">
	<div
		class={`overflow-y-scroll overflow-x-hidden flex flex-col gap-2 ${taskStore.selectedTaskIndex ? 'h-[calc(100%-11.875rem)]' : 'h-[100%]'}`}
	>
		{#if comments?.length === 0}
			<div class="flex justify-center mt-10">
				<p class="text-[#484848] text-base">
					{taskStore?.selectedTaskIndex ? `No comments yet on task ${taskStore?.selectedTaskIndex}` : 'No comments yet'}
				</p>
			</div>
		{:else}
			{#each comments as comment (comment?.event_id)}
				<div class="flex flex-col gap-2 py-3 bg-[#F6F5F5] rounded-md">
					<div class="flex gap-4 px-3">
						<hot-icon
							name="person-fill"
							class="!text-[1.7rem] text-red-600 cursor-pointer duration-200 rounded-full p-[2px] bg-white border-1 border-solid"
						></hot-icon>
						<div class="flex flex-col gap-1 flex-1">
							<p class="font-semibold capitalize">{comment?.username}</p>
							<div class="flex items-center justify-between">
								<p class="text-[#484848] text-sm">#{comment?.task_id}</p>
								<div class="flex items-center gap-2">
									<hot-icon name="clock-history" class="!text-[1rem] text-red-600 cursor-pointer duration-200"
									></hot-icon>
									<p class="text-[#484848] text-sm">
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
	{#if taskStore.selectedTaskId}
		<div class="mt-2">
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
			<div class="w-full flex justify-end my-2 gap-2">
				<sl-button
					onclick={() => {
						editorRef?.commands.clearContent(true);
					}}
					onkeydown={() => {}}
					role="button"
					tabindex="0"
					variant="default"
					size="small"
					class="secondary col-span-2 sm:col-span-1"><span class="font-barlow text-sm">CLEAR</span></sl-button
				>
				<sl-button
					variant="primary"
					size="small"
					class="col-span-2 sm:col-span-1"
					onclick={() => {
						if (taskStore.selectedTaskId) commentTask(projectId, taskStore.selectedTaskId, currentComment);
						editorRef?.commands.clearContent(true);
					}}
					onkeydown={() => {}}
					role="button"
					tabindex="0"><span class="font-barlow text-sm">COMMENT</span></sl-button
				>
			</div>
		</div>
	{/if}
</div>
