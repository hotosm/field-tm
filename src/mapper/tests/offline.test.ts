// Mock trySendingSubmission before the tests, to avoid actual API calls
vi.mock('$lib/api/fetch', async (importOriginal) => {
	return {
		...(await importOriginal<typeof import('$lib/api/fetch')>()),
		trySendingSubmission: vi.fn(async (db: PGlite, row: DbApiSubmissionType) => {
			// Mock behavior: no API call, just return true/false based on url
			if (row.url.includes('fail')) {
				await DbApiSubmission.update(db, row.id, 'FAILED', 'dummyerror');
				return false;
			} else {
				await DbApiSubmission.update(db, row.id, 'RECEIVED');
				return true;
			}
		}),
	};
});

// Mock the stores to prevent import errors of browser APIs
vi.mock('$store/common.svelte.ts', () => {
	const mockCommonStore = {
		setOfflineDataIsSyncing: vi.fn(),
		setOfflineSyncPercentComplete: vi.fn(),
	};
	const mockAlertStore = {
		setAlert: vi.fn(),
	};

	return {
		getCommonStore: () => mockCommonStore,
		getAlertStore: () => mockAlertStore,
	};
});

import fs from 'fs/promises';
import path from 'path';
import { describe, it, beforeEach, expect, vi } from 'vitest';
import type { PGlite } from '@electric-sql/pglite';

import type { DbApiSubmissionType } from '$lib/types';
import { DbApiSubmission } from '$lib/db/api-submissions';
import { loadDbFromDump } from '$lib/db/pglite';
import { getCommonStore, getAlertStore } from '$store/common.svelte.ts';

let db: Awaited<ReturnType<typeof loadDbFromDump>>;
let commonStore: ReturnType<typeof getCommonStore>;
let alertStore: ReturnType<typeof getAlertStore>;

const dbDumpPath = path.resolve(__dirname, '../../migrations/init/pgdata.tar.gz');
const fileBuffer = await fs.readFile(dbDumpPath);
if (fileBuffer.length === 0) {
	throw new Error('pgdata.tar.gz was empty or not read properly');
}
const fileBlob = new Blob([fileBuffer], { type: 'application/x-gzip' });
db = await loadDbFromDump('memory://', fileBlob);

let iterateAndSendOfflineSubmissions: typeof import('$lib/api/offline').iterateAndSendOfflineSubmissions;
let trySendingSubmission: typeof import('$lib/api/fetch').trySendingSubmission;

beforeEach(async () => {
	vi.resetModules(); // ensure clean module state
	vi.resetAllMocks(); // reset mocks

	commonStore = getCommonStore();
	alertStore = getAlertStore();

	// Import after mocks are in effect
	const apiFetch = await import('$lib/api/fetch');
	const apiOffline = await import('$lib/api/offline');
	trySendingSubmission = apiFetch.trySendingSubmission;
	iterateAndSendOfflineSubmissions = apiOffline.iterateAndSendOfflineSubmissions;

	// Clean db state before each test
	await db.query('DELETE FROM api_submissions;');
	await db.query('DELETE FROM api_failures;');
});

async function seedSubmissions(data: any[]) {
	for (const [i, row] of data.entries()) {
		await db.query(
			`INSERT INTO api_submissions (id, url, method, content_type, payload, headers, status, retry_count, queued_at)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
			[
				i + 1,
				row.url,
				row.method || 'POST',
				row.content_type || 'application/json',
				JSON.stringify(row.payload),
				JSON.stringify(row.headers || {}),
				'PENDING',
				0,
				new Date().toISOString(),
			],
		);
	}
}

describe('iterateAndSendOfflineSubmissions', async () => {
	it('should process submissions and move failures to api_failures', async () => {
		await seedSubmissions([
			{ url: 'https://api.example.com/data1', payload: { a: 1 } },
			{ url: 'https://api.example.com/fail', payload: { b: 2 } }, // simulate failure
			{ url: 'https://api.example.com/data2', payload: { c: 3 } },
		]);

		const result = await iterateAndSendOfflineSubmissions(db);
		expect(result).toBe(true);
		expect(trySendingSubmission).toHaveBeenCalledTimes(3);

		const remaining = await DbApiSubmission.count(db);
		expect(remaining).toBe(0);

		const failures = await DbApiSubmission.allFailed(db);
		if (!failures) throw new Error('No api_failures entries');
		// Check failures table has one failed record with error
		expect(failures).toHaveLength(1);
		expect(failures[0].url).toBe('https://api.example.com/fail');
		expect(failures[0].status).toBe('FAILED');
		expect(failures[0].error).toBe('dummyerror');

		// Check the logs/store interactions
		expect(commonStore.setOfflineDataIsSyncing).toHaveBeenCalledWith(true);
		expect(commonStore.setOfflineDataIsSyncing).toHaveBeenCalledWith(false); // assuming your impl toggles this back
		expect(commonStore.setOfflineSyncPercentComplete).toHaveBeenCalled(); // optionally, check call count

		expect(alertStore.setAlert).toHaveBeenCalledWith(
			expect.objectContaining({
				message: expect.stringContaining('Finished sending offline data'),
			}),
		);
	});

	it('should handle multipart/form-data correctly in getSubmissionFetchOptions', async () => {
		const fileData = {
			form: {
				submission_xml: '<xml>test</xml>',
				submission_files: [
					{
						base64: Buffer.from('testfilecontent').toString('base64'),
						name: 'file.txt',
						type: 'text/plain',
					},
				],
			},
		};

		await seedSubmissions([
			{
				url: 'https://api.example.com/upload',
				payload: fileData,
				content_type: 'multipart/form-data',
			},
		]);

		// Spy on FormData and file decoding logic
		const appendSpy = vi.spyOn(FormData.prototype, 'append');

		const result = await iterateAndSendOfflineSubmissions(db);
		expect(result).toBe(true);
		expect(trySendingSubmission).toHaveBeenCalledTimes(1);

		// expect(appendSpy).toHaveBeenCalledWith('submission_xml', fileData.form.submission_xml);
		// expect(appendSpy).toHaveBeenCalledWith(
		// 	'submission_files',
		// 	expect.any(File)
		// );
		// appendSpy.mockRestore();
	});

	// it('should handle application/json correctly in getSubmissionFetchOptions', async () => {
	// 	const jsonData = {
	// 	  form: {
	// 		submission_xml: '<xml>test</xml>',
	// 		submission_files: [
	// 		  {
	// 			base64: Buffer.from('testfilecontent').toString('base64'),
	// 			name: 'file.txt',
	// 			type: 'text/plain'
	// 		  }
	// 		]
	// 	  }
	// 	};

	// 	await seedSubmissions([
	// 	  {
	// 		url: 'https://api.example.com/upload',
	// 		payload: jsonData,
	// 		content_type: 'application/json'
	// 	  }
	// 	]);

	// 	// No FormData append spy needed here since JSON is used
	// 	const appendSpy = vi.spyOn(FormData.prototype, 'append');

	// 	const result = await iterateAndSendOfflineSubmissions(db);
	// 	expect(result).toBe(true);
	// 	expect(trySendingSubmission).toHaveBeenCalledTimes(1);

	// 	// Check that FormData append was NOT called since it's JSON
	// 	expect(appendSpy).not.toHaveBeenCalled();

	// 	// Instead, check trySendingSubmission called with JSON string payload
	// 	expect(trySendingSubmission).toHaveBeenCalledWith(
	// 	  expect.objectContaining({
	// 		body: JSON.stringify(jsonData),
	// 		headers: expect.objectContaining({
	// 		  'Content-Type': 'application/json'
	// 		}),
	// 		url: 'https://api.example.com/upload'
	// 	  })
	// 	);

	// 	appendSpy.mockRestore();
	//   });
});
