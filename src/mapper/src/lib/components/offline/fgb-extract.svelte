<script lang="ts">
	import { writeOfflineExtract } from '$lib/map/extracts';
	import { getAlertStore } from '$store/common.svelte';
	import { getEntitiesStatusStore } from '$store/entities.svelte';
	import { m } from '$translations/messages.js';

	interface Props {
		projectId: number;
		extract_url: string;
	}

	let { projectId, extract_url }: Props = $props();

	const entitiesStore = getEntitiesStatusStore();
	const alertStore = getAlertStore();

	const storeFeaturesOffline = () => {
		if (!entitiesStore.fgbOpfsUrl) {
			writeOfflineExtract(projectId, extract_url);
		} else {
			alertStore.setAlert({ message: m['offline.features_offline_info'](), variant: 'default' });
		}
	};
</script>

<div class="extract">
	<sl-button
		onclick={() => storeFeaturesOffline()}
		onkeydown={(e: KeyboardEvent) => {
			e.key === 'Enter' && storeFeaturesOffline();
		}}
		role="button"
		tabindex="0"
		size="small"
		class="button"
	>
		<sl-icon slot="prefix" name="download" class="icon"></sl-icon>
		<span>{m['offline.features_offline_info']()}</span>
	</sl-button>
</div>
