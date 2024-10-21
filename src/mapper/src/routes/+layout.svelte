<script lang="ts">
	import '@hotosm/ui/dist/style.css';
	import '@hotosm/ui/dist/hotosm-ui';
	import { setBasePath } from '@hotosm/ui/dist/hotosm-ui';
	import Toast from '$lib/components/common/toast.svelte';

	setBasePath('/mapnow');

	export let data;
</script>

<main class="flex flex-col h-screen overflow-hidden">
	<hot-header></hot-header>
	<Toast />
	<slot {data}></slot>
</main>
