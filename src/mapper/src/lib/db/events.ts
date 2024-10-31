import { v4 as uuidv4 } from 'uuid';
import { TaskEventEnum } from '$lib/types';
import type { TaskEvent, TaskEventResponse, NewEvent } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL;

async function add_event(
	// db,
	projectId: number,
	taskId: number,
	// userId: number,
	eventType: TaskEvent,
	// comment: string = '',
	// ): Promise<void> {
): Promise<TaskEventResponse | false> {
	// const eventId = uuidv4()
	const newEvent: NewEvent = {
		event_id: uuidv4(),
		event: eventType,
		task_id: taskId,
	};
	const resp = await fetch(`${API_URL}/tasks/${taskId}/event/?project_id=${projectId}`, {
		method: 'POST',
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(newEvent),
	});

	if (resp.status !== 200) {
		console.error('Failed to update status in API');
		return false;
	}

	const response = await resp.json();
	return response;

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
	await add_event(/* db, */ projectId, taskId, TaskEventEnum.MAP);
}

export async function finishTask(/* db, */ projectId: number, taskId: number): Promise<void> {
	await add_event(/* db, */ projectId, taskId, TaskEventEnum.FINISH);
}

export async function resetTask(/* db, */ projectId: number, taskId: number): Promise<void> {
	await add_event(/* db, */ projectId, taskId, TaskEventEnum.BAD);
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
