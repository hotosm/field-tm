export type geojsonObjectModelType = {
  features: { geometry: any; properties: any; type: any }[];
  type: string;
  SRID: {
    type: string;
    properties: {
      name: string;
    };
  };
};

export const geojsonObjectModel: geojsonObjectModelType = {
  type: 'FeatureCollection',
  SRID: {
    type: 'name',
    properties: {
      name: 'EPSG:3857',
    },
  },
  features: [],
};
