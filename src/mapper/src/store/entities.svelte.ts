import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData } from '@electric-sql/client';
import type { FeatureCollection } from 'geojson';
import type { UUID } from 'crypto';
import type { LngLatLike } from 'svelte-maplibre';

import type { DbEntityType, EntityStatusPayload, entitiesApiResponse, entityStatusOptions } from '$lib/types';
import { EntityStatusNameMap } from '$lib/types';
import { getAlertStore } from './common.svelte';
import { javarosaToGeojsonGeom } from '$lib/odk/javarosa';

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
// Map each entity_id to the entity data, for faster lookup in map
let entityMap = $derived(new Map(entitiesList.map((entity) => [entity.entity_id, entity])));
let selectedEntity: DbEntityType | null = $derived(entityMap.get(selectedEntityId || '') ?? null);

// Derive new and bad geoms to display as an overlay
let badGeomFeatcol: FeatureCollection = $derived({
	type: 'FeatureCollection',
	features: entitiesList
		.filter((e) => e.status === 'MARKED_BAD')
		.map(entityDataToGeojsonFeature)
		.filter(Boolean),
});
let newGeomFeatcol: FeatureCollection = $derived({
	type: 'FeatureCollection',
	features: entitiesList
		.filter((e) => e.created_by !== '')
		.map(entityDataToGeojsonFeature)
		.filter(Boolean),
});

const alertStore = getAlertStore();

let syncEntityStatusManuallyLoading: boolean = $state(false);
let updateEntityStatusLoading: boolean = $state(false);
let selectedEntityCoordinate: entityIdCoordinateMapType | null = $state(null);
let entityToNavigate: entityIdCoordinateMapType | null = $state(null);
let toggleGeolocation: boolean = $state(false);
let taskSubmissionInfo: taskSubmissionInfoType[] = $state([]);
let fgbOpfsUrl: string = $state('');
let selectedEntityJavaRosaGeom: string | null = $state(null);

function entityDataToGeojsonFeature(entity: DbEntityType): Feature | null {
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
			// BigInt doesn't work with svelte-maplibre layers, so we revert to string
			osm_id: entity.osm_id.toString(),
			submission_ids: entity.submission_ids,
			created_by: entity.created_by,
		},
	};
}

function getEntitiesStatusStore() {
	async function startEntityStatusStream(projectId: number): Promise<ShapeStream | undefined> {
		if (!projectId) {
			return;
		}

		const entitiesStream = new ShapeStream({
			url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
			params: {
				table: 'odk_entities',
				where: `project_id=${projectId}`,
			},
		});
		const entitiesShape = new Shape(entitiesStream);

		entitiesUnsubscribe = entitiesShape?.subscribe(async (entityData: ShapeData[]) => {
			// Here we merge new rows from electric with existing entity records
			// preserving any existing entity properties not included in the ShapeStream
			const entityMapClone = new Map(entitiesList.map((e) => [e.entity_id, e]));

			// Append entity_id to data
			for (const entity of entityData.rows) {
				const updatedEntity = {
					...(entityMapClone.get(entity.entity_id) || {}),
					...entity,
				};
				entityMapClone.set(entity.entity_id, updatedEntity);
			}

			entitiesList = Array.from(entityMapClone.values());
			_calculateTaskSubmissionCounts();
		});
	}

	function unsubscribeEntitiesStream() {
		if (entitiesUnsubscribe) {
			entitiesUnsubscribe();
			entitiesUnsubscribe = null;
		}
	}

	function addStatusToGeojsonProperty(geojsonData: FeatureCollection): FeatureCollection {
		return {
			...geojsonData,
			features: geojsonData.features.map((feature) => {
				// Must convert number type from fgb number --> bigint for comparison
				const entity = getEntityByOsmId(BigInt(feature?.properties?.osm_id));
				return {
					...feature,
					properties: {
						...feature.properties,
						status: entity?.status,
						entity_id: entity?.entity_id,
						submission_ids: entity?.submission_ids,
						// BigInt doesn't work with svelte-maplibre layers, so we revert to string
						osm_id: entity?.osm_id.toString(),
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

	// Manually sync the entity status via button
	async function syncEntityStatusManually(projectId: number) {
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

			// Replace in-memory list from store entirely (refresh)
			entitiesList = newEntitiesList;
			_calculateTaskSubmissionCounts();
		} catch (error) {
			syncEntityStatusManuallyLoading = false;
		}
	}

	async function updateEntityStatus(projectId: number, payload: EntityStatusPayload) {
		const entityRequestUrl = `${API_URL}/projects/${projectId}/entity/status`;
		const entityRequestMethod = 'POST';
		const entityRequestPayload = JSON.stringify(payload);
		const entityRequestContentType = 'application/json';

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
	}

	async function createEntity(projectId: number, entityUuid: UUID, featcol: FeatureCollection) {
		const entityRequestUrl = `${API_URL}/central/entity?project_id=${projectId}&entity_uuid=${entityUuid}`;
		const entityRequestMethod = 'POST';
		const entityRequestPayload = JSON.stringify(featcol);
		const entityRequestContentType = 'application/json';

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
	}

	async function createNewSubmission(projectId: number, submissionXml: string, attachments: File[]) {
		const entityRequestUrl = `${API_URL}/submission?project_id=${projectId}`;
		const entityRequestMethod = 'POST';

		const form = new FormData();

		// Upload XML as a file (Blob), not a raw string (reduce memory usage)
		const xmlBlob = new Blob([submissionXml], { type: 'text/xml' });
		form.append('submission_xml', xmlBlob, 'submission.xml');

		attachments.forEach((file) => {
			form.append('submission_files', file);
		});

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
	}

	async function deleteNewEntity(project_id: number, entity_id: string) {
		try {
			const geomDeleteResponse = await fetch(`${API_URL}/projects/entity/${entity_id}?project_id=${project_id}`, {
				method: 'DELETE',
				credentials: 'include',
			});

			if (geomDeleteResponse.ok) {
				syncEntityStatusManually(project_id);
			} else {
				throw new Error('Failed to delete geometry');
			}
		} catch (error: any) {
			alertStore.setAlert({
				variant: 'danger',
				message: error.message,
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

	function getEntityByOsmId(osmId: bigint): DbEntityType | undefined {
		return entitiesList.find((entity) => entity.osm_id === osmId);
	}

	function getOsmIdByEntityId(entityId: string): number | undefined {
		return entityMap.get(entityId)?.osm_id;
	}

	function setFgbOpfsUrl(url: string) {
		fgbOpfsUrl = url;
	}

	function setSelectedEntityJavaRosaGeom(geom: string | null) {
		selectedEntityJavaRosaGeom = geom;
	}

	return {
		startEntityStatusStream: startEntityStatusStream,
		unsubscribeEntitiesStream: unsubscribeEntitiesStream,
		syncEntityStatusManually: syncEntityStatusManually,
		addStatusToGeojsonProperty: addStatusToGeojsonProperty,
		createEntity: createEntity,
		deleteNewEntity: deleteNewEntity,
		updateEntityStatus: updateEntityStatus,
		createNewSubmission: createNewSubmission,
		setEntityToNavigate: setEntityToNavigate,
		setToggleGeolocation: setToggleGeolocation,
		setUserLocationCoordinate: setUserLocationCoordinate,
		setFgbOpfsUrl: setFgbOpfsUrl,
		setSelectedEntityJavaRosaGeom: setSelectedEntityJavaRosaGeom,
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
		get selectedEntityJavaRosaGeom() {
			return selectedEntityJavaRosaGeom;
		},
	};
}

export { getEntitiesStatusStore };
