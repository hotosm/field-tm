<script>
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Toolbar from './toolbar.svelte';
	import './editor.css';
	import '../../../../styles/button.css';

	let element;
	let editor;

	onMount(() => {
		editor = new Editor({
			element: element,
			extensions: [StarterKit],
			content: '',
			onTransaction: () => {
				editor = editor;
			},
		});
	});

	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});
</script>

<div>
	<div style="border: 1px solid #c2c2c2;" class="rounded-md">
		{#if editor}
			<Toolbar {editor} />
		{/if}

		<div bind:this={element} />
	</div>
	<div class="w-full flex justify-end my-2 gap-2">
		<sl-button
			on:click={editor?.commands.clearContent(true)}
			variant="default"
			size="small"
			class="secondary col-span-2 sm:col-span-1"><span class="font-barlow-medium text-sm">CLEAR</span></sl-button
		>
		<sl-button variant="default" size="small" class="primary col-span-2 sm:col-span-1"
			><span class="font-barlow-medium text-sm">COMMENT</span></sl-button
		>
	</div>
</div>

<style>
</style>
