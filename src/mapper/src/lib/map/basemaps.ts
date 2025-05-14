import type { UUID } from 'crypto';

import { getAlertStore, getProjectBasemapStore } from '$store/common.svelte.ts';
import { readFileFromOPFS, writeBinaryToOPFS } from '$lib/fs/opfs';
import { m } from '$translations/messages.js';

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
			message: m['error_downloading'](),
		});
		return [];
	}
}

export async function loadOnlinePmtiles(url: string | undefined) {
	if (!url) return;

	const pmtilesUrl = `pmtiles://${url}`;
	basemapStore.setProjectPmtilesUrl(pmtilesUrl);
}

export async function loadOfflinePmtiles(projectId: number) {
	const filePath = `${projectId}/basemap.pmtiles`;

	// Read file from OPFS and display on map
	const opfsPmtilesData = await readFileFromOPFS(filePath);
	// FIXME perhaps add error or warning here
	if (!opfsPmtilesData) return;

	// Create URL from OPFS file (must start with pmtiles://)
	const pmtilesUrl = `pmtiles://${URL.createObjectURL(opfsPmtilesData)}`;
	// URL.revokeObjectURL(pmtilesUrl);

	basemapStore.setProjectPmtilesUrl(pmtilesUrl);
}

async function downloadBasemap(url: string | undefined): Promise<ArrayBuffer> {
	let basemapData: ArrayBuffer = new ArrayBuffer(0);

	if (!url) return basemapData;

	try {
		const downloadResponse = await fetch(url);

		if (!downloadResponse.ok) {
			throw new Error('Failed to download mbtiles');
		}

		basemapData = await downloadResponse.arrayBuffer();
		if (!basemapData) {
			throw new Error('Basemap contained no data');
		}
	} catch (error) {
		console.error('Error downloading basemaps:', error);
		alertStore.setAlert({
			variant: 'danger',
			message: m['error_downloading'](),
		});
	} finally {
		return basemapData;
	}
}

export async function writeOfflinePmtiles(projectId: number, url: string | undefined) {
	const data = await downloadBasemap(url);

	// Copy to OPFS filesystem for offline use
	const filePath = `${projectId}/basemap.pmtiles`;
	await writeBinaryToOPFS(filePath, data);

	await loadOfflinePmtiles(projectId);
}
