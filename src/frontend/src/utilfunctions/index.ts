import { v4 as uuidv4 } from 'uuid';

export function convertFileUrlToFileArray(url: string): { id: string; file: { name: string }; previewURL: string }[] {
  const fileArray = url.split('/');
  const fileName = fileArray[fileArray.length - 1];
  return [
    {
      id: uuidv4(),
      file: { name: fileName },
      previewURL: url,
    },
  ];
}

export function getFileNameFromURL(url: string) {
  const fileArray = url.split('/');
  const fileName = fileArray[fileArray.length - 1];
  return fileName;
}
