import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData } from '@electric-sql/client';
import type { Feature, FeatureCollection, GeoJSON } from 'geojson';

import type { ProjectTask, TaskEventType } from '$lib/types';
import { getLoginStore } from '$store/login.svelte.ts';
import { getTimeDiff } from '$lib/utils/datetime';
import type { taskStatus } from '$constants/enums';

const loginStore = getLoginStore();

let eventsUnsubscribe: (() => void) | null = $state(null);
let featcol: FeatureCollection = $state({ type: 'FeatureCollection', features: [] });
let latestEvent: TaskEventType | null = $state(null);
let events: TaskEventType[] = $state([]);

// for UI show task index for simplicity & for api's use task id
let selectedTaskId: number | null = $state(null);
let selectedTaskIndex: number | null = $state(null);

let selectedTask: any = $state(null);
let selectedTaskState: taskStatus | null = $state(null);
let selectedTaskGeom: GeoJSON | null = $state(null);
let taskIdIndexMap: Record<number, number> = $state({});
let commentMention: TaskEventType | null = $state(null);
let userDetails = $derived(loginStore.getAuthDetails);

function getTaskStore() {
	async function startTaskEventStream(projectId: number): Promise<ShapeStream | undefined> {
		if (!projectId) {
			return;
		}

		const taskEventStream = new ShapeStream({
			url: `${import.meta.env.VITE_SYNC_URL}/v1/shape`,
			params: {
				table: 'task_events',
				where: `project_id=${projectId}`,
			},
		});
		const taskEventShape = new Shape(taskEventStream);

		eventsUnsubscribe = taskEventShape?.subscribe((taskEventData: ShapeData[]) => {
			let taskEventRows: TaskEventType[];
			if (events.length > 0) {
				// If we already have data, only append data changes made since last update
				taskEventRows = taskEventData.rows
					.filter((item): item is { value: TaskEventType } => 'value' in item && item.value !== null)
					.map((item) => item.value);
			} else {
				taskEventRows = taskEventData.rows;
			}

			if (taskEventRows.length) {
				latestEvent = taskEventRows.at(-1) ?? null;

				// If the user is tagged in a comment, then set reactive commentMention variable
				if (
					latestEvent?.event === 'COMMENT' &&
					typeof latestEvent?.comment === 'string' &&
					latestEvent.comment.includes(`@${userDetails?.username}`) &&
					latestEvent.comment.startsWith('#submissionId:uuid:') &&
					getTimeDiff(new Date(latestEvent.created_at)) < 120
				) {
					commentMention = latestEvent;
				}

				// Update the state of currently selected task area
				for (const newEvent of taskEventRows) {
					if (newEvent.task_id === selectedTaskId) {
						selectedTaskState = newEvent.state;
					}
				}

				// Update the events in taskStore
				events = taskEventRows;
			}
		});
	}

	function unsubscribeEventStream() {
		if (eventsUnsubscribe) {
			eventsUnsubscribe();
			eventsUnsubscribe = null;
		}
	}

	async function appendTaskStatesToFeatcol(projectTasks: ProjectTask[]) {
		const latestTaskStates = new Map();

		// Ensure state and actioned_by_uid vars are set for each event
		for (const taskEvent of events) {
			latestTaskStates.set(taskEvent.task_id, {
				state: taskEvent.state,
				actioned_by_uid: taskEvent.user_id,
			});
		}

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

	async function setSelectedTaskId(taskId: number | null, taskIndex: number | null) {
		selectedTaskId = taskId;
		selectedTaskIndex = taskIndex;

		if (!taskId) return;

		// Filter the local `events` store for matching task_id
		const taskRows = events.filter((ev) => ev.task_id === taskId);
		if (!taskRows.length) return;

		// Pick the latest event for this task
		selectedTask = taskRows.at(-1) ?? null;
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
		selectedTaskState = null;
		taskIdIndexMap = {};
		featcol = { type: 'FeatureCollection', features: [] };
	}
	return {
		startTaskEventStream: startTaskEventStream,
		unsubscribeEventStream: unsubscribeEventStream,
		// The task areas / status colours displayed on the map
		appendTaskStatesToFeatcol: appendTaskStatesToFeatcol,
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

export { getTaskStore };
