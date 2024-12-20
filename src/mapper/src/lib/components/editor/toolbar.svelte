<script lang="ts">
	let { editor } = $props();

	const iconClassName = 'text-[1.2rem] text-[#52525B] hover:bg-[#f7d9d8] p-[2px] rounded cursor-pointer duration-200';
</script>

<div style="border-bottom: 1px solid #c2c2c2;" class="flex items-center gap-2 px-2 py-1 flex-wrap">
	<sl-tooltip content="Bold" placement="bottom">
		<hot-icon
			name="bold"
			class={`${iconClassName}`}
			class:active={editor.isActive('bold')}
			onclick={() => editor?.chain()?.focus()?.toggleBold().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleBold().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Italic" placement="bottom">
		<hot-icon
			name="italic"
			class={`${iconClassName}`}
			class:active={editor.isActive('italic')}
			onclick={() => editor?.chain()?.focus()?.toggleItalic().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleItalic().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Strike" placement="bottom">
		<hot-icon
			name="strike"
			class={`${iconClassName}`}
			class:active={editor.isActive('strike')}
			onclick={() => editor?.chain()?.focus()?.toggleStrike().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleStrike().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 1" placement="bottom">
		<hot-icon
			name="h1"
			class={`${iconClassName}`}
			class:active={editor.isActive('heading', { level: 1 })}
			onclick={() => editor?.chain()?.focus()?.toggleHeading({ level: 1 }).run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleHeading({ level: 1 }).run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 2" placement="bottom">
		<hot-icon
			name="h2"
			class={`${iconClassName}`}
			class:active={editor.isActive('heading', { level: 2 })}
			onclick={() => editor?.chain()?.focus()?.toggleHeading({ level: 2 }).run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleHeading({ level: 2 }).run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 3" placement="bottom">
		<hot-icon
			name="h3"
			class={`${iconClassName}`}
			class:active={editor.isActive('heading', { level: 3 })}
			onclick={() => editor?.chain()?.focus()?.toggleHeading({ level: 3 }).run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleHeading({ level: 3 }).run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Unordered List" placement="bottom">
		<hot-icon
			name="list-ul"
			class={`${iconClassName}`}
			class:active={editor.isActive('bulletList')}
			onclick={() => editor?.chain()?.focus()?.toggleBulletList().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleBulletList().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Ordered List" placement="bottom">
		<hot-icon
			name="list-ol"
			class={`${iconClassName}`}
			class:active={editor.isActive('orderedList')}
			onclick={() => editor?.chain()?.focus()?.toggleOrderedList().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleOrderedList().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Code" placement="bottom">
		<hot-icon
			name="code"
			class={`${iconClassName}`}
			class:active={editor.isActive('codeBlock')}
			onclick={() => editor?.chain()?.focus()?.toggleCodeBlock().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleCodeBlock().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Quote" placement="bottom">
		<hot-icon
			name="quote"
			class={`${iconClassName}`}
			class:active={editor.isActive('blockquote')}
			onclick={() => editor?.chain()?.focus()?.toggleBlockquote().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.toggleBlockquote().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Horizontal Ruler" placement="bottom">
		<hot-icon
			name="hr"
			class={`${iconClassName}`}
			onclick={() => editor?.chain()?.focus()?.setHorizontalRule().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.setHorizontalRule().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Undo" placement="bottom">
		<hot-icon
			name="undo"
			class={`${iconClassName}`}
			onclick={() => editor?.chain()?.focus()?.undo().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.undo().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Redo" placement="bottom">
		<hot-icon
			name="redo"
			class={`${iconClassName}`}
			onclick={() => editor?.chain()?.focus()?.redo().run()}
			onkeydown={(e: KeyboardEvent) => {
				if (e.key === 'Enter') editor?.chain()?.focus()?.redo().run();
			}}
			role="button"
			tabindex="0"
		></hot-icon>
	</sl-tooltip>
</div>

<style>
	hot-icon.active {
		background: #f7d9d8;
		color: #e84846;
	}

	sl-tooltip {
		font-size: 10px;
	}
</style>
