import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData, Row } from '@electric-sql/client';
import type { Feature, FeatureCollection, GeoJSON } from 'geojson';

import type { ProjectTask, TaskEventType } from '$lib/types';
import { getLoginStore } from '$store/login.svelte.ts';
import { getTimeDiff } from '$lib/utils/datetime';

const loginStore = getLoginStore();

let taskEventShape: Shape;
let featcol: FeatureCollection = $state({ type: 'FeatureCollection', features: [] });
let latestEvent: TaskEventType | null = $state(null);
let events: TaskEventType[] = $state([]);

// for UI show task index for simplicity & for api's use task id
let selectedTaskId: number | null = $state(null);
let selectedTaskIndex: number | null = $state(null);

let selectedTask: any = $state(null);
let selectedTaskState: string = $state('');
let selectedTaskGeom: GeoJSON | null = $state(null);
let taskIdIndexMap: Record<number, number> = $state({});
let commentMention: TaskEventType | null = $state(null);

let userDetails = $derived(loginStore.getAuthDetails);

function getTaskEventStream(projectId: number): ShapeStream | undefined {
	if (!projectId) {
		return;
	}
	return new ShapeStream({
		url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
		params: {
			table: 'task_events',
			where: `project_id=${projectId}`,
		},
	});
}

function getTaskStore() {
	async function subscribeToTaskEvents(taskEventStream: ShapeStream | undefined) {
		if (!taskEventStream) return;
		taskEventShape = new Shape(taskEventStream);
		taskEventShape.subscribe((taskEvent: ShapeData) => {
			const rows: Row[] = taskEvent.rows;
			if (rows && Array.isArray(rows)) {
				latestEvent = rows?.slice(-1)?.[0];

				// if the logged in user is tagged, add mentioned comment to the state
				if (
					latestEvent?.event === 'COMMENT' &&
					latestEvent?.comment?.includes(`@${userDetails?.username}`) &&
					latestEvent.comment?.startsWith('#submissionId:uuid:') &&
					getTimeDiff(new Date(latestEvent?.created_at)) < 120
				) {
					commentMention = latestEvent;
				}
				for (const newEvent of rows) {
					if (newEvent.task_id === selectedTaskId) {
						selectedTaskState = newEvent.state;
					}
				}
			}
		});
	}

	async function appendTaskStatesToFeatcol(projectTasks: ProjectTask[]) {
		const latestTaskStates = await getLatestStatePerTask();
		const features: Feature[] = projectTasks.map((task) => ({
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
		selectedTaskGeom = featcol.features.find((x) => x?.properties?.fid === taskId)?.geometry || null;
	}

	function setTaskIdIndexMap(idIndexMappedRecord: Record<number, number>) {
		taskIdIndexMap = idIndexMappedRecord;
	}

	function dismissCommentMention() {
		commentMention = null;
	}

	function clearTaskStates() {
		selectedTask = null;
		selectedTaskId = null;
		selectedTaskIndex = null;
		selectedTaskGeom = null;
		selectedTaskState = '';
		taskIdIndexMap = {};
		featcol = { type: 'FeatureCollection', features: [] };
	}
	return {
		// The task areas / status colours displayed on the map
		appendTaskStatesToFeatcol: appendTaskStatesToFeatcol,
		subscribeToEvents: subscribeToTaskEvents,
		setSelectedTaskId: setSelectedTaskId,
		setTaskIdIndexMap: setTaskIdIndexMap,
		dismissCommentMention: dismissCommentMention,
		clearTaskStates: clearTaskStates,
		get featcol() {
			return featcol;
		},
		// The latest event to display in notifications bar
		get latestEvent() {
			return latestEvent;
		},
		get events() {
			return events;
		},

		// The selected task to display mapping dialog
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
		get taskIdIndexMap() {
			return taskIdIndexMap;
		},
		get commentMention() {
			return commentMention;
		},
	};
}

export { getTaskStore, getTaskEventStream };
