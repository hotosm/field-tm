<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getAlertStore } from '$store/common.svelte';
	import { getLoginStore } from '$store/login.svelte';
	import '$styles/auth.css';

	const VITE_API_URL = import.meta.env.VITE_API_URL;
	const location = window.location;
	const params = new URLSearchParams(location.search);
	const token = params.get('token');

	const alert = getAlertStore();
	const loginStore = getLoginStore();

	onMount(async () => {
		try {
			const response = await fetch(`${VITE_API_URL}/users/invite/${token}`, {
				credentials: 'include',
			});

			// if user signed in, status is 200
			if (response.status === 200) {
				sessionStorage.removeItem('requestedPath');
				goto('/');
				return;
			}

			const responseData = await response.json();

			// if user not signed in, status is 401. so set inviteUrl path in session storage & show login modal, and after successful sign-in redirect to inviteUrl
			if (
				response.status === 401 ||
				(response.status === 403 && loginStore?.refreshCookieResponse?.username === 'svcfmtm')
			) {
				sessionStorage.setItem('requestedPath', `${location.pathname}${location.search}`);
				loginStore.toggleLoginModal(true);
				loginStore.setRefreshCookieResponse({});
				return;
			}
			// throw error besides 401
			else if (!response.ok) {
				throw new Error(responseData?.detail);
			}
		} catch (error) {
			if (error instanceof Error) {
				alert.setAlert({
					variant: 'danger',
					message: error.message || 'Failed to accept invitation',
				});
				goto('/');
			}
		}
	});
</script>

<div class="spinner">
	<sl-spinner></sl-spinner>
	<h2>Accepting Invitation...</h2>
</div>
