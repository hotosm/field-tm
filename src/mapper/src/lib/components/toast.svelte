<script lang="ts">
	import SlAlert from '@shoelace-style/shoelace/dist/components/alert/alert.js';
	import { getAlertStore } from '$store/common.svelte.ts';

	const alertStore = getAlertStore();
	let alertRef: SlAlert | undefined = $state();

	$effect(() => {
		if (alertStore.alert) {
			if (!alertStore.alert?.message) return;
			// Display the alert
			alertRef?.toast();
		}
	});

	const iconName = {
		default: 'info-circle',
		success: 'check',
		warning: 'exclamation-triangle',
		danger: 'exclamation-octagon',
	};

	// map with variant because red color for error/danger is not red color i.e. primary is associated with red color (due to HOT theme)
	const variantMap = {
		default: 'default',
		success: 'success',
		warning: 'warning',
		danger: 'primary',
	};
</script>

<div>
	<sl-alert bind:this={alertRef} variant={variantMap?.[alertStore.alert?.variant]} duration="4000" closable>
		<sl-icon slot="icon" name={iconName?.[alertStore.alert?.variant]}></sl-icon>
		{alertStore.alert?.message}
	</sl-alert>
</div>

<style>
	.alert-duration sl-alert {
		margin-top: var(--sl-spacing-medium);
	}
</style>
