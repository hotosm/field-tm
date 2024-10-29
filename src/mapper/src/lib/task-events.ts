import { v4 as uuidv4 } from 'uuid';
import { TaskStatusEnum } from '$lib/types';
import type { MappingState, TaskEvent } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL;

export function statusEnumLabelToValue(statusLabel: string): string {
	console.log(statusLabel);
	// Check if the statusLabel exists in TaskStatusEnum
	if (!(statusLabel in TaskStatusEnum)) {
		throw new Error(`Invalid status string: ${statusLabel}`);
	}
	const statusValue = TaskStatusEnum[statusLabel as keyof MappingState];

	return statusValue;
}

export function statusEnumValueToLabel(statusValue: string): keyof MappingState {
	// Validate if statusValue exists in TaskStatusEnum
	const statusEntry = Object.entries(TaskStatusEnum).find(([_, value]) => value === statusValue);

	if (statusEntry) {
		return statusEntry[0] as keyof MappingState;
	} else {
		throw new Error(`Invalid status value: ${statusValue}`);
	}
}

// // interface NewEvent {
// //   project_id: number;
// //   task_id: number;
// //   user_id: number;
// // }

async function add_event(
	// db,
	projectId: number,
	taskId: number,
	// userId: number,
	actionId: string,
	// comment: string = '',
	// ): Promise<void> {
): Promise<TaskEvent | false> {
	// const eventId = uuidv4()
	const resp = await fetch(`${API_URL}/tasks/${taskId}/new-status/${actionId}?project_id=${projectId}`, {
		method: 'POST',
		credentials: 'include',
	});

	if (resp.status !== 200) {
		console.error('Failed to update status in API');
		return false;
	}

	const newEvent = await resp.json();
	return newEvent;

	// // Uncomment this for local first approach
	// await db.task_events.create({
	// 	data: {
	// 		event_id: uuidv4(),
	// 		project_id: projectId,
	// 		task_id: taskId,
	// 		event: action,
	// 		comment: comment,
	// 		created_at: new Date().toISOString(),
	// 		user_id: userId,
	// 	},
	// });
}

export async function mapTask(/* db, */ projectId: number, taskId: number): Promise<void> {
	await add_event(/* db, */ projectId, taskId, TaskStatusEnum.LOCKED_FOR_MAPPING);
}

export async function finishTask(/* db, */ projectId: number, taskId: number): Promise<void> {
	// TODO the backend /new-status endpoint is actually posting MappingState
	// TODO it should likely be posting TaskEvent (TaskEvent) to the endpoint
	// TODO then we handle the status of the task internally
	// i.e. it's duplicated info!
	await add_event(/* db, */ projectId, taskId, TaskStatusEnum.UNLOCKED_TO_VALIDATE);
}

export async function resetTask(/* db, */ projectId: number, taskId: number): Promise<void> {
	await add_event(/* db, */ projectId, taskId, TaskStatusEnum.UNLOCKED_TO_MAP);
}

// async function finishTask(db, projectId: number, taskId: number, userId: number): Promise<void> {
// 	// const query = `
// 	//     WITH last AS (
// 	//         SELECT *
// 	//         FROM task_events
// 	//         WHERE project_id = ? AND task_id = ?
// 	//         ORDER BY aid DESC
// 	//         LIMIT 1
// 	//     ),
// 	//     locked AS (
// 	//         SELECT *
// 	//         FROM last
// 	//         WHERE user_id = ? AND action = 'LOCKED_FOR_MAPPING'
// 	//     )
// 	//     INSERT INTO task_events (
// 	//         event_id, project_id, task_id, action,
// 	//         comment, created_at, user_id
// 	//     )
// 	//     SELECT
// 	//         ?, -- event_id
// 	//         ?, -- project_id
// 	//         ?, -- task_id
// 	//         'UNLOCKED_TO_VALIDATE',
// 	//         'Note: Mapping finished',
// 	//         ?
// 	//         user_id
// 	//     FROM last
// 	//     WHERE user_id = ?
// 	//     RETURNING project_id, task_id, user_id;
// 	// `

// 	// const newEvent: NewEvent = db.rawQuery({
// 	//     sql: query,
// 	//     bindParams: [
// 	//         projectId,
// 	//         taskId,
// 	//         userId,
// 	//         //
// 	//         genUUID(),
// 	//         projectId,
// 	//         taskId,
// 	//         new Date().toISOString(),
// 	//         //
// 	//         userId,
// 	//     ]
// 	// })

// 	// assert(newEvent.project_id === projectId);
// 	// assert(newEvent.task_id === taskId);
// 	// assert(newEvent.user_id === userId);

// 	await add_event(db, projectId, taskId, userId, 'UNLOCKED_TO_VALIDATE');
// }

// async function validateTask(db, projectId: number, taskId: number, userId: number): Promise<void> {
// 	await add_event(db, projectId, taskId, userId, 'LOCKED_FOR_VALIDATION');
// }

// async function goodTask(db, projectId: number, taskId: number, userId: number): Promise<void> {
// 	await add_event(db, projectId, taskId, userId, 'VALIDATED');
// }

// async function commentTask(db, projectId: number, taskId: number, userId: number, comment: string): Promise<void> {
// 	await add_event(db, projectId, taskId, userId, 'COMMENT', comment);
// }

// export { mapTask, finishTask, validateTask, goodTask, commentTask };
