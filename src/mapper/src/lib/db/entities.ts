import type { PGliteWithSync } from '@electric-sql/pglite-sync';
import type { DbEntity } from '$lib/types';
import { applyDataToTableWithCsvCopy } from '$lib/db/helpers';

export async function updateLocalEntityStatus(db: PGliteWithSync, entity: DbEntity) {
	await db.query(
		`UPDATE odk_entities
         SET status = $2
         WHERE entity_id = $1`,
		[entity.entity_id, entity.status],
	);
}

export async function createLocalEntity(db: PGliteWithSync, entity: DbEntity) {
	await db.query(
		`INSERT INTO odk_entities (
            entity_id,
            status,
            project_id,
            task_id,
            submission_ids,
            osm_id
        )
        VALUES ($1, $2, $3, $4, $5, $6)`,
		[entity.entity_id, entity.status, entity.project_id, entity.task_id, entity.submission_ids, entity.osm_id],
	);
}

// An optimised insert for multiple geom records in bulk
export async function createLocalEntities(db: PGliteWithSync, entities: DbEntity[]) {
	// The entities are already in Record format, however we ensure all undefined or empty strings are set to null for insert
	const dataObj = entities.map((entity) => ({
		entity_id: entity.entity_id,
		status: entity.status,
		project_id: entity.project_id,
		task_id: entity.task_id,
		osm_id: entity.osm_id,
		submission_ids: entity.submission_ids === '' ? null : entity.submission_ids,
	}));

	await applyDataToTableWithCsvCopy(db, 'odk_entities', dataObj);
}
