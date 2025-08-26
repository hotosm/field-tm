<script lang="ts">
	import '$styles/editor.css';
	let { editor } = $props();
</script>

<div class="toolbar">
	<sl-tooltip content="Bold" placement="bottom">
		<sl-icon
			name="bold"
			class="icon"
			class:active={editor.isActive('bold')}
			onclick={() => editor?.chain()?.focus()?.toggleBold().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleBold().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Italic" placement="bottom">
		<sl-icon
			name="italic"
			class="icon"
			class:active={editor.isActive('italic')}
			onclick={() => editor?.chain()?.focus()?.toggleItalic().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleItalic().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Strike" placement="bottom">
		<sl-icon
			name="strike"
			class="icon"
			class:active={editor.isActive('strike')}
			onclick={() => editor?.chain()?.focus()?.toggleStrike().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleStrike().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 1" placement="bottom">
		<sl-icon
			name="h1"
			class="icon"
			class:active={editor.isActive('heading', { level: 1 })}
			onclick={() => editor?.chain()?.focus()?.toggleHeading({ level: 1 }).run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleHeading({ level: 1 }).run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 2" placement="bottom">
		<sl-icon
			name="h2"
			class="icon"
			class:active={editor.isActive('heading', { level: 2 })}
			onclick={() => editor?.chain()?.focus()?.toggleHeading({ level: 2 }).run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleHeading({ level: 2 }).run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 3" placement="bottom">
		<sl-icon
			name="h3"
			class="icon"
			class:active={editor.isActive('heading', { level: 3 })}
			onclick={() => editor?.chain()?.focus()?.toggleHeading({ level: 3 }).run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleHeading({ level: 3 }).run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Unordered List" placement="bottom">
		<sl-icon
			name="list-ul"
			class="icon"
			class:active={editor.isActive('bulletList')}
			onclick={() => editor?.chain()?.focus()?.toggleBulletList().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleBulletList().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Ordered List" placement="bottom">
		<sl-icon
			name="list-ol"
			class="icon"
			class:active={editor.isActive('orderedList')}
			onclick={() => editor?.chain()?.focus()?.toggleOrderedList().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleOrderedList().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Code" placement="bottom">
		<sl-icon
			name="code"
			class="icon"
			class:active={editor.isActive('codeBlock')}
			onclick={() => editor?.chain()?.focus()?.toggleCodeBlock().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleCodeBlock().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Quote" placement="bottom">
		<sl-icon
			name="quote"
			class="icon"
			class:active={editor.isActive('blockquote')}
			onclick={() => editor?.chain()?.focus()?.toggleBlockquote().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleBlockquote().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Horizontal Ruler" placement="bottom">
		<sl-icon
			name="hr"
			class="icon"
			onclick={() => editor?.chain()?.focus()?.setHorizontalRule().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.setHorizontalRule().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Undo" placement="bottom">
		<sl-icon
			name="undo"
			class="icon"
			onclick={() => editor?.chain()?.focus()?.undo().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.undo().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
	<sl-tooltip content="Redo" placement="bottom">
		<sl-icon
			name="redo"
			class="icon"
			onclick={() => editor?.chain()?.focus()?.redo().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.redo().run();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</sl-tooltip>
</div>
