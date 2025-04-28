import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData } from '@electric-sql/client';
import type { Feature, FeatureCollection } from 'geojson';
import type { LngLatLike } from 'svelte-maplibre';

import type { EntityStatusPayload } from '$lib/types';
import { getAlertStore } from './common.svelte';

const API_URL = import.meta.env.VITE_API_URL;

type entitiesStatusListType = {
	osmid: number | undefined;
	entity_id: string;
	project_id: number;
	status: 'READY' | 'OPENED_IN_ODK' | 'SURVEY_SUBMITTED' | 'MARKED_BAD' | 'VALIDATED';
	task_id: number;
};

type entitiesListType = {
	id: string;
	task_id: number;
	osm_id: number;
	status: number;
	updated_at: string | null;
	submission_ids: string;
};

type entitiesShapeType = {
	entity_id: string;
	status: string;
	project_id: number;
	task_id: number;
};

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

let userLocationCoord: LngLatLike | undefined = $state();
let selectedEntity: string | null = $state(null);
let entitiesShape: Shape;
let geomShape: Shape;
let entitiesStatusList: entitiesStatusListType[] = $state([]);
let badGeomList: FeatureCollection = $state({ type: 'FeatureCollection', features: [] });
let newGeomList: FeatureCollection = $state({ type: 'FeatureCollection', features: [] });
let syncEntityStatusLoading: boolean = $state(false);
let updateEntityStatusLoading: boolean = $state(false);
let selectedEntityCoordinate: entityIdCoordinateMapType | null = $state(null);
let entityToNavigate: entityIdCoordinateMapType | null = $state(null);
let toggleGeolocation: boolean = $state(false);
let entitiesList: entitiesListType[] = $state([]);
let taskSubmissionInfo: taskSubmissionInfoType[] = $state([]);
let alertStore = getAlertStore();

function getEntityStatusStream(projectId: number): ShapeStream | undefined {
	if (!projectId) {
		return;
	}
	return new ShapeStream({
		url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
		params: {
			table: 'odk_entities',
			where: `project_id=${projectId}`,
		},
	});
}

function getNewBadGeomStream(projectId: number): ShapeStream | undefined {
	if (!projectId) {
		return;
	}
	return new ShapeStream({
		url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
		params: {
			table: 'geometrylog',
			where: `project_id=${projectId}`,
		},
	});
}

function setTaskSubmissionInfo(entities: entitiesListType[]) {
	const taskEntityMap = entities?.reduce((acc: Record<number, entitiesListType[]>, item) => {
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
			if (entity.status > 1) {
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
	taskSubmissionInfo = taskInfo;
}

function getEntitiesStatusStore() {
	async function subscribeToEntityStatusUpdates(
		entitiesStream: ShapeStream | undefined,
		entitiesList: entitiesListType[],
	) {
		if (!entitiesStream) return;
		entitiesShape = new Shape(entitiesStream);

		// use Map for quick lookups
		const entityMap = new Map(entitiesList.map((entity) => [entity.id, entity.osm_id]));

		entitiesShape.subscribe((entities: ShapeData) => {
			const rows: entitiesShapeType[] = entities.rows;
			if (Array.isArray(rows)) {
				entitiesStatusList = rows.map((entity) => ({
					...entity,
					osmid: entityMap.get(entity.entity_id) || null,
				}));
			}
		});
	}

	async function subscribeToNewBadGeom(geomStream: ShapeStream | undefined) {
		if (!geomStream) return;
		geomShape = new Shape(geomStream);

		geomShape.subscribe((geom: ShapeData) => {
			const rows: newBadGeomType<'NEW' | 'BAD'>[] = geom.rows;
			const badRows = rows.filter((row) => row.status === 'BAD').map((row) => row?.geojson) as Feature[];
			const newRows = rows.filter((row) => row.status === 'NEW').map((row) => row?.geojson) as Feature[];

			if (rows && Array.isArray(rows)) {
				badGeomList = {
					type: 'FeatureCollection',
					features: badRows,
				};
				newGeomList = {
					type: 'FeatureCollection',
					features: newRows,
				};
			}
		});
	}

	async function setSelectedEntity(entityOsmId: number | null) {
		selectedEntity = entityOsmId;
	}

	async function setSelectedEntityCoordinate(entityCoordinate: entityIdCoordinateMapType | null) {
		selectedEntityCoordinate = entityCoordinate;
	}

	async function syncEntityStatus(projectId: number) {
		try {
			syncEntityStatusLoading = true;
			const entityStatusResponse = await fetch(`${API_URL}/projects/${projectId}/entities/statuses`, {
				credentials: 'include',
			});
			const response = await entityStatusResponse.json();
			entitiesList = response;
			syncEntityStatusLoading = false;
			setTaskSubmissionInfo(response);
		} catch (error) {
			syncEntityStatusLoading = false;
		}
	}

	async function updateEntityStatus(projectId: number, payload: EntityStatusPayload) {
		try {
			updateEntityStatusLoading = true;
			await fetch(`${import.meta.env.VITE_API_URL}/projects/${projectId}/entity/status`, {
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
			const resp = await fetch(`${import.meta.env.VITE_API_URL}/central/entity?project_id=${projectId}`, {
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
			return await resp.json();
		} catch (error: any) {
			alertStore.setAlert({
				variant: 'danger',
				message: error.message || 'Failed to create entity',
			});
		}
	}

	async function createGeomRecord(projectId: number, payload: Record<string, any>) {
		try {
			const resp = await fetch(`${import.meta.env.VITE_API_URL}/projects/${projectId}/geometry/records`, {
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

	function setEntityToNavigate(entityCoordinate: entityIdCoordinateMapType | null) {
		entityToNavigate = entityCoordinate;
	}

	function setToggleGeolocation(status: boolean) {
		toggleGeolocation = status;
	}

	function setUserLocationCoordinate(coordinate: LngLatLike | undefined) {
		userLocationCoord = coordinate;
	}

	return {
		subscribeToEntityStatusUpdates: subscribeToEntityStatusUpdates,
		setSelectedEntity: setSelectedEntity,
		syncEntityStatus: syncEntityStatus,
		updateEntityStatus: updateEntityStatus,
		createEntity: createEntity,
		createGeomRecord: createGeomRecord,
		setSelectedEntityCoordinate: setSelectedEntityCoordinate,
		setEntityToNavigate: setEntityToNavigate,
		setToggleGeolocation: setToggleGeolocation,
		setUserLocationCoordinate: setUserLocationCoordinate,
		subscribeToNewBadGeom: subscribeToNewBadGeom,
		get selectedEntity() {
			return selectedEntity;
		},
		get entitiesStatusList() {
			return entitiesStatusList;
		},
		get badGeomList() {
			return badGeomList;
		},
		get newGeomList() {
			return newGeomList;
		},
		get syncEntityStatusLoading() {
			return syncEntityStatusLoading;
		},
		get updateEntityStatusLoading() {
			return updateEntityStatusLoading;
		},
		get selectedEntityCoordinate() {
			return selectedEntityCoordinate;
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
	};
}

export { getEntityStatusStream, getEntitiesStatusStore, getNewBadGeomStream };
