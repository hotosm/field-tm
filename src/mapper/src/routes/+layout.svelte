<script lang="ts">
	import '@hotosm/ui/dist/style.css';
	import '@hotosm/ui/dist/hotosm-ui';
	import { pwaInfo } from 'virtual:pwa-info';
	import Toast from '$lib/components/toast.svelte';
	import Header from '$lib/components/header.svelte';

	let { data, children } = $props();
	const webManifestLink = $derived(pwaInfo ? pwaInfo.webManifest.linkTag : '');
</script>

<svelte:head> 
 	{@html webManifestLink} 
</svelte:head>
<main class="flex flex-col h-screen overflow-hidden">
	<Header />
	<Toast />
	{@render children?.({ data })}
</main>
