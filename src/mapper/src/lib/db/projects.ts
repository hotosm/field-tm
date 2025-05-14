import { PGlite } from '@electric-sql/pglite';
import type { DbProjectType } from '$lib/types';
import { DB_PROJECT_COLUMNS } from '$lib/types';

async function all(db: PGlite): Promise<DbProjectType[] | null> {
	if (!db) return null;

	const query = await db.query(`SELECT * FROM projects;`);
	return (query.rows as DbProjectType[]) ?? [];
}

async function one(db: PGlite, projectId: string): Promise<DbProjectType | undefined> {
	if (!db) return;

	const response = await db.query(`SELECT * FROM projects WHERE id = $1;`, [projectId]);
	return response.rows.at(-1) as DbProjectType | undefined;
}

async function upsert(db: PGlite, projectData: Partial<DbProjectType>): Promise<void> {
	if (!db || !projectData || !projectData.id) return;

	// Filter keys to only include those present in the actual DB schema
	const columns = Object.keys(projectData).filter((key) => DB_PROJECT_COLUMNS.has(key));
	if (columns.length === 0) return;

	const placeholders = columns.map((_, i) => `$${i + 1}`).join(', ');
	const values = columns.map((key) => projectData[key as keyof DbProjectType]);

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

// This isn't super efficient, but as we only insert 12 at a time, it's not terrible
// We want to do this instead of DELETE then bulk COPY, as we don't want to lose the
// project data already loaded if the user went to a project details page.
async function bulkUpsert(db: PGlite, projects: Partial<DbProjectType>[]): Promise<void> {
	if (!db || !projects.length) return;

	for (const project of projects) {
		await DbProject.upsert(db, project);
	}
}

export const DbProject = {
	one,
	all,
	upsert,
	bulkUpsert,
};
