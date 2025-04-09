<script>
	import { goto } from '$app/navigation';
	import { getUserDetailsFromApi } from '$lib/utils/login';
	import { getAlertStore } from '$store/common.svelte';
	import { getLoginStore } from '$store/login.svelte';
	import { onMount } from 'svelte';
	const location = window.location;
	const params = new URLSearchParams(location.search);
	const authCode = params.get('code');
	const state = params.get('state');
	const alert = getAlertStore();
	const loginStore = getLoginStore();

	const loginRedirect = async () => {
		if (authCode) {
			try {
				let response;
				if (location.pathname.includes('googleauth')) {
					response = await fetch(
						`${import.meta.env.VITE_API_URL}/auth/callback/google?code=${authCode}&state=${state}`,
						{ credentials: 'include' },
					);
				} else {
					response = await fetch(`${import.meta.env.VITE_API_URL}/auth/callback/osm/mapper?code=${authCode}&state=${state}`, {
						credentials: 'include',
					});
				}

				if (!response.ok) {
					throw new Error(`Callback request failed with status ${response.status}`);
				}
				const apiUser = await getUserDetailsFromApi(fetch);
				loginStore.setAuthDetails(apiUser);
				goto('/');
			} catch (err) {
				alert.setAlert({
					variant: 'danger',
					message: `Error during callback: ${err}` || 'Failed to authenticate. Please try again.',
				});
			}
		}
	};

	onMount(() => {
		if (
			window.location.href.includes('127.0.0.1:7057/googleauth') ||
			window.location.href.includes('127.0.0.1:7057/osmauth')
		) {
			window.location.href = `http://mapper.fmtm.localhost:7050${location.pathname}${location.search}`;
			return;
		}

		loginRedirect();
	});
</script>

<div class="h-full flex flex-col justify-center items-center">
	<sl-spinner style="font-size: 4rem; --track-width: 4px;"></sl-spinner>
	<h2 class="font-barlow text-[#757575] font-semibold">Signing in...</h2>
</div>
