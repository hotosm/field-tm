import { readFileFromOPFS, writeBinaryToOPFS } from '$lib/fs/opfs';
import { getAlertStore } from '$store/common.svelte';
import { getEntitiesStatusStore } from '$store/entities.svelte';

const alertStore = getAlertStore();
const entitiesStore = getEntitiesStatusStore();

export async function loadOfflineExtract(projectId: number) {
	const filePath = `${projectId}/extract.fgb`;

	// Read file from OPFS and display on map
	const opfsExtractFile = await readFileFromOPFS(filePath);

	// FIXME perhaps add error or warning here
	if (!opfsExtractFile) return;

	// Create URL from OPFS file
	const fgbUrl = window.URL.createObjectURL(opfsExtractFile);
	entitiesStore.setFgbOpfsUrl(fgbUrl);
}

async function downloadExtract(url: string | undefined): Promise<ArrayBuffer> {
	let extractData: ArrayBuffer = new ArrayBuffer(0);

	if (!url) return extractData;

	try {
		const downloadResponse = await fetch(url);

		if (!downloadResponse.ok) {
			throw new Error('Failed to download extract');
		}

		extractData = await downloadResponse.arrayBuffer();
		if (!extractData) {
			throw new Error('Extract contained no data');
		}
	} catch (error) {
		alertStore.setAlert({
			variant: 'danger',
			message: 'Error downloading extract file.',
		});
	} finally {
		return extractData;
	}
}

export async function writeOfflineExtract(projectId: number, url: string | undefined) {
	const data = await downloadExtract(url);

	// Copy to OPFS filesystem for offline use
	const filePath = `${projectId}/extract.fgb`;
	await writeBinaryToOPFS(filePath, data);

	await loadOfflineExtract(projectId);
}
