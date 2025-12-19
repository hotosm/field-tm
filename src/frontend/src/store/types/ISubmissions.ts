export type featureType = {
  type: 'Feature';
  geometry: Partial<{
    type: string;
    coordinates: any[];
  }>;
  properties: Record<string, any>;
};

export type geojsonType = {
  type: 'FeatureCollection';
  features: featureType[];
};
