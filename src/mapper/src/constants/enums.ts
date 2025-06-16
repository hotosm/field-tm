export enum projectSetupStep {
	// TODO add a prompt here for the user to log in via OSM
	// if they are not already, informing them this is required
	// to get attribution for their mapping contributions
	'osm_login_prompt' = 0,
	'odk_project_load' = 1,
	'task_selection' = 2,
	'complete_setup' = 3,
}

export enum MapGeomTypes {
	POINT = 'POINT',
	POLYGON = 'POLYGON',
	POLYLINE = 'POLYLINE',
}

export enum projectStatus {
	DRAFT = 'DRAFT',
	PUBLISHED = 'PUBLISHED',
	ARCHIVED = 'ARCHIVED',
	COMPLETED = 'COMPLETED',
}

export enum taskStatus {
	UNLOCKED_TO_MAP = 'UNLOCKED_TO_MAP',
	LOCKED_FOR_MAPPING = 'LOCKED_FOR_MAPPING',
	UNLOCKED_TO_VALIDATE = 'UNLOCKED_TO_VALIDATE',
	LOCKED_FOR_VALIDATION = 'LOCKED_FOR_VALIDATION',
	UNLOCKED_DONE = 'UNLOCKED_DONE',
}
