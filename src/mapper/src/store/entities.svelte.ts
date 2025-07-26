import type { Collection, UseLiveQueryReturn } from '@tanstack/svelte-db';
import { useLiveQuery } from '@tanstack/svelte-db';
import type { FeatureCollection } from 'geojson';
import type { UUID } from 'crypto';
import type { LngLatLike } from 'svelte-maplibre';

import type { DbEntityType, EntityStatusPayload, entityStatusOptions } from '$lib/types';
import type { OdkEntity } from '$store/collections';
import { EntityStatusNameMap } from '$lib/types';
import { getAlertStore } from '$store/common.svelte';

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

let userLocationCoord: LngLatLike | undefined = $state();
let selectedEntityId: string | null = $state(null);
let entitiesCollection: Collection | undefined = $state(undefined);
let entitiesList: UseLiveQueryReturn<OdkEntity[]> | undefined;

// Map each entity_id to the entity data, for faster lookup in map
let entityMap = $derived(new Map(entitiesList?.data.map((entity) => [entity.entity_id, entity])));
let selectedEntity: DbEntityType | null = $derived(entityMap.get(selectedEntityId || '') ?? null);

const alertStore = getAlertStore();

let syncEntityStatusManuallyLoading: boolean = $state(false);
let updateEntityStatusLoading: boolean = $state(false);
let selectedEntityCoordinate: entityIdCoordinateMapType | null = $state(null);
let entityToNavigate: entityIdCoordinateMapType | null = $state(null);
let toggleGeolocation: boolean = $state(false);
// TODO calculate submission info from collection
let taskSubmissionInfo: taskSubmissionInfoType[] = $derived(calculateTaskSubmissionCounts());
let fgbOpfsUrl: string = $state('');
let selectedEntityJavaRosaGeom: string | null = $state(null);

function calculateTaskSubmissionCounts(): taskSubmissionInfoType[] {
	if (!entitiesList) return [];

	const StatusToCode: Record<entityStatusOptions, number> = Object.entries(EntityStatusNameMap).reduce(
		(acc, [codeStr, status]) => {
			acc[status] = Number(codeStr);
			return acc;
		},
		{} as Record<entityStatusOptions, number>,
	);

	const taskEntityMap = entitiesList.data?.reduce((acc: Record<number, DbEntityType[]>, item) => {
		if (!acc[item?.task_id]) {
			acc[item.task_id] = [];
		}
		acc[item.task_id].push(item);
		return acc;
	}, {});

	return Object.entries(taskEntityMap).map(([taskId, taskEntities]) => {
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
}

function getEntitiesStatusStore() {
	function addStatusToGeojsonProperties(geojsonData: FeatureCollection): FeatureCollection {
		return {
			...geojsonData,
			features: geojsonData.features.map((feature) => {
				// Must convert number type from fgb number --> bigint for comparison
				console.log(typeof feature?.properties?.osm_id);
				console.log(feature?.properties?.osm_id);
				const entity = getEntityByOsmId(BigInt(feature?.properties?.osm_id));
				console.log(entity);
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

	// Manually sync the entity status via button - this should push through updates via electric
	async function syncEntityStatusManually(projectId: number) {
		try {
			syncEntityStatusManuallyLoading = true;
			const entityStatusResponse = await fetch(`${API_URL}/projects/${projectId}/entities/statuses`, {
				credentials: 'include',
			});
			if (!entityStatusResponse.ok) {
				throw Error('Failed to get entities for project');
			}
			syncEntityStatusManuallyLoading = false;
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
		try {
			const resp = await fetch(`${API_URL}/central/entity?project_id=${projectId}&entity_uuid=${entityUuid}`, {
				method: 'POST',
				body: JSON.stringify(featcol),
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
				message: error.message || 'Failed to create entity',
			});
			throw new Error(error);
		}
	}

	async function createNewSubmission(projectId: number, submissionXml: string, attachments: File[]) {
		const entityRequestUrl = `${API_URL}/submission?project_id=${projectId}`;
		const entityRequestMethod = 'POST';

		const form = new FormData();
		form.append('submission_xml', submissionXml);
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
		return entitiesList?.data.find((entity) => entity.osm_id === osmId);
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
		syncEntityStatusManually: syncEntityStatusManually,
		addStatusToGeojsonProperties: addStatusToGeojsonProperties,
		createEntity: createEntity,
		deleteNewEntity: deleteNewEntity,
		updateEntityStatus: updateEntityStatus,
		createNewSubmission: createNewSubmission,
		setEntityToNavigate: setEntityToNavigate,
		setToggleGeolocation: setToggleGeolocation,
		setUserLocationCoordinate: setUserLocationCoordinate,
		setFgbOpfsUrl: setFgbOpfsUrl,
		setSelectedEntityJavaRosaGeom: setSelectedEntityJavaRosaGeom,
		get entitiesCollection() {
			return entitiesCollection;
		},
		setEntitiesCollection(newCollection: Collection) {
			entitiesCollection = newCollection;
			entitiesList = useLiveQuery({
				query: (q) => q.from({ entities: entitiesCollection }),
			});
		},
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
		get badGeomCollection() {
			return badGeomCollection;
		},
		get newGeomCollection() {
			return newGeomCollection;
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
