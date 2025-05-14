import { PGlite } from '@electric-sql/pglite';
import type { projectType, DbProject } from '$lib/types';
import { DB_PROJECT_COLUMNS } from '$lib/types';

export async function fetchProjectFromLocalDB(db: PGlite, projectId: string): Promise<projectType | undefined> {
	if (!db) return;

	const response = await db.query(`SELECT * FROM projects WHERE id = $1;`, [projectId]);
	const localProject = response.rows.at(-1) ?? null;
	return localProject;
}

export async function upsertLocalDbProjectData(db: PGlite, projectData: Partial<DbProject>): Promise<void> {
	if (!db || !projectData || !projectData.id) return;

	// Filter keys to only include those present in the actual DB schema
	const columns = Object.keys(projectData).filter((key) => DB_PROJECT_COLUMNS.has(key));
	if (columns.length === 0) return;

	const placeholders = columns.map((_, i) => `$${i + 1}`).join(', ');
	const values = columns.map((key) => projectData[key as keyof DbProject]);

	const updateClause = columns
		.filter((col) => col !== 'id') // Don't update ID
		.map((col, i) => `${col} = excluded.${col}`)
		.join(', ');

	const sql = `
		INSERT INTO projects (${columns.join(', ')})
		VALUES (${placeholders})
		ON CONFLICT(id) DO UPDATE SET ${updateClause};
	`;

	await db.query(sql, values);
}
