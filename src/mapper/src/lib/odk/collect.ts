import type { Geometry as GeoJSONGeometry } from 'geojson';

import { getAlertStore } from '$store/common.svelte.ts';
import { geojsonGeomToJavarosa } from '$lib/odk/javarosa';

const alertStore = getAlertStore();

export function openOdkCollectNewFeature(xFormId: string, geom: GeoJSONGeometry, task_id: number | null) {
	if (!xFormId || !geom) {
		return;
	}

	const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

	const javarosaGeom = geojsonGeomToJavarosa(geom);

	if (isMobile) {
		document.location.href = `odkcollect://form/${xFormId}?new_feature=${javarosaGeom}&task_id=${task_id}`;
	} else {
		alertStore.setAlert({
			variant: 'warning',
			message: 'Requires a mobile phone with ODK Collect.',
		});
	}
}
