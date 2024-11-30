export async function readFileFromOPFS(filePath: string): Promise<File | null> {
	const opfsRoot = await navigator.storage.getDirectory();
	const directories = filePath.split('/');

	let currentDirectoryHandle: FileSystemDirectoryHandle = opfsRoot;

	// Iterate dirs and get directory handles
	for (const directory of directories.slice(0, -1)) {
		// console.log(`Reading OPFS dir: ${directory}`);
		try {
			currentDirectoryHandle = await currentDirectoryHandle.getDirectoryHandle(directory);
		} catch {
			return null; // Directory doesn't exist
		}
	}

	// Get file within the final directory handle
	try {
		const filename = directories.pop();
		if (!filename) {
			return null; // Invalid path
		}
		// console.log(`Getting OPFS file: ${filename}`);
		const fileHandle = await currentDirectoryHandle.getFileHandle(filename);
		const fileData = await fileHandle.getFile(); // Read the file
		return fileData;
	} catch {
		return null; // File doesn't exist or error occurred
	}
}

export async function writeBinaryToOPFS(filePath: string, data: Blob | BufferSource | string): Promise<void> {
	console.log(`Starting write to OPFS file: ${filePath}`);

	const opfsRoot = await navigator.storage.getDirectory();

	// Split the filePath into directories and filename
	const directories = filePath.split('/');
	const filename = directories.pop();
	if (!filename) {
		throw new Error('Invalid file path'); // Ensure filename exists
	}

	// Start with the root directory handle
	let currentDirectoryHandle: FileSystemDirectoryHandle = opfsRoot;

	// Iterate over directories and create nested directories
	for (const directory of directories) {
		console.log(`Creating OPFS dir: ${directory}`);
		try {
			currentDirectoryHandle = await currentDirectoryHandle.getDirectoryHandle(directory, { create: true });
		} catch (error) {
			console.error('Error creating directory:', error);
			throw error;
		}
	}

	// Create the file handle within the last directory
	const fileHandle = await currentDirectoryHandle.getFileHandle(filename, { create: true });
	const writable = await fileHandle.createWritable();

	// Write data to the writable stream
	try {
		await writable.write(data);
	} catch (error) {
		console.error('Error writing to file:', error);
		throw error;
	}

	// Close the writable stream
	await writable.close();
	console.log(`Finished write to OPFS file: ${filePath}`);
}
