import type { FeatureCollection } from 'geojson';

import type { OdkEntity } from '$store/collections';

const API_URL = import.meta.env.VITE_API_URL;

export const entities = {
	create: async (featcol: FeatureCollection): Promise<{ entity: OdkEntity; txid: number }> => {
		const entity: OdkEntity = featcol.features.at(-1)?.properties;
		const response = await fetch(
			`${API_URL}/central/entity?project_id=${entity.project_id}&entity_uuid=${entity.entity_id}`,
			{
				method: 'POST',
				body: JSON.stringify(featcol),
				headers: { 'Content-type': 'application/json' },
				credentials: 'include',
			},
		);
		if (!response.ok) {
			const errorData = await response.json();
			// alertStore.setAlert({
			// 	variant: 'danger',
			// 	message: error.message || 'Failed to create entity',
			// });
			throw new Error(errorData.detail);
		}
		return response.json();
	},
	update: async (
		projectId: string,
		// The endpoint is non-standard an also accepts a 'label' field
		changes: Partial<OdkEntity> & { label?: string },
	): Promise<{ entity: OdkEntity; txid: number }> => {
		const response = await fetch(`${API_URL}/projects/${projectId}/entity/status`, {
			method: `POST`,
			body: JSON.stringify(changes),
			headers: { 'Content-Type': `application/json` },
			credentials: 'include',
		});
		if (!response.ok) {
			const errorData = await response.json();
			// alertStore.setAlert({
			// 	variant: 'danger',
			// 	message: error.message || 'Failed to update entity',
			// });
			throw new Error(errorData.detail);
		}
		return response.json();
	},
	delete: async (projectId: string, entityId: string): Promise<{ success: boolean; txid: number }> => {
		const response = await fetch(`${API_URL}/projects/entity/${entityId}?project_id=${projectId}`, {
			method: `DELETE`,
			credentials: 'include',
		});
		if (!response.ok) {
			const errorData = await response.json();
			// alertStore.setAlert({
			// 	variant: 'danger',
			// 	message: error.message || 'Failed to delete entity',
			// });
			throw new Error(errorData.detail);
		}
		return response.json();
	},
};
