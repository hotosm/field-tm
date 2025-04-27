import { getAlertStore } from '$store/common.svelte.ts';

const alertStore = getAlertStore();

export function openOdkCollectNewFeature(xFormId: string, entityId: string) {
	if (!xFormId || !entityId) {
		return;
	}

	const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

	if (!isMobile) {
		alertStore.setAlert({
			variant: 'warning',
			message: 'Requires a mobile phone with ODK Collect.',
		});
	} else {
		// TODO we need to update the form to support task_id=${}&
		document.location.href = `odkcollect://form/${xFormId}?feature=${entityId}`;
	}
}
