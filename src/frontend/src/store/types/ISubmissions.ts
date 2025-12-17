export type filterType = {
  task_id: string | null;
  submitted_by: string | null;
  review_state: string | null;
  submitted_date_range: string | null;
  page: number;
  results_per_page: number;
};

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
