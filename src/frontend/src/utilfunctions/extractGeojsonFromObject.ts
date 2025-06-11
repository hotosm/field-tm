import { featureType, geojsonType } from '@/store/types/ISubmissions';

// convert JavaRosa string to a GeoJson
export const convertCoordinateStringToFeature = (key: string, coordinateString: string) => {
  let feature: featureType = {
    type: 'Feature',
    geometry: {},
    properties: {},
  };

  // if feature is Polygon in JavaRosa format it contains string of array separated by ';'
  if (coordinateString?.replace(/;$/, '')?.includes(';')) {
    let coordinates = coordinateString
      ?.replace(/;$/, '')
      ?.split(';')
      ?.map((coord) => {
        let coordinate = coord
          .trim()
          .split(' ')
          .slice(0, 2)
          .map((value: string) => {
            return parseFloat(value);
          });
        return [coordinate[1], coordinate[0]];
      });
    // if initial and last coordinates are same, it's a Polygon else LineString
    if (coordinates?.[0]?.toString() === coordinates?.[coordinates?.length - 1]?.toString()) {
      feature = { ...feature, geometry: { type: 'Polygon', coordinates: [coordinates] }, properties: { label: key } };
    } else {
      feature = { ...feature, geometry: { type: 'LineString', coordinates: coordinates }, properties: { label: key } };
    }
  } else {
    // if feature is Point in JavaRosa format it contains string of array
    const splittedCoord = coordinateString?.split(' ');
    let coordinates = [+splittedCoord[1], +splittedCoord[0]];
    feature = { ...feature, geometry: { type: 'Point', coordinates: coordinates }, properties: { label: key } };
  }
  return feature;
};

export function extractGeojsonFromObject(data: Record<string, any>) {
  /*{ all feature of geometry points are stored in clusterLayerGeojson
      reason: more than one gps point can be on the exact same coordinate, so clustering and point expand on cluster click is important for visualization 
  }*/
  let clusterLayerGeojson: geojsonType = {
    type: 'FeatureCollection',
    features: [],
  };

  // feature other than of geometry type points are stored in vectorLayerGeojson
  let vectorLayerGeojson: any = {
    type: 'FeatureCollection',
    features: [],
  };

  // function called recursively until the object is traversed
  function traverse(data: Record<string, any>) {
    typeof data === 'object' &&
      Object.entries(data)?.map(([key, value]) => {
        if (value && typeof value === 'object' && Object.keys(value).includes('coordinates')) {
          const feature = value as featureType['geometry'];
          if (feature?.type === 'Point') {
            clusterLayerGeojson = {
              ...clusterLayerGeojson,
              features: [
                ...clusterLayerGeojson.features,
                { type: 'Feature', geometry: feature, properties: { label: key } },
              ],
            };
          } else {
            vectorLayerGeojson = {
              ...vectorLayerGeojson,
              features: [
                ...vectorLayerGeojson.features,
                { type: 'Feature', geometry: value, properties: { label: key } },
              ],
            };
          }
        }
        // if value is object then traverse
        else if (value && typeof value === 'object') {
          traverse(value);
        }
        // check if value is JavaRosa LineString
        // the JavaRosa LineString is separated by ';'
        else if (
          value &&
          typeof value === 'string' &&
          value?.includes(';') &&
          value
            ?.split(';')?.[0]
            ?.split(' ')
            ?.every((item) => !isNaN(+item))
        ) {
          const convertedFeature = convertCoordinateStringToFeature(key, value);
          vectorLayerGeojson = {
            ...vectorLayerGeojson,
            features: [...vectorLayerGeojson.features, convertedFeature],
          };
        }
        // check if value is JavaRosa Point
        // point contains 4 floating point data
        else if (
          value &&
          typeof value === 'string' &&
          value?.split(' ')?.every((item) => !isNaN(+item)) &&
          value?.split(' ')?.length === 4
        ) {
          const convertedFeature = convertCoordinateStringToFeature(key, value);
          clusterLayerGeojson = {
            ...clusterLayerGeojson,
            features: [...clusterLayerGeojson.features, convertedFeature],
          };
        }
      });
  }

  traverse(data);
  return { clusterLayerGeojson, vectorLayerGeojson };
}
