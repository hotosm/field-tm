export const convertFileToGeojson = async (file: File): Promise<any> => {
  try {
    if (!file) return;

    // Parse file as JSON
    const fileReader = new FileReader();
    const fileLoaded: any = await new Promise((resolve) => {
      fileReader.onload = (e) => resolve(e.target?.result);
      fileReader.readAsText(file, 'UTF-8');
    });

    const parsedJSON = JSON.parse(fileLoaded);
    let convertedGeojson;

    if (parsedJSON?.type === 'FeatureCollection') {
      convertedGeojson = parsedJSON;
    } else {
      convertedGeojson = {
        type: 'FeatureCollection',
        features: [{ type: 'Feature', properties: null, geometry: parsedJSON }],
      };
    }
    return convertedGeojson;
  } catch (error) {
    return error;
  }
};
