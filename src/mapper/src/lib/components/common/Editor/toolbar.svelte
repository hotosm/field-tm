<script lang="ts">
	export let editor;

	const iconClassName = 'text-[1.2rem] text-[#52525B] hover:bg-[#f7d9d8] p-[2px] rounded cursor-pointer duration-200';
</script>

<div style="border-bottom: 1px solid #c2c2c2;" class="flex items-center gap-2 px-2 py-1 flex-wrap">
	<sl-tooltip content="Bold" placement="bottom">
		<hot-icon
			name="bold"
			class={`${iconClassName}`}
			class:active={editor.isActive('bold')}
			on:click={() => editor?.chain()?.focus()?.toggleBold().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Italic" placement="bottom">
		<hot-icon
			name="italic"
			class={`${iconClassName}`}
			class:active={editor.isActive('italic')}
			on:click={() => editor?.chain()?.focus()?.toggleItalic().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Strike" placement="bottom">
		<hot-icon
			name="strike"
			class={`${iconClassName}`}
			class:active={editor.isActive('strike')}
			on:click={() => editor?.chain()?.focus()?.toggleStrike().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 1" placement="bottom">
		<hot-icon
			name="h1"
			class={`${iconClassName}`}
			class:active={editor.isActive('heading', { level: 1 })}
			on:click={() => editor?.chain()?.focus()?.toggleHeading({ level: 1 }).run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 2" placement="bottom">
		<hot-icon
			name="h2"
			class={`${iconClassName}`}
			class:active={editor.isActive('heading', { level: 2 })}
			on:click={() => editor?.chain()?.focus()?.toggleHeading({ level: 2 }).run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Heading 3" placement="bottom">
		<hot-icon
			name="h3"
			class={`${iconClassName}`}
			class:active={editor.isActive('heading', { level: 3 })}
			on:click={() => editor?.chain()?.focus()?.toggleHeading({ level: 3 }).run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Unordered List" placement="bottom">
		<hot-icon
			name="list-ul"
			class={`${iconClassName}`}
			class:active={editor.isActive('bulletList')}
			on:click={() => editor?.chain()?.focus()?.toggleBulletList().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Ordered List" placement="bottom">
		<hot-icon
			name="list-ol"
			class={`${iconClassName}`}
			class:active={editor.isActive('orderedList')}
			on:click={() => editor?.chain()?.focus()?.toggleOrderedList().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Code" placement="bottom">
		<hot-icon
			name="code"
			class={`${iconClassName}`}
			class:active={editor.isActive('codeBlock')}
			on:click={() => editor?.chain()?.focus()?.toggleCodeBlock().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Quote" placement="bottom">
		<hot-icon
			name="quote"
			class={`${iconClassName}`}
			class:active={editor.isActive('blockquote')}
			on:click={() => editor?.chain()?.focus()?.toggleBlockquote().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Horizontal Ruler" placement="bottom">
		<hot-icon name="hr" class={`${iconClassName}`} on:click={() => editor?.chain()?.focus()?.setHorizontalRule().run()}
		></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Undo" placement="bottom">
		<hot-icon name="undo" class={`${iconClassName}`} on:click={() => editor?.chain()?.focus()?.undo().run()}></hot-icon>
	</sl-tooltip>
	<sl-tooltip content="Redo" placement="bottom">
		<hot-icon name="redo" class={`${iconClassName}`} on:click={() => editor?.chain()?.focus()?.redo().run()}></hot-icon>
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
