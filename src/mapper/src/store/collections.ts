import * as z from 'zod';
import { createCollection } from '@tanstack/svelte-db';
import type { Collection } from '@tanstack/svelte-db';
import { electricCollectionOptions } from '@tanstack/electric-db-collection';
import type { FeatureCollection } from 'geojson';

import { EntityStatusNameMap, TaskEventEnum, TaskStatusEnum } from '$lib/types';
import { api } from '$lib/api';
import { javarosaToGeojsonGeom } from '$lib/odk/javarosa';

export const OdkEntity = z.object({
	entity_id: z.string,
	status: z.enum(EntityStatusNameMap),
	project_id: z.number,
	task_id: z.number,
	osm_id: z.string, // we convert bigint --> string for frontend usage
	submission_ids: z.string,
	geometry: z.string().nullish(),
	created_by: z.string().nullish(),
});
export type OdkEntity = z.infer<typeof OdkEntity>;

export const TaskEvent = z.object({
	event_id: z.string,
	event: z.enum(TaskEventEnum),
	task_id: z.number,
	comment: z.string().nullish(),
	created_at: z.string,
	username: z.string,
	profile_img: z.string,
	status: z.enum(TaskStatusEnum),
});
export type TaskEvent = z.infer<typeof TaskEvent>;

export async function getEntitiesCollection(projectId: string): Promise<Collection> {
	return createCollection(
		electricCollectionOptions({
			id: `entities`,
			shapeOptions: {
				url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
				params: {
					table: 'odk_entities',
					where: `project_id=${projectId}`,
				},
				parser: {
					osm_id: (value: unknown) => (value as bigint).toString(),
				},
			},
			getKey: (item) => item.entity_id,
			schema: OdkEntity,
			onInsert: async ({ transaction }) => {
				const { entity_id: _id, ...modified } = transaction.mutations[0].modified;
				const response = await api.entities.create(modified);
				return { txid: response.txid };
			},
			// TODO need to send an entity object via PATCH instead of featcol
			onUpdate: async ({ transaction }) => {
				const txids = await Promise.all(
					transaction.mutations.map(async (mutation) => {
						const { original, changes } = mutation;
						const response = await api.entities.update(String(original.project_id), changes);
						return response.txid;
					}),
				);
				return { txid: txids };
			},
			onDelete: async ({ transaction }) => {
				const txids = await Promise.all(
					transaction.mutations.map(async (mutation) => {
						const { original } = mutation;
						const response = await api.entities.delete(String(original.project_id), String(original.entity_id));
						return response.txid;
					}),
				);
				return { txid: txids };
			},
		}),
	);
}

export async function getTaskEventsCollection(projectId: string): Promise<Collection> {
	return createCollection(
		electricCollectionOptions({
			id: `task_events`,
			shapeOptions: {
				url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
				params: {
					table: 'task_events',
					where: `project_id=${projectId}`,
				},
			},
			getKey: (item) => item.event_id,
			schema: TaskEvent,
			onInsert: async ({ transaction }) => {
				const { event_id: _id, ...modified } = transaction.mutations[0].modified;
				const response = await api.events.create(modified);
				return { txid: response.txid };
			},
		}),
	);
}

export function entityDataToFeatureCollection(entities: OdkEntity[]): FeatureCollection {
	return {
		type: 'FeatureCollection',
		features: entities.map((entity: OdkEntity) => {
			if (!entity.geometry) return null;
			const geometry = javarosaToGeojsonGeom(entity.geometry);
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
		}),
	};
}
