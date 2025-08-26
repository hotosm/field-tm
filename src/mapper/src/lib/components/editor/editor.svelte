<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import '$styles/button.css';
	import '$styles/editor.css';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Link from '@tiptap/extension-link';
	import Image from '@tiptap/extension-image';

	import Toolbar from '$lib/components/editor/toolbar.svelte';

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
			extensions: [
				StarterKit,
				Link.configure({
					validate: (href: string) => /^https?:\/\//.test(href),
				}),
				Image.configure({
					inline: true,
				}),
			],
			content: content,
			onTransaction: () => {
				editor = editor;
			},
			editable: editable,
			onUpdate: (
				{
					/** editor **/
				},
			) => {
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

<div class="editor-wrapper">
	<div class="editor {editable ? 'editable' : 'non-editable'}">
		{#if editor && editable}
			<Toolbar {editor} />
		{/if}

		<div class="bottom">
			<div bind:this={element}></div>
		</div>
	</div>
</div>
