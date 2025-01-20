export type submissionContributorsTypes = {
  user: string;
  contributions: number;
};

export type submissionFormFieldsTypes = {
  path: string;
  name: string;
  type: string;
  binary: any;
  selectMultiple: any;
};

export type submissionTableDataTypes = {
  results: Record<string, any>[];
  pagination: {
    has_next: boolean;
    has_prev: boolean;
    total: number | null;
    page: number | null;
    prev_num: number | null;
    next_num: number | null;
    per_page: number | null;
    pages: number | null;
  };
};

export type reviewListType = {
  id: string;
  title: string;
  className: string;
  hoverClass: string;
};

export type formSubmissionType = { date: string; count: number; label: string };
export type validatedMappedType = { date: string; Validated: number; Mapped: number; label: string };

type featureType = {
  type: 'Feature';
  geometry: Partial<{
    type: string;
    coordinates: any[];
  }>;
  properties: Record<string, any>;
};

export type geometryLogType = {
  status: 'NEW' | 'BAD';
  geojson: featureType;
  project_id: number;
  task_id: number;
};

export type updateReviewStateType = {
  instanceId: string;
  submitterId: number;
  deviceId: string;
  createdAt: string;
  updatedAt: string;
  reviewState: string;
};
