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

async function downloadBasemap(
	url: string | undefined,
	onProgress?: (percent: number) => void,
	// default to 10 minutes, as firefox sets 60s, chrome 300s
	timeoutMs = 10 * 60 * 1000,
): Promise<ArrayBuffer> {
	if (!url) return new ArrayBuffer(0);

	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), timeoutMs);

	try {
		const response = await fetch(url, { signal: controller.signal });

		clearTimeout(timeout);

		if (!response.ok || !response.body) {
			throw new Error('Failed to download basemap');
		}

		const contentLengthHeader = response.headers.get('Content-Length');
		const contentLength = contentLengthHeader ? parseInt(contentLengthHeader, 10) : null;

		const reader = response.body.getReader();
		const chunks: Uint8Array[] = [];
		let receivedLength = 0;

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			if (value) {
				chunks.push(value);
				receivedLength += value.length;

				if (onProgress) {
					if (contentLength) {
						onProgress((receivedLength / contentLength) * 100);
					} else {
						// Fallback: unknown total size
						onProgress(0); // Unknown progress
					}
				}
			}
		}

		const result = new Uint8Array(receivedLength);
		let position = 0;
		for (const chunk of chunks) {
			result.set(chunk, position);
			position += chunk.length;
		}
		return result.buffer;
	} catch (error: any) {
		if (error.name === 'AbortError') {
			console.warn('Timeout downloading basemap', error);
		} else {
			console.error('Error downloading basemaps:', error);
		}

		alertStore.setAlert({
			variant: 'danger',
			message: m['error_downloading'](),
		});

		return new ArrayBuffer(0);
	}
}

export async function writeOfflinePmtiles(
	projectId: number,
	url: string | undefined,
	onProgress?: (percent: number) => void,
) {
	const data = await downloadBasemap(url, onProgress);

	// Ensure final update to 100% in case it wasn't hit exactly
	if (onProgress) onProgress(100);

	// Copy to OPFS filesystem for offline use
	const filePath = `${projectId}/basemap.pmtiles`;
	await writeBinaryToOPFS(filePath, data);

	await loadOfflinePmtiles(projectId);
}
