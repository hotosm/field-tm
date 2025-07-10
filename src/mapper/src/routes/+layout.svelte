<script lang="ts">
	import '$styles/page.css';
	import '@hotosm/ui/dist/hotosm-ui';

	import { onMount, onDestroy } from 'svelte';
	import { online } from 'svelte/reactivity/window';
	import { error } from '@sveltejs/kit';
	import type { PageProps } from './$types';
	// import { pwaInfo } from 'virtual:pwa-info';
	import { useRegisterSW } from 'virtual:pwa-register/svelte';
	import type { RegisterSWOptions } from 'vite-plugin-pwa/types';

	import { getCommonStore, getAlertStore } from '$store/common.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { refreshCookies, getUserDetailsFromApi } from '$lib/api/login';
	import Toast from '$lib/components/toast.svelte';
	import Header from '$lib/components/header.svelte';
	import { m } from '$translations/messages.js';

	let { data, children }: PageProps = $props();

	const commonStore = getCommonStore();
	const loginStore = getLoginStore();
	const alertStore = getAlertStore();
	commonStore.setConfig(data.config);

	let dbPromise = data.dbPromise;
	let lastOnlineStatus: boolean | null = $state(null);
	let loginDebounce: ReturnType<typeof setTimeout> | null = $state(null);

	// Required for PWA to work with svelte
	// const webManifestLink = $derived(pwaInfo ? pwaInfo.webManifest.linkTag : '');
    const { registerSW, offlineReady, needRefresh, updateServiceWorker }: RegisterSWOptions = useRegisterSW({
        onRegistered(swr: any) {
            console.log(`SW registered: ${swr}`);
        },
        onRegisterError(error: any) {
            console.log('SW registration error', error);
        },
        onOfflineReady() {
            console.log('SW ready for offline')
			alertStore.setAlert({ message: m['offline.ready_offline'](), variant: 'default', duration: 2000 });
        },
		// // TODO consider enabling this at some point once functionality is more stable?
		// // We wouldn't want to clear projects during active mapping campaign where we
		// // are pushing regular updates
		//
		// async onNeedRefresh() {
		// 	console.log('SW update available');

		// 	alertStore.setAlert({
		// 		message: 'New version available. Refreshing...',
		// 		variant: 'default',
		// 		duration: 2000
		// 	});

		// 	// Run db project cleanup
		// 	const db = await dbPromise;
		// 	db.query('DELETE FROM projects;').then(() => {
		// 		console.log('Old projects cleared due to version update.');
		// 		updateServiceWorker(); // Then update SW
		// 	});
		// }
    });

	async function refreshCookiesAndLogin() {
		try {
			/*
				Login + user details
			*/
			if (online.current) {
				// Online: always go through API and refresh cookies
				let apiUser = await refreshCookies(fetch);
				loginStore.setRefreshCookieResponse(apiUser);

				// svcfmtm is the default 'temp' user, to still allow mapping without login
				if (apiUser?.username !== 'svcfmtm') {
					// Call /auth/me to populate the user details in the header
					apiUser = await getUserDetailsFromApi(fetch);

					if (!apiUser) {
						loginStore.signOut();
						throw error(401, { message: `You must log in first` });
					} else {
						loginStore.setAuthDetails(apiUser);
					}
				}
			}
		} catch (error) {
			console.warn('Error getting user login details')
		}
	}

	// Attempt cookie refresh / login once connectivity restored
	$effect(() => {
		const isOnline = online.current;

		// Prevent running unnecessarily
		if (isOnline === lastOnlineStatus) return;
		lastOnlineStatus = isOnline;

		if (loginDebounce) {
			clearTimeout(loginDebounce);
			loginDebounce = null;
		}

		loginDebounce = setTimeout(() => {
			if (isOnline) {
				refreshCookiesAndLogin();
			}
		}, 200);
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

	onDestroy(async() => {
		const db = await dbPromise();
		db.close()
	});
</script>

<!-- <svelte:head>
	{@html webManifestLink}
</svelte:head> -->

<main class="flex flex-col h-screen overflow-hidden font-barlow">
	<Header></Header>
	<Toast></Toast>

	{#await dbPromise}
		<div class="spinner-wrapper">
			<sl-spinner class="loading-spinner"></sl-spinner>
		</div>
	{:then db}
		{@render children?.({ data, db })}
	{:catch error}
		<p class="text-red-500 p-4">Error loading PGLite: {error.message}</p>
	{/await}
</main>
