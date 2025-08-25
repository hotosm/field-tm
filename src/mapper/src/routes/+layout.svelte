<script lang="ts">
	import '$styles/page.css';
	import '$styles/layout.css';
	import '@hotosm/ui';
	import '@hotosm/ui/dist/style.css';
	import '@shoelace-style/shoelace/dist/themes/light.css';
	import '@shoelace-style/shoelace/dist/shoelace.js';

	import { onMount } from 'svelte';
	import { online } from 'svelte/reactivity/window';
	import { error } from '@sveltejs/kit';
	import type { PageProps } from './$types';

	import { getCommonStore } from '$store/common.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { refreshCookies, getUserDetailsFromApi } from '$lib/api/login';
	import Toast from '$lib/components/toast.svelte';
	import Header from '$lib/components/header.svelte';

	let { data, children }: PageProps = $props();

	const commonStore = getCommonStore();
	const loginStore = getLoginStore();
	commonStore.setConfig(data.config);

	let lastOnlineStatus: boolean | null = $state(null);
	let loginDebounce: ReturnType<typeof setTimeout> | null = $state(null);

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
			console.warn('Error getting user login details');
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
</script>

<main class="layout flex flex-col h-screen overflow-hidden">
	<Header></Header>
	<Toast></Toast>
	{@render children?.({ data })}
	<hot-tracking site-id="28" domain={'mapper.fmtm.hotosm.org'}></hot-tracking>
</main>
