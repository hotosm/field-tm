// // Script to generate a PGLite db dump
// // Creates db 'fmtm' & user 'fmtm'
// // Applies required migrations
// // NOTE this is a plain js file as it's ran directly by NodeJS
// // NOTE however, we don't use this approach for now

// import path from 'path';
// import fs from 'fs';
// import { PGlite } from '@electric-sql/pglite';

// const MIGRATIONS = ['1-enums.sql', '2-tables.sql', '3-constraints.sql', '4-indexes.sql'];

// const MIGRATIONS_PATH = path.resolve('/migrations/init/shared');

// async function createFreshDbDump() {
// 	// Step 1: create a main db and create 'fmtm' db and user
// 	const bootstrap = new PGlite({
// 		// debug: 1
// 	});
// 	await bootstrap.query(`
//     CREATE USER fmtm WITH PASSWORD 'fmtm';
//   `);
// 	await bootstrap.query(`
//     CREATE DATABASE fmtm OWNER fmtm;
//   `);
// 	await bootstrap.query(`
//     ALTER SCHEMA public OWNER TO fmtm;
//   `);

// 	// Step 2: dump the bootstrap db (which contains created fmtm db and user)
// 	const tempFile = await bootstrap.dumpDataDir();
// 	const tempFilePath = tempFile.name;
// 	fs.writeFileSync(tempFilePath, Buffer.from(await tempFile.arrayBuffer()));

// 	// Step 3: load it and connect to 'fmtm' as 'fmtm' user
// 	const db = new PGlite({
// 		// debug: 1
// 		database: 'fmtm',
// 		username: 'fmtm',
// 		loadDataDir: tempFile,
// 	});

// 	// Remove the temporary bootstrap file
// 	fs.rmSync(tempFilePath);

// 	// Step 4: Apply all migrations
// 	for (const file of MIGRATIONS) {
// 		const sql = fs.readFileSync(path.join(MIGRATIONS_PATH, file), 'utf-8');
// 		console.log(`Running ${file}...`);
// 		await db.exec(sql);
// 	}

// 	// Step 5: Dump final database
// 	const finalDump = await bootstrap.dumpDataDir();
// 	const finalDumpPath = finalDump.name;
// 	fs.writeFileSync(finalDumpPath, Buffer.from(await finalDump.arrayBuffer()));

// 	console.log(`✅ DB dump written to ${finalDumpPath}`);
// }

// createFreshDbDump().catch((err) => {
// 	console.error('❌ Failed to init DB:', err);
// 	process.exit(1);
// });
