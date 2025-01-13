export enum projectSetupStep {
	// TODO add a prompt here for the user to log in via OSM
	// if they are not already, informing them this is required
	// to get attribution for their mapping contributions
	'osm_login_prompt' = 0,
	'odk_project_load' = 1,
	'task_selection' = 2,
	'complete_setup' = 3,
}

export enum NewGeomTypes {
	POINT = 'POINT',
	POLYGON = 'POLYGON',
	LINESTRING = 'LINESTRING',
}
