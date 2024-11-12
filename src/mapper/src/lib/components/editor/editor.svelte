<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import '$styles/button.css';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Toolbar from '$lib/components/editor/toolbar.svelte';
	import '$lib/components/editor/editor.css';

	type Props = {
		editable: boolean;
		content: string;
		setEditorHtmlContent?: (content: string) => any;
		setEditorRef?: (editor: any) => void;
	};

	let element: Element | undefined = $state();
	let editor: Editor | undefined = $state();
	let { editable, content, setEditorHtmlContent, setEditorRef }: Props = $props();

	onMount(() => {
		editor = new Editor({
			element: element,
			extensions: [StarterKit],
			content: content,
			onTransaction: () => {
				editor = editor;
			},
			editable: editable,
			onUpdate: ({ editor }) => {
				setEditorHtmlContent && setEditorHtmlContent(editor.getHTML());
			},
		});
		setEditorRef && setEditorRef(editor);
	});

	onDestroy(() => {
		if (editor) {
			editor?.destroy();
		}
	});
</script>

<div>
	<div style={`border: ${editable ? '1px' : '0px'} solid #c2c2c2;`} class="rounded-md">
		{#if editor && editable}
			<Toolbar {editor} />
		{/if}

		<div class={`${editable ? 'h-[80px] overflow-y-scroll pt-[3px]' : 'h-full'}`}>
			<div bind:this={element}></div>
		</div>
	</div>
</div>

<style>
</style>
