import type { Geometry as GeoJSONGeometry } from 'geojson';

import { getAlertStore } from '$store/common.svelte.ts';
import { geojsonGeomToJavarosa } from '$lib/odk/javarosa';

const alertStore = getAlertStore();

export function openOdkCollectNewFeature(xFormId: string, geom: GeoJSONGeometry) {
	if (!xFormId || !geom) {
		return;
	}

	const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

	const javarosaGeom = geojsonGeomToJavarosa(geom);

	if (isMobile) {
		// TODO we need to update the form to support task_id=${}&
		document.location.href = `odkcollect://form/${xFormId}?new_feature=${javarosaGeom}`;
	} else {
		alertStore.setAlert({
			variant: 'warning',
			message: 'Requires a mobile phone with ODK Collect.',
		});
	}
}
