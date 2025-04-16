import { getAlertStore, getCommonStore } from '$store/common.svelte.ts';

const commonStore = getCommonStore();
const alertStore = getAlertStore();
const enableWebforms = commonStore.config?.enableWebforms || false;

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
	} else if (enableWebforms) {
		// TODO can we open the webform directly, instead of needing to click
		// TODO the 'Collect Data' button?
	} else {
		// TODO we need to update the form to support task_id=${}&
		document.location.href = `odkcollect://form/${xFormId}?feature=${entityId}`;
	}
}
