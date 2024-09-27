import { useEffect, useState } from 'react';
import qrcodeGenerator from 'qrcode-generator';
import { deflate } from 'pako/lib/deflate';

// function base64zlibdecode(string) {
//   return new TextDecoder().decode(inflate(Uint8Array.from(window.atob(string), (c) => c.codePointAt(0))))
// }

function base64zlibencode(string: string) {
  return window.btoa(String.fromCodePoint(...deflate(new TextEncoder().encode(string))));
}

export const GetProjectQrCode = (
  odkToken: string | undefined,
  projectName: string | undefined,
  osmUser: string,
): { qrcode: string } => {
  const [qrcode, setQrcode] = useState('');

  useEffect(() => {
    const fetchProjectFileById = async (
      odkToken: string | undefined,
      projectName: string | undefined,
      osmUser: string,
    ) => {
      if (!odkToken || !projectName) {
        setQrcode('');
        return;
      }

      const odkCollectJson = JSON.stringify({
        general: {
          server_url: odkToken,
          form_update_mode: 'match_exactly',
          basemap_source: 'osm',
          autosend: 'wifi_and_cellular',
          metadata_email: 'NOT IMPLEMENTED',
          metadata_username: osmUser,
        },
        project: { name: projectName },
        admin: {},
      });

      // Note: error correction level = "L"
      const code = qrcodeGenerator(0, 'L');
      // Note: btoa base64 encodes the JSON string
      // Note: pako.deflate zlib encodes to content
      code.addData(base64zlibencode(odkCollectJson));
      code.make();
      // Note: cell size = 3, margin = 5
      setQrcode(code.createDataURL(3, 5));
    };

    fetchProjectFileById(odkToken, projectName, osmUser);
  }, [projectName, odkToken, osmUser]);
  return { qrcode };
};

export async function readFileFromOPFS(filePath: string) {
  const opfsRoot = await navigator.storage.getDirectory();
  const directories = filePath.split('/');

  let currentDirectoryHandle = opfsRoot;

  // Iterate dirs and get directoryHandles
  for (const directory of directories.slice(0, -1)) {
    console.log(`Reading OPFS dir: ${directory}`);
    try {
      currentDirectoryHandle = await currentDirectoryHandle.getDirectoryHandle(directory);
    } catch {
      return null; // Directory doesn't exist
    }
  }

  // Get file within final directory handle
  try {
    const filename: any = directories.pop();
    console.log(`Getting OPFS file: ${filename}`);
    const fileHandle = await currentDirectoryHandle.getFileHandle(filename);
    const fileData = await fileHandle.getFile(); // Read the file
    return fileData;
  } catch {
    return null; // File doesn't exist or error occurred
  }
}

export async function writeBinaryToOPFS(filePath: string, data: any) {
  console.log(`Starting write to OPFS file: ${filePath}`);

  const opfsRoot = await navigator.storage.getDirectory();

  // Split the filePath into directories and filename
  const directories = filePath.split('/');
  const filename: any = directories.pop();

  // Start with the root directory handle
  let currentDirectoryHandle = opfsRoot;

  // Iterate over directories and create nested directories
  for (const directory of directories) {
    console.log(`Creating OPFS dir: ${directory}`);
    try {
      currentDirectoryHandle = await currentDirectoryHandle.getDirectoryHandle(directory, { create: true });
    } catch (error) {
      console.error('Error creating directory:', error);
    }
  }

  // Create the file handle within the last directory
  const fileHandle = await currentDirectoryHandle.getFileHandle(filename, { create: true });
  const writable = await fileHandle.createWritable();

  // Write data to the writable stream
  try {
    await writable.write(data);
  } catch (error) {
    console.log(error);
  }

  // Close the writable stream
  await writable.close();
  console.log(`Finished write to OPFS file: ${filePath}`);
}
