<script lang="ts">
	import '@hotosm/ui/dist/style.css';
	import '@hotosm/ui/dist/hotosm-ui';
	import { setBasePath } from '@hotosm/ui/dist/hotosm-ui';
	import Toast from '$lib/components/toast.svelte';
	import Header from '$lib/components/header.svelte';

	setBasePath('/mapnow');

	let { data, children } = $props();
</script>

<main class="flex flex-col h-screen overflow-hidden font-barlow-regular">
	<Header />
	<Toast />
	{@render children?.({ data })}
</main>
