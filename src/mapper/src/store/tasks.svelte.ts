import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData, Row } from '@electric-sql/client';
import type { GeoJSON } from 'geosjon';

import type { ProjectTask, TaskEventType } from '$lib/types';

let taskEventShape: Shape;
let featcol = $state({ type: 'FeatureCollection', features: [] });
let latestEvent = $state(null);
let events: TaskEventType[] = $state([]);
let selectedTaskId: number | null = $state(null);
let selectedTask: any = $state(null);
let selectedTaskState: string = $state('');
let selectedTaskGeom: GeoJSON | null = $state(null);

function getTaskEventStream(projectId: number): ShapeStream | undefined {
	if (!projectId) {
		return;
	}
	return new ShapeStream({
		url: `${import.meta.env.VITE_SYNC_URL}/v1/shape/task_events`,
		where: `project_id=${projectId}`,
	});
}

function getTaskStore() {
	async function subscribeToTaskEvents(taskEventStream: ShapeStream) {
		taskEventShape = new Shape(taskEventStream);

		taskEventShape.subscribe((taskEvent: ShapeData) => {
			let newEvent: Row;
			for (newEvent of taskEvent);
			if (newEvent) {
				latestEvent = newEvent[1];
			}
			if (newEvent?.[1]?.task_id === selectedTaskId) {
				selectedTaskState = newEvent[1].state;
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

	async function setSelectedTaskId(newId: number) {
		selectedTaskId = newId;
		const allTasksCurrentStates = await getLatestStatePerTask();
		selectedTask = allTasksCurrentStates.get(newId);
		selectedTaskState = selectedTask?.state || 'UNLOCKED_TO_MAP';
		selectedTaskGeom = featcol.features.find((x) => x.properties.fid === newId)?.geometry || null;
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
