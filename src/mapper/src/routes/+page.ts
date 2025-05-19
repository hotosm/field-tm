import type { PageLoad } from './$types';

export const load: PageLoad = async ({ parent }) => {
	const { dbPromise } = await parent();
	return { dbPromise };
};
