<script lang="ts">
	import '@hotosm/ui/dist/hotosm-ui';
	import { onMount } from 'svelte';
	import { pwaInfo } from 'virtual:pwa-info';

	import { getCommonStore } from '$store/common.svelte.ts';
	import Toast from '$lib/components/toast.svelte';
	import Header from '$lib/components/header.svelte';

	let { data, children } = $props();
	const commonStore = getCommonStore();
	// Required for PWA to work with svelte
	const webManifestLink = $derived(pwaInfo ? pwaInfo.webManifest.linkTag : '');

	onMount(async () => {
		const response = await fetch('/config.json');
    	const configData = await response.json();
		commonStore.setConfig(configData);

		// Dynamically inject CSS specified in config
		if (configData?.cssFile) {
			const linkElement = document.createElement('link');
			linkElement.rel = 'stylesheet';
			linkElement.href = configData.cssFile;
			document.head.appendChild(linkElement);
		}
	})
</script>

<svelte:head> 
 	{@html webManifestLink} 
</svelte:head>
<main class="flex flex-col h-screen overflow-hidden">
	<Header />
	<Toast />
	{@render children?.({ data })}
</main>
