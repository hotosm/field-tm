<script>
	import { page } from '$app/stores';
	import { getLoginStore } from '$store/login.svelte.ts';

	const loginStore = getLoginStore();

	$effect(() => {
		if ($page.status === 403 && !loginStore.getAuthDetails) {
			loginStore.toggleLoginModal(true);
		} else {
			loginStore.toggleLoginModal(false);
		}
	});
</script>

<h1>{$page.error.message}</h1>
