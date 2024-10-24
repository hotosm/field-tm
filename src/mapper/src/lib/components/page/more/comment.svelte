<script>
	import Editor from '$lib/components/common/Editor/editor.svelte';
	import CommentSkeleton from '$lib/components/skeleton/comment.svelte';
</script>

<div class="h-[calc(100%-2.25rem)] sm:h-[calc(100%-2.6rem)]">
	<div class="h-[calc(100%-11.875rem)] overflow-y-scroll overflow-x-hidden flex flex-col gap-2">
		{#if false}
			{#each Array.from({ length: 5 }) as _, index}
				<CommentSkeleton />
			{/each}
		{:else}
			{#each Array.from({ length: 5 }) as _, index}
				<div class="flex flex-col gap-2 py-3 bg-[#F6F5F5] rounded-md">
					<div class="flex gap-4 px-3">
						<hot-icon
							name="person-fill"
							style="border: 1px solid"
							class="!text-[1.7rem] text-red-600 cursor-pointer duration-200 rounded-full p-[2px] bg-white"
						></hot-icon>
						<div class="flex flex-col gap-1 flex-1">
							<p class="font-semibold">Localadmin</p>
							<div class="flex items-center justify-between">
								<p class="text-[#484848] text-sm">#2</p>
								<div class="flex items-center gap-2">
									<hot-icon name="clock-history" class="!text-[1rem] text-red-600 cursor-pointer duration-200"
									></hot-icon>
									<p class="text-[#484848] text-sm">2024-10-21 11:42</p>
								</div>
							</div>
						</div>
					</div>
					<Editor editable={false} content={'<p>This is a comment</p>'} />
				</div>
			{/each}
		{/if}
	</div>

	<div class="mt-2">
		<Editor
			editable={true}
			content=""
			setEditorHtmlContent={(editorText) => {
				// to-do: store state to post comment
			}}
		/>
		<div class="w-full flex justify-end my-2 gap-2">
			<sl-button variant="default" size="small" class="secondary col-span-2 sm:col-span-1"
				><span class="font-barlow-medium text-sm">CLEAR</span></sl-button
			>
			<sl-button variant="default" size="small" class="primary col-span-2 sm:col-span-1"
				><span class="font-barlow-medium text-sm">COMMENT</span></sl-button
			>
		</div>
	</div>
</div>

<style></style>
