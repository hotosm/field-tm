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

export interface APIProject {
	id: number;
	name: string;
	short_description: string;
	description: string;
	per_task_instructions: string;
	priority: number;
	location_str: string;
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

export interface DbProject {
	id: number;
	organisation_id?: number;
	name?: string;
	short_description?: string;
	description?: string;
	per_task_instructions?: string;
	location_str?: string;
	status: string; // e.g., 'DRAFT' | 'ACTIVE' | ...
	total_tasks?: number;
	odk_form_id?: string;
	visibility: string; // e.g., 'PUBLIC' | 'PRIVATE'
	mapper_level: string; // e.g., 'BEGINNER' | 'INTERMEDIATE'
	priority?: string; // e.g., 'LOW' | 'MEDIUM' | 'HIGH'
	featured?: boolean;
	odk_token?: string;
	data_extract_url?: string;
	hashtags?: string[];
	custom_tms_url?: string;
	geo_restrict_force_error?: boolean;
	geo_restrict_distance_meters?: number;
	primary_geom_type?: string; // e.g., 'POLYGON'
	new_geom_type?: string;
	use_odk_collect?: boolean;
	created_at: string; // ISO timestamp
	updated_at?: string;

	// API-calculated or client-side only fields
	organisation_logo?: string;
	outline?: any;
	centroid?: any;
	tasks?: ProjectTask[];
	num_contributors?: number;
	total_submissions?: number;
}

// This should match the frontend-only/schema.sql fields
export const DB_PROJECT_COLUMNS = new Set([
	'id',
	'organisation_id',
	'name',
	'short_description',
	'description',
	'per_task_instructions',
	'location_str',
	'status',
	'total_tasks',
	'odk_form_id',
	'visibility',
	'mapper_level',
	'priority',
	'featured',
	'odk_token',
	'data_extract_url',
	'hashtags',
	'custom_tms_url',
	'geo_restrict_force_error',
	'geo_restrict_distance_meters',
	'primary_geom_type',
	'new_geom_type',
	'use_odk_collect',
	'created_at',
	'updated_at',
	'organisation_logo',
	'outline',
	'centroid',
	'tasks',
	'num_contributors',
	'total_submissions',
]);

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
	id: number;
	name: string;
	short_description: string;
	organisation_id?: number;
	organisation_logo: string | null;
	priority: number;
	outline?: Polygon;
	centroid?: Point;
	location_str: string | null;
	hashtags: string[];
	total_tasks?: string;
	num_contributors?: number;
	total_submissions?: number;
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
	label: string; // there is no easy way to automatically determine this
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

export type DbEntity = {
	entity_id: string;
	status: entityStatusOptions;
	project_id: number;
	task_id: number;
	osm_id: number;
	submission_ids: string;
};
