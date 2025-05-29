import type { PGlite } from '@electric-sql/pglite';
import type { PGliteWithSync } from '@electric-sql/pglite-sync';
import type { ShapeStream, FetchError } from '@electric-sql/client';
import type { ShapeData } from '@electric-sql/client';
import { online } from 'svelte/reactivity/window';
import type { FeatureCollection } from 'geojson';
import type { UUID } from 'crypto';
import type { LngLatLike } from 'svelte-maplibre';

import type { DbEntityType, EntityStatusPayload, entitiesApiResponse, entityStatusOptions } from '$lib/types';
import { EntityStatusNameMap } from '$lib/types';
import { getAlertStore } from './common.svelte';
import { DbEntity } from '$lib/db/entities';
import { DbApiSubmission } from '$lib/db/api-submissions';
import { geojsonGeomToJavarosa } from '$lib/odk/javarosa';

const API_URL = import.meta.env.VITE_API_URL;

type entityIdCoordinateMapType = {
	entityId: string;
	coordinate: [number, number];
};

type taskSubmissionInfoType = {
	task_id: number;
	index: number;
	submission_count: number;
	feature_count: number;
};

let entitiesUnsubscribe: (() => void) | null = $state(null);
let userLocationCoord: LngLatLike | undefined = $state();
let selectedEntityId: string | null = $state(null);
let entitiesList: DbEntityType[] = $state([]);
let selectedEntity: DbEntityType | null = $derived(
	entitiesList.find((entity) => entity.entity_id === selectedEntityId) ?? null,
);
// Map each entity_id to the entity data, for faster lookup in map
let entityMap = $derived(new Map(entitiesList.map((entity) => [entity.entity_id, entity])));

// Derive new and bad geoms to display as an overlay
let badGeomFeatcol: FeatureCollection = $derived({
	type: 'FeatureCollection',
	features: entitiesList
		.filter((e) => e.status === 'MARKED_BAD')
		.map(DbEntity.toGeojsonFeature)
		.filter(Boolean),
});
let newGeomFeatcol: FeatureCollection = $derived({
	type: 'FeatureCollection',
	features: entitiesList
		.filter((e) => e.created_by !== '')
		.map(DbEntity.toGeojsonFeature)
		.filter(Boolean),
});

let syncEntityStatusManuallyLoading: boolean = $state(false);
let updateEntityStatusLoading: boolean = $state(false);
let selectedEntityCoordinate: entityIdCoordinateMapType | null = $state(null);
let entityToNavigate: entityIdCoordinateMapType | null = $state(null);
let toggleGeolocation: boolean = $state(false);
let taskSubmissionInfo: taskSubmissionInfoType[] = $state([]);
let alertStore = getAlertStore();
let entitiesSync: any = $state(undefined);
let fgbOpfsUrl: string = $state('');
let geomDeleteLoading: boolean = $state(false);

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
		await setEntitiesListFromDbRecords(db, projectId);
		_calculateTaskSubmissionCounts();

		entitiesUnsubscribe = entitiesSync?.stream.subscribe(
			async (entities: ShapeData[]) => {
				// Create map for faster lookup
				const rows: DbEntityType[] = entities
					.filter((item): item is { value: DbEntityType } => 'value' in item && item.value !== null)
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
					await DbEntity.update(db, entity);
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

	async function setEntitiesListFromDbRecords(db: PGliteWithSync, projectId: number) {
		const dbEntities = await db.query(`SELECT * FROM odk_entities WHERE project_id = $1;`, [projectId]);
		entitiesList = dbEntities.rows.map((entity: DbEntityType) => ({
			entity_id: entity.entity_id,
			status: entity.status,
			project_id: projectId,
			task_id: entity.task_id,
			osm_id: entity.osm_id,
			submission_ids: entity.submission_ids,
			geometry: entity.geometry,
			created_by: entity.created_by,
		}));
	}

	function addStatusToGeojsonProperty(geojsonData: FeatureCollection): FeatureCollection {
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
						// osm_id is BigInt, which doesn't work with svelte-maplibre layers
						osm_id: feature?.properties?.osm_id.toString(),
					},
				};
			}),
		};
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

		const taskEntityMap = entitiesList?.reduce((acc: Record<number, DbEntityType[]>, item) => {
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
	async function syncEntityStatusManually(db: PGlite, projectId: number) {
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
			const newEntitiesList: DbEntityType[] = responseJson.map((entity: entitiesApiResponse) => ({
				entity_id: entity.id,
				status: EntityStatusNameMap[entity.status],
				project_id: projectId,
				task_id: entity.task_id,
				submission_ids: entity.submission_ids,
				osm_id: entity.osm_id,
				geometry: entity.geometry,
				created_by: entity.created_by,
			}));
			syncEntityStatusManuallyLoading = false;

			// Replace in-memory list from store
			entitiesList = newEntitiesList;

			// Clear odk_entities table first in local db, then re-add data
			await db.query(`DELETE FROM odk_entities WHERE project_id = $1;`, [projectId]);
			await DbEntity.bulkCreate(db, newEntitiesList);
			_calculateTaskSubmissionCounts();
		} catch (error) {
			syncEntityStatusManuallyLoading = false;
		}
	}

	async function updateEntityStatus(db: PGlite, projectId: number, payload: EntityStatusPayload) {
		const entityRequestUrl = `${API_URL}/projects/${projectId}/entity/status`;
		const entityRequestMethod = 'POST';
		const entityRequestPayload = JSON.stringify(payload);
		const entityRequestContentType = 'application/json';

		if (online.current) {
			try {
				updateEntityStatusLoading = true;
				const resp = await fetch(entityRequestUrl, {
					method: entityRequestMethod,
					body: entityRequestPayload,
					headers: {
						'Content-type': entityRequestContentType,
					},
					credentials: 'include',
				});
				if (!resp.ok) {
					const errorData = await resp.json();
					throw new Error(errorData.detail);
				}
				updateEntityStatusLoading = false;
			} catch (error: any) {
				updateEntityStatusLoading = false;
				alertStore.setAlert({
					variant: 'danger',
					message: error.message || 'Failed to update entity',
				});
				throw new Error(error);
			}
		} else {
			// Save for later submission + add entity update to local db
			await DbApiSubmission.create(db, {
				url: entityRequestUrl,
				method: entityRequestMethod,
				content_type: entityRequestContentType,
				payload: entityRequestPayload,
			});

			// Update entity in localdb
			await DbEntity.update(db, {
				entity_id: payload.entity_id,
				status: EntityStatusNameMap[payload.status],
			});
			// Reuse function to get records from db and set svelte store
			await setEntitiesListFromDbRecords(db, projectId);
		}
	}

	async function createEntity(db: PGlite, projectId: number, entityUuid: UUID, featcol: FeatureCollection) {
		const entityRequestUrl = `${API_URL}/central/entity?project_id=${projectId}&entity_uuid=${entityUuid}`;
		const entityRequestMethod = 'POST';
		const entityRequestPayload = JSON.stringify(featcol);
		const entityRequestContentType = 'application/json';

		if (online.current) {
			try {
				const resp = await fetch(entityRequestUrl, {
					method: entityRequestMethod,
					body: entityRequestPayload,
					headers: {
						'Content-type': entityRequestContentType,
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
					message: error.message || 'Failed to create entity',
				});
				throw new Error(error);
			}
		} else {
			const javarosaGeom = geojsonGeomToJavarosa(featcol.features[0].geometry);
			if (!javarosaGeom) {
				throw Error('Could not convert geometry.');
			}

			// Save for later submission + add entity entry to local db
			await DbApiSubmission.create(db, {
				url: entityRequestUrl,
				method: entityRequestMethod,
				content_type: entityRequestContentType,
				payload: entityRequestPayload,
			});

			// Add to localdb
			await DbEntity.create(db, {
				entity_id: entityUuid.toString(),
				status: 'READY',
				project_id: projectId,
				task_id: featcol.features[0].properties?.task_id,
				submission_ids: '',
				osm_id: featcol.features[0].properties?.osm_id,
				geometry: javarosaGeom,
				created_by: featcol.features[0].properties?.created_by,
			});
			// Reuse function to get records from db and set svelte store
			await setEntitiesListFromDbRecords(db, projectId);
		}
	}

	function _fileToBase64(file: File): Promise<string> {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(reader.result as string);
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	}

	async function createNewSubmission(db: PGlite, projectId: number, submissionXml: string, attachments: File[]) {
		const entityRequestUrl = `${API_URL}/submission?project_id=${projectId}`;
		const entityRequestMethod = 'POST';
		const entityRequestContentType = 'multipart/form-data';

		const form = new FormData();
		form.append('submission_xml', submissionXml);
		attachments.forEach((file) => {
			form.append('submission_files', file);
		});

		if (online.current) {
			try {
				const resp = await fetch(entityRequestUrl, {
					method: entityRequestMethod,
					body: form,
					credentials: 'include',
				});
				if (!resp.ok) {
					const errorData = await resp.json();
					throw new Error(errorData.detail);
				}
			} catch (error: any) {
				alertStore.setAlert({
					variant: 'danger',
					message: error.message || 'Failed to submit',
				});
				throw new Error(error);
			}
		} else {
			// Save for offline sync
			const submissionFilesPayload = await Promise.all(
				attachments.map(async (file) => {
					const base64 = await _fileToBase64(file);
					return {
						name: file.name,
						type: file.type,
						base64,
					};
				}),
			);

			await DbApiSubmission.create(db, {
				url: entityRequestUrl,
				method: entityRequestMethod,
				content_type: entityRequestContentType,
				payload: {
					form: {
						submission_xml: submissionXml,
						submission_files: submissionFilesPayload,
					},
				},
			});
		}
	}

	async function deleteNewEntity(project_id: number, entity_id: string, geom_id: string) {
		try {
			geomDeleteLoading = true;
			// delete entity from central
			// await fetch(`${API_URL}/central/entity/${entity_id}?project_id=${project_id}`, {
			// 	method: 'DELETE',
			// 	credentials: 'include',
			// });

			// delete from geomlog table
			const geomDeleteResponse = await fetch(`${API_URL}/projects/${project_id}/geometry/records/${geom_id}`, {
				method: 'DELETE',
				credentials: 'include',
			});

			if (!geomDeleteResponse.ok) {
				throw new Error('Failed to delete geometry');
			}
		} catch (error: any) {
			alertStore.setAlert({
				variant: 'danger',
				message: error.message,
			});
		} finally {
			geomDeleteLoading = false;
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

	function getEntityByOsmId(osmId: number): DbEntityType | undefined {
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
		createEntity: createEntity,
		updateEntityStatus: updateEntityStatus,
		createNewSubmission: createNewSubmission,
		deleteNewEntity: deleteNewEntity,
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

export { getEntitiesStatusStore };
