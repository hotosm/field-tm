<script lang="ts">
	type propsType = {
		className?: string;
	};
	const { className }: propsType = $props();
</script>

<div class={`animate-pulse rounded-md bg-[#D7D7D7] ${className}`}></div>
