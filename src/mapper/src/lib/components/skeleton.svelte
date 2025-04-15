<script lang="ts">
	import '$styles/skeleton.css';
	type propsType = {
		className?: string;
	};
	const { className }: propsType = $props();
</script>

<div class={`skeleton ${className}`}></div>
