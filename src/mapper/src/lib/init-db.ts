import { PGlite } from '@electric-sql/pglite';
import { drizzle } from 'drizzle-orm/pglite';
import type { PgliteDatabase } from 'drizzle-orm/pglite';

export const initDb = (): PgliteDatabase => {
	const client = new PGlite('idb://fmtm.db', {
		relaxedDurability: true,
	});
	const db = drizzle(client);
	return db;
};
