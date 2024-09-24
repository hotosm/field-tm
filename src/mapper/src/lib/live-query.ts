import { readable } from 'svelte/store';
import { QualifiedTablename, hasIntersection } from 'electric-sql/util';
import { type Notifier } from 'electric-sql/notifiers';

export interface LiveResultContext<T> {
	(): Promise<LiveResult<T>>;
	sourceQuery?: Record<string, any> | undefined;
}

/**
 * A live result wrapping the `result` as well as the concerned table names.
 * The table names are used to subscribe to changes to those tables
 * in order to re-run the live query when one of the tables change.
 */
export class LiveResult<T> {
	constructor(
		public result: T,
		public tablenames: QualifiedTablename[],
	) {}
}

export function createLiveQuery<T>(notifier: Notifier, query: LiveResultContext<T>) {
	return readable<T | undefined>(undefined, (set) => {
		let tablenames: QualifiedTablename[];
		let key: string;
		query().then((r) => {
			tablenames = r.tablenames;
			set(r.result);

			key = notifier.subscribeToDataChanges((notification) => {
				const changedTablenames = notifier.alias(notification);

				if (hasIntersection(tablenames, changedTablenames)) {
					query().then((r) => set(r.result));
				}
			});
		});

		return function stop() {
			if (key) {
				notifier.unsubscribeFromDataChanges(key);
			}
		};
	});
}
