const API_URL = import.meta.env.VITE_API_URL;

const DEFAULT_CACHE_NAME = 'c488ea01-8c52-4a18-a93e-934bc77f1eb8';

export async function fetchCachedBlobUrl(url: string, cacheName: string): Promise<string> {
	const cacheStorage = await caches.open(cacheName || DEFAULT_CACHE_NAME);
	const response = await cacheStorage.match(url);
	if (response) {
		const blob = await response.blob();
		return URL.createObjectURL(blob);
	} else {
		const response = await fetch(url);
		cacheStorage.put(url, response);
		const blob = await response.blob();
		return URL.createObjectURL(blob);
	}
}

/**
 * @name fetchBlobUrl
 * @param url - url to a web resource like a script or xml file
 * @returns {string} object url to the cached fetch response
 */
export async function fetchBlobUrl(url: string): Promise<string> {
	const response = await fetch(url);
	const blob = await response.blob();
	return URL.createObjectURL(blob);
}

export async function fetchFormMediBlobUrls(projectId: number): Promise<{ [filename: string]: string }> {
	if (projectId === undefined) return {};

	const response = await fetch(`${API_URL}/central/get-form-media?project_id=${projectId}`, { method: 'POST' });
	const data: { [filename: string]: string } = await response.json();

	const formMediaBlobs: { [filename: string]: string } = {};
	for (let filename in data) {
		const url = data[filename];
		formMediaBlobs[filename] = await fetchBlobUrl(url);
	}

	return formMediaBlobs;
}
