import type { PGliteWithSync } from '@electric-sql/pglite-sync';
import type { ShapeStream, FetchError } from '@electric-sql/client';
import type { ShapeData } from '@electric-sql/client';
import type { Feature, FeatureCollection } from 'geojson';
import type { LngLatLike } from 'svelte-maplibre';

import type { DbEntity, EntityStatusPayload, entitiesApiResponse, entityStatusOptions } from '$lib/types';
import { EntityStatusNameMap } from '$lib/types';
import { getAlertStore } from './common.svelte';
import { createLocalEntities, updateLocalEntityStatus } from '$lib/db/entities';

const API_URL = import.meta.env.VITE_API_URL;

type entityIdCoordinateMapType = {
	entityId: string;
	coordinate: [number, number];
};

type newBadGeomType<T> = {
	geojson: Feature;
	id: number;
	project_id: number;
	status: T;
	task_id: number;
};

type taskSubmissionInfoType = {
	task_id: number;
	index: number;
	submission_count: number;
	feature_count: number;
};

let entitiesUnsubscribe: (() => void) | null = $state(null);
let newBadGeomUnsubscribe: (() => void) | null = $state(null);

let userLocationCoord: LngLatLike | undefined = $state();
let selectedEntityId: string | null = $state(null);
let entitiesList: DbEntity[] = $state([]);
let selectedEntity: DbEntity | null = $derived(
	entitiesList.find((entity) => entity.entity_id === selectedEntityId) ?? null,
);
// Map each entity_id to the entity data, for faster lookup in map
let entityMap = $derived(new Map(entitiesList.map((entity) => [entity.entity_id, entity])));

let badGeomFeatcol: FeatureCollection = $state({ type: 'FeatureCollection', features: [] });
let newGeomFeatcol: FeatureCollection = $state({ type: 'FeatureCollection', features: [] });
let syncEntityStatusManuallyLoading: boolean = $state(false);
let updateEntityStatusLoading: boolean = $state(false);
let selectedEntityCoordinate: entityIdCoordinateMapType | null = $state(null);
let entityToNavigate: entityIdCoordinateMapType | null = $state(null);
let toggleGeolocation: boolean = $state(false);
let taskSubmissionInfo: taskSubmissionInfoType[] = $state([]);
let alertStore = getAlertStore();
let entitiesSync: any = $state(undefined);
let newBadGeomSync: any = $state(undefined);
let fgbOpfsUrl: string = $state('');

function getEntitiesStatusStore() {
	async function getEntityStatusStream(db: PGliteWithSync, projectId: number): Promise<ShapeStream | undefined> {
		if (!db || !projectId) {
			return;
		}

		entitiesSync = await db.electric.syncShapeToTable({
			shape: {
				url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
				params: {
					table: 'odk_entities',
					where: `project_id=${projectId}`,
				},
			},
			table: 'odk_entities',
			primaryKey: ['entity_id'],
			shapeKey: 'odk_entities',
			initialInsertMethod: 'csv', // performance boost on initial sync
		});

		// Populate initial entity statuses
		await getInitialEntities(db, projectId);
		_calculateTaskSubmissionCounts();

		entitiesUnsubscribe = entitiesSync?.stream.subscribe(
			async (entities: ShapeData[]) => {
				// Create map for faster lookup
				const rows: DbEntity[] = entities
					.filter((item): item is { value: DbEntity } => 'value' in item && item.value !== null)
					.map((item) => item.value);

				// Map current list for faster lookups
				const entityMapClone = new Map(entitiesList.map((e) => [e.entity_id, e]));

				for (const entity of rows) {
					const updatedEntity = {
						...entityMapClone.get(entity.entity_id), // fallback to existing data
						...entity, // overwrite with new status
					};
					entityMapClone.set(entity.entity_id, updatedEntity);
					// Store value in local db for persistence across restarts
					await updateLocalEntityStatus(db, entity);
				}

				// Set the reactive store var for updates
				entitiesList = Array.from(entityMapClone.values());

				_calculateTaskSubmissionCounts();
			},
			(error: FetchError) => {
				console.error('entity sync error', error);
			},
		);

		return entitiesSync;
	}

	function unsubscribeEntitiesStream() {
		if (entitiesUnsubscribe) {
			entitiesSync?.unsubscribe();
			entitiesUnsubscribe();
			entitiesUnsubscribe = null;
		}
	}

	async function getInitialEntities(db: PGliteWithSync, projectId: number) {
		const dbEntities = await db.query(`SELECT * FROM odk_entities WHERE project_id = $1;`, [projectId]);
		entitiesList = dbEntities.rows.map((entity: DbEntity) => ({
			entity_id: entity.entity_id,
			status: entity.status,
			project_id: projectId,
			task_id: entity.task_id,
			osm_id: entity.osm_id,
			submission_ids: entity.submission_ids,
		}));
	}

	function addStatusToGeojsonProperty(geojsonData: FeatureCollection, entityType: '' | 'new'): FeatureCollection {
		if (entityType === 'new') {
			return {
				...geojsonData,
				features: geojsonData.features.map((feature) => {
					const entity = entityMap.get(feature?.properties?.entity_id);
					return {
						...feature,
						properties: {
							...feature.properties,
							status: entity?.status,
							entity_id: entity?.entity_id,
						},
					};
				}),
			};
		} else {
			return {
				...geojsonData,
				features: geojsonData.features.map((feature) => {
					const entity = getEntityByOsmId(feature?.properties?.osm_id);
					return {
						...feature,
						properties: {
							...feature.properties,
							status: entity?.status,
							entity_id: entity?.entity_id,
						},
					};
				}),
			};
		}
	}

	function _calculateTaskSubmissionCounts() {
		if (!entitiesList) return;

		const StatusToCode: Record<entityStatusOptions, number> = Object.entries(EntityStatusNameMap).reduce(
			(acc, [codeStr, status]) => {
				acc[status] = Number(codeStr);
				return acc;
			},
			{} as Record<entityStatusOptions, number>,
		);

		const taskEntityMap = entitiesList?.reduce((acc: Record<number, DbEntity[]>, item) => {
			if (!acc[item?.task_id]) {
				acc[item.task_id] = [];
			}
			acc[item.task_id].push(item);
			return acc;
		}, {});

		const taskInfo = Object.entries(taskEntityMap).map(([taskId, taskEntities]) => {
			// Calculate feature_count
			const featureCount = taskEntities.length;
			let submissionCount = 0;

			// Calculate submission_count
			taskEntities.forEach((entity) => {
				const statusCode = StatusToCode[entity.status];
				if (statusCode > 1) {
					submissionCount++;
				}
			});

			return {
				task_id: +taskId,
				index: +taskId,
				submission_count: submissionCount,
				feature_count: featureCount,
			};
		});

		// Set submission info in store
		taskSubmissionInfo = taskInfo;
	}

	// Manually sync the entity status via button (if local db gets out of sync with backend)
	async function syncEntityStatusManually(db: PGliteWithSync, projectId: number) {
		try {
			syncEntityStatusManuallyLoading = true;
			const entityStatusResponse = await fetch(`${API_URL}/projects/${projectId}/entities/statuses`, {
				credentials: 'include',
			});
			if (!entityStatusResponse.ok) {
				throw Error('Failed to get entities for project');
			}

			const responseJson: entitiesApiResponse[] = await entityStatusResponse.json();
			// Convert API response into our internal entity shape
			const newEntitiesList: DbEntity[] = responseJson.map((entity: entitiesApiResponse) => ({
				entity_id: entity.id,
				status: EntityStatusNameMap[entity.status],
				project_id: projectId,
				task_id: entity.task_id,
				submission_ids: entity.submission_ids,
				osm_id: entity.osm_id,
			}));
			syncEntityStatusManuallyLoading = false;

			// Replace in-memory list from store
			entitiesList = newEntitiesList;

			// Clear odk_entities table first in local db, then re-add data
			await db.query(`DELETE FROM odk_entities WHERE project_id = $1;`, [projectId]);
			await createLocalEntities(db, newEntitiesList);
			_calculateTaskSubmissionCounts();
		} catch (error) {
			syncEntityStatusManuallyLoading = false;
		}
	}

	async function updateEntityStatus(projectId: number, payload: EntityStatusPayload) {
		try {
			updateEntityStatusLoading = true;
			await fetch(`${API_URL}/projects/${projectId}/entity/status`, {
				method: 'POST',
				body: JSON.stringify(payload),
				headers: {
					'Content-type': 'application/json',
				},
				credentials: 'include',
			});
			updateEntityStatusLoading = false;
		} catch (error) {
			updateEntityStatusLoading = false;
		}
	}

	async function createEntity(projectId: number, payload: FeatureCollection) {
		try {
			const resp = await fetch(`${API_URL}/central/entity?project_id=${projectId}`, {
				method: 'POST',
				body: JSON.stringify(payload),
				headers: {
					'Content-type': 'application/json',
				},
				credentials: 'include',
			});
			if (!resp.ok) {
				const errorData = await resp.json();
				throw new Error(errorData.detail);
			}
			// Response is the ODK Central entity details JSON
			return await resp.json();
		} catch (error: any) {
			alertStore.setAlert({
				variant: 'danger',
				message: error.message || 'Failed to create entity',
			});
		}
	}

	function setEntityToNavigate(entityCoordinate: entityIdCoordinateMapType | null) {
		entityToNavigate = entityCoordinate;
	}

	function setToggleGeolocation(status: boolean) {
		toggleGeolocation = status;
	}

	function setUserLocationCoordinate(coordinate: LngLatLike | undefined) {
		userLocationCoord = coordinate;
	}

	function getEntityByOsmId(osmId: number): DbEntity | undefined {
		return entitiesList.find((entity) => entity.osm_id === osmId);
	}

	function getOsmIdByEntityId(entityId: string): number | undefined {
		return entityMap.get(entityId)?.osm_id;
	}

	function setFgbOpfsUrl(url: string) {
		fgbOpfsUrl = url;
	}

	return {
		getEntityStatusStream: getEntityStatusStream,
		unsubscribeEntitiesStream: unsubscribeEntitiesStream,
		syncEntityStatusManually: syncEntityStatusManually,
		addStatusToGeojsonProperty: addStatusToGeojsonProperty,
		updateEntityStatus: updateEntityStatus,
		createEntity: createEntity,
		setEntityToNavigate: setEntityToNavigate,
		setToggleGeolocation: setToggleGeolocation,
		setUserLocationCoordinate: setUserLocationCoordinate,
		setFgbOpfsUrl: setFgbOpfsUrl,
		get selectedEntityId() {
			return selectedEntityId;
		},
		setSelectedEntityId(clickedEntityId: string | null) {
			selectedEntityId = clickedEntityId;
		},
		get selectedEntity() {
			return selectedEntity;
		},
		get entityMap() {
			return entityMap;
		},
		getEntityByOsmId: getEntityByOsmId,
		getOsmIdByEntityId: getOsmIdByEntityId,
		get badGeomFeatcol() {
			return badGeomFeatcol;
		},
		get newGeomFeatcol() {
			return newGeomFeatcol;
		},
		get syncEntityStatusManuallyLoading() {
			return syncEntityStatusManuallyLoading;
		},
		get updateEntityStatusLoading() {
			return updateEntityStatusLoading;
		},
		get selectedEntityCoordinate() {
			return selectedEntityCoordinate;
		},
		setSelectedEntityCoordinate(newEntityCoordinate: entityIdCoordinateMapType | null) {
			selectedEntityCoordinate = newEntityCoordinate;
		},
		get entityToNavigate() {
			return entityToNavigate;
		},
		get toggleGeolocation() {
			return toggleGeolocation;
		},
		get userLocationCoord() {
			return userLocationCoord;
		},
		get entitiesList() {
			return entitiesList;
		},
		get taskSubmissionInfo() {
			return taskSubmissionInfo;
		},
		get fgbOpfsUrl() {
			return fgbOpfsUrl;
		},
	};
}

function getNewBadGeomStore() {
	async function getNewBadGeomStream(db: PGliteWithSync, projectId: number): Promise<ShapeStream | undefined> {
		if (!db || !projectId) {
			return;
		}

		newBadGeomSync = await db.electric.syncShapeToTable({
			shape: {
				url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
				params: {
					table: 'geometrylog',
					where: `project_id=${projectId}`,
				},
			},
			table: 'geometrylog',
			primaryKey: ['id'],
			shapeKey: 'geometrylog',
			initialInsertMethod: 'csv', // performance boost on initial sync
		});

		// Set initial state of newGeom and badGeom from db
		await getInitialGeomRecords(db, projectId);

		// Append new geoms created to the existing state
		newBadGeomUnsubscribe = newBadGeomSync.stream.subscribe(
			(geoms: ShapeData[]) => {
				const rows: newBadGeomType<'NEW' | 'BAD'>[] = geoms
					.filter((item): item is { value: newBadGeomType<'NEW' | 'BAD'> } => 'value' in item && item.value !== null)
					.map((item) => item.value);

				const badRows = rows.filter((row) => row.status === 'BAD').map((row) => row.geojson);
				const newRows = rows.filter((row) => row.status === 'NEW').map((row) => row.geojson);

				// Append new or bad geom to existing featcol overlay
				badGeomFeatcol = {
					...badGeomFeatcol,
					features: [...badGeomFeatcol.features, ...badRows],
				};
				newGeomFeatcol = {
					...newGeomFeatcol,
					features: [...newGeomFeatcol.features, ...newRows],
				};
			},
			(error: FetchError) => {
				console.error('geom sync error', error);
			},
		);

		return newBadGeomSync;
	}

	function unsubscribeNewBadGeomStream() {
		if (newBadGeomUnsubscribe) {
			newBadGeomSync?.unsubscribe();
			newBadGeomUnsubscribe();
			newBadGeomUnsubscribe = null;
		}
	}

	async function getInitialGeomRecords(db: PGliteWithSync, projectId: number) {
		const dbNewGeoms = await db.query(`SELECT * FROM geometrylog WHERE project_id = $1 AND status = 'NEW';`, [
			projectId,
		]);
		const existingNewGeoms = dbNewGeoms.rows.map((row: newBadGeomType<'NEW'>) => row.geojson);
		newGeomFeatcol = {
			type: 'FeatureCollection',
			features: existingNewGeoms,
		};

		const dbBadGeoms = await db.query(`SELECT * FROM geometrylog WHERE project_id = $1 AND status = 'BAD';`, [
			projectId,
		]);
		const existingBadGeoms = dbBadGeoms.rows.map((row: newBadGeomType<'BAD'>) => row.geojson);
		badGeomFeatcol = {
			type: 'FeatureCollection',
			features: existingBadGeoms,
		};
	}

	async function createGeomRecord(projectId: number, payload: Record<string, any>) {
		try {
			const resp = await fetch(`${API_URL}/projects/${projectId}/geometry/records`, {
				method: 'POST',
				body: JSON.stringify(payload),
				headers: {
					'Content-type': 'application/json',
				},
				credentials: 'include',
			});
			if (!resp.ok) {
				const errorData = await resp.json();
				throw new Error(errorData.detail);
			}
		} catch (error: any) {
			alertStore.setAlert({
				variant: 'danger',
				message: error.message || 'Failed to create geometry record',
			});
		}
	}

	return {
		getNewBadGeomStream: getNewBadGeomStream,
		unsubscribeNewBadGeomStream: unsubscribeNewBadGeomStream,
		createGeomRecord: createGeomRecord,
	};
}

export { getEntitiesStatusStore, getNewBadGeomStore };
