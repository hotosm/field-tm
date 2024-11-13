import { writable } from 'svelte/store';
import { ShapeStream, Shape } from '@electric-sql/client';
import type { ShapeData, Row } from '@electric-sql/client';

const entitiesStatusStore = writable([]);
let selectedEntity = writable<any>(null);
let entitiesShape: Shape;

function getEntityStatusStream(projectId: number): ShapeStream | undefined {
	if (!projectId) {
		return;
	}
	return new ShapeStream({
		url: `${import.meta.env.VITE_SYNC_URL}/v1/shape/odk_entities`,
		where: `project_id=${projectId}`,
	});
}

async function subscribeToEntityStatusUpdates(taskEventStream: ShapeStream) {
	entitiesShape = new Shape(taskEventStream);

	entitiesShape.subscribe((taskEvent: ShapeData) => {
		let newStatus: Row;
		for (newStatus of taskEvent);
		if (newStatus) {
			entitiesStatusStore.set(newStatus[1]);
		}
	});
}

export { entitiesStatusStore, selectedEntity, getEntityStatusStream, subscribeToEntityStatusUpdates };
