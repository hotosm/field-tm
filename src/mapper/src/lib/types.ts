import type { UUID } from 'crypto';
import type { Point, Polygon } from 'geojson';
import { m } from '$translations/messages.js';

export type ProjectTask = {
	id: number;
	project_id: number;
	project_task_index: number;
	feature_count: number;
	outline: Polygon;
};

export interface ProjectData {
	id: number;
	odkid: number;
	name: string;
	short_description: string;
	description: string;
	per_task_instructions: string;
	outline: {
		type: string;
		geometry: {
			type: string;
			coordinates: [];
		};
		properties: {
			id: number;
			bbox: [number, number, number, number];
		};
		id: number;
	};
	location_str: string;
	osm_category: string;
	odk_form_id: string;
	data_extract_url: string;
	odk_token: string;
	organisation_id: number;
	organisation_logo: string;
	author_id: number;
	custom_tms_url: string;
	status: number;
	hashtags: string[];
	tasks: ProjectTask[];
	geo_restrict_distance_meters: number;
	geo_restrict_force_error: boolean;
	use_odk_collect: boolean;
}

export interface ZoomToTaskEventDetail {
	taskId: number;
}

export type TaskStatus = {
	UNLOCKED_TO_MAP: string;
	LOCKED_FOR_MAPPING: string;
	UNLOCKED_TO_VALIDATE: string;
	LOCKED_FOR_VALIDATION: string;
	UNLOCKED_DONE: string;
};
export const TaskStatusEnum: TaskStatus = Object.freeze({
	UNLOCKED_TO_MAP: m['task_states.UNLOCKED_TO_MAP'](),
	LOCKED_FOR_MAPPING: m['task_states.LOCKED_FOR_MAPPING'](),
	UNLOCKED_TO_VALIDATE: m['task_states.UNLOCKED_TO_VALIDATE'](),
	LOCKED_FOR_VALIDATION: m['task_states.LOCKED_FOR_VALIDATION'](),
	UNLOCKED_DONE: m['task_states.UNLOCKED_DONE'](),
});

export type TaskEvent = {
	MAP: string;
	FINISH: string;
	VALIDATE: string;
	GOOD: string;
	BAD: string;
};
export const TaskEventEnum: TaskEvent = Object.freeze({
	MAP: 'MAP',
	FINISH: 'FINISH',
	VALIDATE: 'VALIDATE',
	GOOD: 'GOOD',
	BAD: 'BAD',
});

export type TaskEventResponse = {
	event_id: string;
	event: TaskEvent;
	task_id: number;
	comment: string;
	created_at: string;
	username: string;
	profile_img: string;
	status: TaskStatus;
};

export type NewEvent = {
	event_id: UUID;
	event: TaskEvent;
	task_id: number;
	comment?: string | null;
};

export type TaskEventType = {
	event_id: string;
	event: TaskEvent | 'COMMENT';
	state: TaskStatus | null;
	project_id: number;
	task_id: number;
	user_id: number;
	username: string;
	comment: string | null;
	created_at: string;
};

export type projectType = {
	centroid: Point;
	hashtags: string[];
	id: number;
	location_str: string | null;
	name: string;
	num_contributors: number;
	organisation_id: number;
	organisation_logo: string | null;
	outline: Polygon;
	priority: number;
	short_description: string;
	total_tasks: string;
};

export type paginationType = {
	has_next: boolean;
	has_prev: boolean;
	next_num: number | null;
	page: number | null;
	pages: number | null;
	prev_num: number | null;
	per_page: number;
	total: number | null;
};

export type EntityStatusPayload = {
	entity_id: UUID;
	status: number;
	// label: string, // label is now automatically determined
};

export type EntitiesDbType = {
	entity_id: UUID;
	status: string;
	project_id: number;
	task_id: number;
};

export type entityStatusOptions =
	| 'READY'
	| 'OPENED_IN_ODK'
	| 'SURVEY_SUBMITTED'
	| 'NEW_GEOM'
	| 'MARKED_BAD'
	| 'VALIDATED';
export const EntityStatusNameMap: Record<number, entityStatusOptions> = {
	0: 'READY',
	1: 'OPENED_IN_ODK',
	2: 'SURVEY_SUBMITTED',
	3: 'NEW_GEOM',
	5: 'VALIDATED',
	6: 'MARKED_BAD',
};

export type entitiesApiResponse = {
	id: string;
	task_id: number;
	osm_id: number;
	status: number;
	updated_at: string | null;
	submission_ids: string;
};

export type entitiesShapeType = {
	entity_id: string;
	status: entityStatusOptions;
	project_id: number;
	task_id: number;
};

// What we actually use in the frontend (a merger from API / ShapeStream / DB)
export type entitiesListType = {
	entity_id: string;
	status: entityStatusOptions;
	project_id: number;
	task_id: number;
	osm_id?: number | undefined;
	submission_ids?: string | undefined;
};
