import type { UUID } from 'crypto';
import type { Polygon } from 'geojson';
import type { MapGeomTypes } from '$constants/enums.ts';

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
	// INVALIDATED: string;
	// BAD: string;
	// SPLIT: string;
	// ARCHIVED: string;
};
export const TaskStatusEnum: TaskStatus = Object.freeze({
	UNLOCKED_TO_MAP: 'UNLOCKED_TO_MAP',
	LOCKED_FOR_MAPPING: 'LOCKED_FOR_MAPPING',
	UNLOCKED_TO_VALIDATE: 'UNLOCKED_TO_VALIDATE',
	LOCKED_FOR_VALIDATION: 'LOCKED_FOR_VALIDATION',
	UNLOCKED_DONE: 'UNLOCKED_DONE',
});

export type TaskEvent = {
	MAP: string;
	FINISH: string;
	VALIDATE: string;
	GOOD: string;
	BAD: string;
	// SPLIT: string;
	// MERGE: string;
	// ASSIGN: string;
	// COMMENT: string;
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
	comment: string | null;
	created_at: string;
	event: TaskEvent | 'COMMENT';
	event_id: string;
	project_id: number;
	state: TaskStatus | null;
	task_id: number;
	user_id: number;
	username: string;
};
