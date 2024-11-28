import type { UUID } from 'crypto';

import { getAlertStore, getProjectBasemapStore } from '$store/common.svelte.ts';
import { readFileFromOPFS, writeBinaryToOPFS } from '$lib/fs/opfs';

export interface Basemap {
	id: UUID;
	url: string;
	tile_source: string;
	status: string;
	created_at: string;
	format: string;
	mimetype: string;
}

const API_URL = import.meta.env.VITE_API_URL;
const alertStore = getAlertStore();
const basemapStore = getProjectBasemapStore();

export async function getBasemapList(projectId: number): Promise<Basemap[]> {
	try {
		const basemapsResponse = await fetch(`${API_URL}/projects/${projectId}/tiles`, {
			credentials: 'include',
		});

		if (!basemapsResponse.ok) {
			throw new Error('Failed to fetch basemaps');
		}

		return await basemapsResponse.json();
	} catch (error) {
		console.error('Error refreshing basemaps:', error);
		alertStore.setAlert({
			variant: 'danger',
			message: 'Error fetching basemaps list.',
		});
		return [];
	}
}

type BasemapDownload = {
	data: ArrayBuffer;
	headers: Headers | null;
};

async function downloadBasemap(projectId: number, basemapId: UUID): Promise<BasemapDownload> {
	try {
		const downloadResponse = await fetch(`${API_URL}/projects/${projectId}/tiles/${basemapId}`, {
			credentials: 'include',
		});

		if (!downloadResponse.ok) {
			throw new Error('Failed to download mbtiles');
		}

		let basemapData = await downloadResponse.arrayBuffer();
		if (!basemapData) {
			throw new Error('Basemap contained no data');
		}

		return {
			data: basemapData,
			headers: downloadResponse.headers,
		};
	} catch (error) {
		console.error('Error downloading basemaps:', error);
		alertStore.setAlert({
			variant: 'danger',
			message: 'Error downloading basemap file.',
		});
		return { data: new ArrayBuffer(0), headers: null };
	}
}

export async function downloadMbtiles(projectId: number, basemapId: UUID | null) {
	if (!basemapId) return;

	const { data, headers } = await downloadBasemap(projectId, basemapId);
	const filename = headers?.get('content-disposition')?.split('filename=')[1] || 'basemap.mbtiles';
	const contentType = headers?.get('content-type') || 'application/vnd.mapbox-vector-tile';

	// Create Blob from ArrayBuffer
	const blob = new Blob([data], { type: contentType });
	const downloadUrl = URL.createObjectURL(blob);

	const a = document.createElement('a');
	a.href = downloadUrl;
	a.download = filename;
	a.click();

	// Clean up object URL
	URL.revokeObjectURL(downloadUrl);
}

export async function loadOnlinePmtiles(selectedBasemap: Basemap) {
	const pmtilesUrl = `pmtiles://${selectedBasemap.url}`;
	basemapStore.setProjectPmtilesUrl(pmtilesUrl);
}

export async function loadOfflinePmtiles(projectId: number) {
	const filePath = `${projectId}/all.pmtiles`;

	// Read file from OPFS and display on map
	const opfsPmtilesData = await readFileFromOPFS(filePath);
	// FIXME perhaps add error or warning here
	if (!opfsPmtilesData) return;

	// Create URL from OPFS file (must start with pmtiles://)
	const pmtilesUrl = `pmtiles://${URL.createObjectURL(opfsPmtilesData)}`;
	// URL.revokeObjectURL(pmtilesUrl);

	basemapStore.setProjectPmtilesUrl(pmtilesUrl);
}

export async function writeOfflinePmtiles(projectId: number, basemapId: UUID | null) {
	if (!basemapId) return;

	const { data } = await downloadBasemap(projectId, basemapId);

	// Copy to OPFS filesystem for offline use
	const filePath = `${projectId}/all.pmtiles`;
	await writeBinaryToOPFS(filePath, data);

	await loadOfflinePmtiles(projectId);
}
