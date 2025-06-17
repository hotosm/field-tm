import type { PGlite } from '@electric-sql/pglite';
import type { DbApiSubmissionType } from '$lib/types.ts';

async function create(
	db: PGlite,
	data: {
		url: string;
		user_sub?: string | undefined;
		method: DbApiSubmissionType['method'];
		content_type?: DbApiSubmissionType['content_type'];
		payload?: any;
		headers?: Record<string, string> | null;
	},
): Promise<DbApiSubmissionType | undefined> {
	if (!db) return;

	const {
		url,
		user_sub = null, // default
		method,
		content_type = 'application/json', // default
		payload = null,
		headers = null,
	} = data;

	const result = await db.query(
		`INSERT INTO api_submissions
			(url, user_sub, method, content_type, payload, headers, status, retry_count, error, queued_at)
		 VALUES
			($1, $2, $3, $4, $5, $6, 'PENDING', 0, NULL, now())
		 RETURNING *`,
		[url, user_sub, method, content_type, payload, headers],
	);

	return result.rows.at(-1) as DbApiSubmissionType | undefined;
}

async function count(db: PGlite): Promise<number> {
	if (!db) return 0;

	const dbData = await db.query(`SELECT COUNT(*) as count FROM api_submissions WHERE status = 'PENDING'`);
	const row = dbData.rows.at(-1) as { count: number } | undefined;
	return row?.count ?? 0;
}

async function next(db: PGlite): Promise<DbApiSubmissionType | undefined> {
	if (!db) return;

	// NOTE we allow 2 retries when calling the API
	const dbData = await db.query<DbApiSubmissionType>(
		`SELECT * FROM api_submissions
		 WHERE status = 'PENDING' OR (status = 'FAILED' AND retry_count < 2)
		 ORDER BY queued_at ASC
		 LIMIT 1`,
	);
	return dbData.rows.at(-1) as DbApiSubmissionType | undefined;
}

async function update(
	db: PGlite,
	id: number,
	status: 'RECEIVED' | 'PENDING' | 'FAILED',
	error: string | null = null,
): Promise<void> {
	if (!db) return;

	await db.query(
		`UPDATE api_submissions
		 SET
			status = $1,
			error = $2,
			last_attempt_at = now(),
			success_at = CASE WHEN $3 = 'RECEIVED' THEN now() ELSE NULL END,
			retry_count = CASE WHEN $4 = 'FAILED' THEN retry_count + 1 ELSE retry_count END
		 WHERE id = $5`,
		// We have to send status as multiple vars, else type inference throws errors
		[status, error, status, status, id],
	);
}

async function deleteById(db: PGlite, id: number): Promise<void> {
	if (!db) return;
	await db.query(`DELETE FROM api_submissions WHERE id = $1;`, [id]);
}

async function allQueued(db: PGlite): Promise<DbApiSubmissionType[] | null> {
	if (!db) return null;

	const query = await db.query(`SELECT * FROM api_submissions;`);
	return (query.rows as DbApiSubmissionType[]) ?? [];
}

async function moveToFailedTable(db: PGlite, id: number): Promise<void> {
	if (!db) return;
	await db.query(
		`INSERT INTO api_failures
		 SELECT * FROM api_submissions
		 WHERE id = $1;`,
		[id],
	);
	await deleteById(db, id);
}

async function allFailed(db: PGlite): Promise<DbApiSubmissionType[] | null> {
	if (!db) return null;

	const query = await db.query(`SELECT * FROM api_failures;`);
	return (query.rows as DbApiSubmissionType[]) ?? [];
}

export const DbApiSubmission = {
	allQueued,
	create,
	update,
	count,
	next,
	deleteById,
	moveToFailedTable,
	allFailed,
};
