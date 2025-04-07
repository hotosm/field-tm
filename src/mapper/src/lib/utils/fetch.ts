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
