import { TaskEventEnum } from '$lib/types';
import type { TaskEvent, TaskEventResponse, NewEvent } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL;

async function add_event(
	// db,
	projectId: number,
	taskId: number,
	// userId: number,
	eventType: TaskEvent,
	comment: string | null = null,
	// ): Promise<void> {
): Promise<TaskEventResponse | false> {
	const newEvent: NewEvent = {
		event_id: crypto.randomUUID(),
		event: eventType,
		task_id: taskId,
		comment: comment,
	};
	const resp = await fetch(`${API_URL}/tasks/${taskId}/event?project_id=${projectId}`, {
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

export async function commentTask(/* db, */ projectId: number, taskId: number, comment: string): Promise<void> {
	await add_event(/* db, */ projectId, taskId, 'COMMENT', comment);
}
