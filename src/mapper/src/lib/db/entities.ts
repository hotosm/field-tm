import type { PGlite } from '@electric-sql/pglite';
import type { Feature } from 'geojson';

import type { DbEntityType } from '$lib/types';
import { applyDataToTableWithCsvCopy } from '$lib/db/helpers';
import { javarosaToGeojsonGeom } from '$lib/odk/javarosa';

async function update(db: PGlite, entity: Partial<DbEntityType>) {
	await db.query(
		`UPDATE odk_entities
         SET status = $2, submission_ids = $3
         WHERE entity_id = $1`,
		[entity.entity_id, entity.status, entity.submission_ids],
	);
}

async function create(db: PGlite, entity: DbEntityType) {
	// Note if we are creating a single entity in the local db, it will always include
	// the geometry field as it is a newgeom or badgeom record.
	await db.query(
		`INSERT INTO odk_entities (
            entity_id,
            status,
            project_id,
            task_id,
            submission_ids,
            osm_id,
			geometry,
			created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
		[
			entity.entity_id,
			entity.status,
			entity.project_id,
			entity.task_id,
			entity.submission_ids,
			entity.osm_id,
			entity.geometry,
			entity.created_by,
		],
	);
}

// An optimised insert for multiple geom records in bulk
async function bulkCreate(db: PGlite, entities: DbEntityType[]) {
	// The entities are already in Record format, however we ensure all undefined or empty strings are set to null for insert
	const dataObj = entities.map((entity) => ({
		entity_id: entity.entity_id,
		status: entity.status,
		project_id: entity.project_id,
		task_id: entity.task_id,
		osm_id: entity.osm_id,
		submission_ids: entity.submission_ids === '' ? null : entity.submission_ids,
		geometry: entity.geometry === '' ? null : entity.geometry,
		created_by: entity.created_by,
	}));

	await applyDataToTableWithCsvCopy(db, 'odk_entities', dataObj);
}

// Convert a DbEntity entry to a GeoJSON Feature
function toGeojsonFeature(entity: DbEntityType): Feature | null {
	const geometry = javarosaToGeojsonGeom(entity.geometry);
	if (!geometry) return null;

	return {
		type: 'Feature',
		geometry,
		properties: {
			entity_id: entity.entity_id,
			status: entity.status,
			project_id: entity.project_id,
			task_id: entity.task_id,
			osm_id: entity.osm_id,
			submission_ids: entity.submission_ids,
			created_by: entity.created_by,
		},
	};
}

export const DbEntity = {
	create,
	update,
	bulkCreate,
	toGeojsonFeature,
};
