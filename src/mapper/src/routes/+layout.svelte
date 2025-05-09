<script lang="ts">
	import '$styles/page.css';
	import '@hotosm/ui/dist/hotosm-ui';

	import { onMount } from 'svelte';
	import type { PageProps } from './$types';
	import { pwaInfo } from 'virtual:pwa-info';

	import { getDbOnce } from '$lib/db/pglite';
	import { getCommonStore } from '$store/common.svelte.ts';
	import Toast from '$lib/components/toast.svelte';
	import Header from '$lib/components/header.svelte';

	let { data, children }: PageProps = $props();

	const commonStore = getCommonStore();

	// Required for PWA to work with svelte
	const webManifestLink = $derived(pwaInfo ? pwaInfo.webManifest.linkTag : '');
	commonStore.setConfig(data.config);

	// Start DB loading immediately, outside of onMount
	const dbPromise = getDbOnce().then((db) => {
		commonStore.setDb(db);
		return db;
	});

	onMount(async () => {
		// Dynamically inject CSS specified in config
		if (data.config?.cssFile) {
			const linkElement = document.createElement('link');
			linkElement.rel = 'stylesheet';
			linkElement.href = data.config.cssFile;
			document.head.appendChild(linkElement);
		}
	});
</script>

<svelte:head>
	{@html webManifestLink}
</svelte:head>

<main class="flex flex-col h-screen overflow-hidden font-barlow">
	<Header />
	<Toast />

	{#await dbPromise}
		<div class="spinner-wrapper">
			<sl-spinner class="loading-spinner"></sl-spinner>
		</div>
	{:then db}
		{@render children?.({ data, db })}
	{/await}
</main>
