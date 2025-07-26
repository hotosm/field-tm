import type { TaskEvent } from '$store/collections';
import type { NewEvent } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL;

export const events = {
	create: async (event: NewEvent): Promise<{ entity: TaskEvent; txid: number }> => {
		// Gen random UUID
		event.event_id = crypto.randomUUID();
		const response = await fetch(`${API_URL}/tasks/${event.task_id}/event?project_id=${event.project_id}`, {
			method: 'POST',
			body: JSON.stringify(event),
			headers: { 'Content-type': 'application/json' },
			credentials: 'include',
		});
		if (!response.ok) {
			const errorData = await response.json();
			// alertStore.setAlert({
			// 	variant: 'danger',
			// 	message: error.message || 'Failed to create event',
			// });
			throw new Error(errorData.detail);
		}
		return response.json();
	},
};
