/**
 * Validates files against accepted file types
 * @param files - Single file or array of files
 * @param accept - Accept string (e.g., 'image/*', '.pdf', 'image/jpeg,.pdf')
 * @returns boolean - true if all files are valid
 */

export default function validateFileTypes(files: File | File[] | FileList, accept: string) {
  if (!accept || accept === '*') return true;

  const fileArray = files instanceof File ? [files] : Array.from(files);
  const acceptedTypes = accept
    .toLowerCase()
    .split(',')
    .map((type) => type.trim());

  return fileArray.every((file) => {
    const fileName = file.name.toLowerCase();
    const fileType = file.type.toLowerCase();

    return acceptedTypes.some((type) => {
      if (type === '*/*') return true;
      if (type.endsWith('/*')) return fileType.startsWith(type.slice(0, -1));
      if (type.startsWith('.')) return fileName.endsWith(type);
      return fileType === type;
    });
  });
}
