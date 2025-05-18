import type { PGlite } from '@electric-sql/pglite';
import type { DbApiSubmissionType } from '$lib/types.ts';
import { DbApiSubmission } from '$lib/db/api-submissions.ts';

const API_URL = import.meta.env.VITE_API_URL;

const DEFAULT_CACHE_NAME = 'c488ea01-8c52-4a18-a93e-934bc77f1eb8';

async function fetchCachedBlobUrl(url: string, cacheName: string): Promise<string> {
	const cacheStorage = await caches.open(cacheName || DEFAULT_CACHE_NAME);
	const response = await cacheStorage.match(url);
	if (response) {
		const blob = await response.blob();
		return URL.createObjectURL(blob);
	} else {
		const response = await fetch(url);
		// clone the response stream as it can only be consumed again
		cacheStorage.put(url, response.clone());
		const blob = await response.blob();
		return URL.createObjectURL(blob);
	}
}

/**
 * @name fetchBlobUrl
 * @param url - url to a web resource like a script or xml file
 * @returns {string} object url to the cached fetch response
 */
async function fetchBlobUrl(url: string): Promise<string> {
	const response = await fetch(url);
	const blob = await response.blob();
	return URL.createObjectURL(blob);
}

async function fetchFormMediBlobUrls(projectId: number): Promise<{ [filename: string]: string }> {
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

type SubmissionResult = { id: number; success: boolean } | undefined;

async function sendNextQueuedSubmissionToApi(db: PGlite): Promise<SubmissionResult | null> {
	const nextSubmission = await DbApiSubmission.next(db);
	if (!nextSubmission) return null;

	try {
		const fetchOptions = buildFetchOptions(nextSubmission);
		const response = await fetch(nextSubmission.url, fetchOptions);

		await DbApiSubmission.update(
			db,
			nextSubmission.id,
			response.ok ? 'RECEIVED' : 'FAILED',
			response.ok ? null : `HTTP ${response.status}`,
		);

		return { id: nextSubmission.id, success: response.ok };
	} catch (err: any) {
		await DbApiSubmission.update(db, nextSubmission.id, 'FAILED', String(err));
		return { id: nextSubmission.id, success: false };
	}
}

function isBlob(value: unknown): value is Blob {
	return typeof Blob !== 'undefined' && value instanceof Blob;
}

function buildFetchOptions(submission: DbApiSubmissionType): RequestInit {
	const { method, content_type, payload, headers } = submission;

	const combinedHeaders: Record<string, string> = {
		'Content-Type': content_type,
		...(headers || {}),
	};

	const fetchOptions: RequestInit = {
		method,
		headers: combinedHeaders,
	};

	if (method !== 'GET' && method !== 'HEAD') {
		if (content_type === 'application/json') {
			fetchOptions.body = JSON.stringify(payload);
		} else if (content_type === 'application/xml' || content_type === 'text/plain') {
			fetchOptions.body = typeof payload === 'string' ? payload : '';
		} else if (content_type === 'multipart/form-data') {
			const form = new FormData();
			Object.entries(payload || {}).forEach(([key, value]) => {
				if (typeof value === 'string' || isBlob(value)) {
					form.append(key, value);
				} else {
					form.append(key, JSON.stringify(value));
				}
			});
			fetchOptions.body = form;
			delete combinedHeaders['Content-Type']; // Let FormData handle this
		}
	}

	return fetchOptions;
}

function decodeBase64File(base64: string, name: string, type: string): File {
	const byteString = atob(base64.split(',')[1]);
	const arrayBuffer = new Uint8Array(byteString.length);
	for (let i = 0; i < byteString.length; i++) {
		arrayBuffer[i] = byteString.charCodeAt(i);
	}
	const blob = new Blob([arrayBuffer], { type });
	return new File([blob], name, { type });
}

async function getSubmissionFetchOptions(row: DbApiSubmissionType): Promise<RequestInit> {
	if (row.content_type === 'application/json') {
		return {
			method: row.method,
			body: JSON.stringify(row.payload),
			headers: {
				'Content-Type': 'application/json',
			},
			credentials: 'include',
		};
	}

	if (row.content_type === 'multipart/form-data') {
		const form = new FormData();
		form.append('submission_xml', row.payload.form.submission_xml);

		for (const f of row.payload.form.submission_files) {
			const file = decodeBase64File(f.base64, f.name, f.type);
			form.append('submission_files', file);
		}

		return {
			method: row.method,
			body: form,
			credentials: 'include',
		};
	}

	throw new Error(`Unsupported content_type: ${row.content_type}`);
}

export {
	fetchCachedBlobUrl,
	fetchBlobUrl,
	fetchFormMediBlobUrls,
	sendNextQueuedSubmissionToApi,
	getSubmissionFetchOptions,
};
