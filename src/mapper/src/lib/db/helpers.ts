import type { PGliteInterface } from '@electric-sql/pglite';

// For bulk import of rows into PGLite using COPY FROM csv blob functionality
// approach taken from https://github.com/electric-sql/pglite repo.
export async function applyDataToTableWithCsvCopy(db: PGliteInterface, table: string, data: Record<string, any>[]) {
	// Get column names from the first message
	const columns = Object.keys(data[0]);

	// Create CSV data
	const csvData = data
		.map((message) => {
			return columns
				.map((column) => {
					const value = message[column];
					// Escape double quotes and wrap in quotes if necessary
					if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
						return `"${value.replace(/"/g, '""')}"`;
					}
					return value === null ? '\\N' : value;
				})
				.join(',');
		})
		.join('\n');
	const csvBlob = new Blob([csvData], { type: 'text/csv' });

	// Perform COPY FROM
	await db.query(
		`
        COPY "public"."${table}" (${columns.map((c) => `"${c}"`).join(', ')})
        FROM '/dev/blob'
        WITH (FORMAT csv, NULL '\\N')
      `,
		[],
		{
			blob: csvBlob,
		},
	);
}
