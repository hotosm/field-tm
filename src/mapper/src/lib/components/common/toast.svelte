<script lang="ts">
	import { setAlert } from '$store/common';

	let alertRef;
	let alertInfo;

	setAlert.subscribe((value) => {
		if (!value?.message) return;
		alertInfo = value;
		alertRef?.toast();
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
	<sl-alert bind:this={alertRef} variant={variantMap?.[alertInfo?.variant]} duration="4000" closable>
		<sl-icon slot="icon" name={iconName?.[alertInfo?.variant]}></sl-icon>
		{alertInfo?.message}
	</sl-alert>
</div>

<style>
	.alert-duration sl-alert {
		margin-top: var(--sl-spacing-medium);
	}
</style>
