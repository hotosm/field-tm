export const getDirtyFieldValues = (allValues: Record<string, any>, dirtyFields: Record<string, any>) => {
  const dirtyValues: any = {};
  Object.keys(allValues).forEach((key: string) => {
    if (dirtyFields[key]) {
      dirtyValues[key] = allValues[key];
    }
  });

  return dirtyValues;
};

export const convertGeojsonToJsonFile = (geojson: any, fileName: string) => {
  const blob = new Blob([JSON.stringify(geojson)], { type: 'application/json' });
  const file = new File([blob], `${fileName}.json`, { type: 'application/json' });
  return file;
};

export const downloadBlobData = (blobData: Blob, filename: string, extension: string) => {
  if (!blobData) return;
  const url = window.URL.createObjectURL(blobData);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filename}.${extension}`;
  a.click();
  window.URL.revokeObjectURL(url);
};
