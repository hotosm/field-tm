import type { PGlite } from '@electric-sql/pglite';
import type { DbApiSubmissionType } from '$lib/types.ts';
import { DbApiSubmission } from '$lib/db/api-submissions.ts';

const API_URL = import.meta.env.VITE_API_URL;

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

async function trySendingSubmission(db: PGlite, row: DbApiSubmissionType): Promise<boolean> {
	try {
		const options = await getSubmissionFetchOptions(row);
		const res = await fetch(row.url, options);

		if (!res.ok) throw new Error(`HTTP ${res.status}`);

		await DbApiSubmission.update(db, row.id, 'RECEIVED');
		return true;
	} catch (err) {
		console.error('Offline send failed:', err);
		await DbApiSubmission.update(db, row.id, 'FAILED', String(err));
		return false;
	}
}

export { fetchBlobUrl, fetchFormMediBlobUrls, trySendingSubmission };
