import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData, Row } from '@electric-sql/client';
import type { GeoJSON } from 'geojson';

import type { ProjectTask, TaskEventType } from '$lib/types';

let taskEventShape: Shape;
let featcol = $state({ type: 'FeatureCollection', features: [] });
let latestEvent = $state(null);
let events: TaskEventType[] = $state([]);

// for UI show task index for simplicity & for api's use task id
let selectedTaskId: number | null = $state(null);
let selectedTaskIndex: number | null = $state(null);

let selectedTask: any = $state(null);
let selectedTaskState: string = $state('');
let selectedTaskGeom: GeoJSON | null = $state(null);

function getTaskEventStream(projectId: number): ShapeStream | undefined {
	if (!projectId) {
		return;
	}
	return new ShapeStream({
		url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
		table: 'task_events',
		where: `project_id=${projectId}`,
	});
}

function getTaskStore() {
	async function subscribeToTaskEvents(taskEventStream: ShapeStream) {
		taskEventShape = new Shape(taskEventStream);

		taskEventShape.subscribe((taskEvent: ShapeData) => {
			const rows: Row[] = taskEvent.rows;
			if (rows && Array.isArray(rows)) {
				for (const newEvent of rows) {
					if (newEvent) {
						latestEvent = newEvent;
					}
					if (newEvent.task_id === selectedTaskId) {
						selectedTaskState = newEvent.state;
					}
				}
			}
		});
	}

	async function appendTaskStatesToFeatcol(projectTasks: ProjectTask[]) {
		const latestTaskStates = await getLatestStatePerTask();
		const features = projectTasks.map((task) => ({
			type: 'Feature',
			geometry: task.outline,
			properties: {
				fid: task.id,
				state: latestTaskStates.get(task.id)?.state || 'UNLOCKED_TO_MAP',
				actioned_by_uid: latestTaskStates.get(task.id)?.actioned_by_uid,
				task_index: task?.project_task_index,
			},
		}));

		featcol = { type: 'FeatureCollection', features };
	}

	async function getLatestStatePerTask() {
		const taskEventData: ShapeData = await taskEventShape.value;
		const taskEventRows = Array.from(taskEventData.values()) as TaskEventType[];
		// Update the events in taskStore
		events = taskEventRows;

		const currentTaskStates = new Map();

		for (const taskData of taskEventRows) {
			// Use the task_id as the key and state as the value
			currentTaskStates.set(taskData.task_id, {
				state: taskData.state,
				actioned_by_uid: taskData.user_id,
			});
		}

		return currentTaskStates;
	}

	async function setSelectedTaskId(taskId: number | null, taskIndex: number | null) {
		selectedTaskId = taskId;
		selectedTaskIndex = taskIndex;
		const allTasksCurrentStates = await getLatestStatePerTask();
		selectedTask = allTasksCurrentStates.get(taskId);
		selectedTaskState = selectedTask?.state || 'UNLOCKED_TO_MAP';
		selectedTaskGeom = featcol.features.find((x) => x.properties.fid === taskId)?.geometry || null;
	}

	return {
		// The task areas / status colours displayed on the map
		appendTaskStatesToFeatcol: appendTaskStatesToFeatcol,
		get featcol() {
			return featcol;
		},

		// The latest event to display in notifications bar
		subscribeToEvents: subscribeToTaskEvents,
		get latestEvent() {
			return latestEvent;
		},
		get events() {
			return events;
		},

		// The selected task to display mapping dialog
		setSelectedTaskId: setSelectedTaskId,
		get selectedTaskId() {
			return selectedTaskId;
		},
		get selectedTaskIndex() {
			return selectedTaskIndex;
		},
		get selectedTask() {
			return selectedTask;
		},
		get selectedTaskState() {
			return selectedTaskState;
		},
		get selectedTaskGeom() {
			return selectedTaskGeom;
		},
	};
}

export { getTaskStore, getTaskEventStream };
