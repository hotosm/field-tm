export type HomeStateTypes = {
  homeProjectSummary: homeProjectSummaryType[];
  selectedProject: homeProjectSummaryType;
  homeProjectLoading: boolean;
  dialogStatus: boolean;
  snackbar: snackbarTypes;
  showMapStatus: boolean;
  projectCentroidLoading: boolean;
  homeProjectPagination: homeProjectPaginationTypes;
};

type homeProjectSummaryType = {
  centroid?: [number, number];
  description?: string;
  hashtags?: string | null;
  id?: number;
  location_str?: string;
  num_contributors?: number;
  organisation_id?: number;
  organisation_logo?: string | null;
  priority?: number;
  tasks_bad?: number;
  tasks_mapped?: number;
  tasks_validated?: number;
  title?: string;
  total_tasks?: number;
};

type snackbarTypes = {
  open: boolean;
  message: string;
  variant: 'info' | 'success' | 'error' | 'warning';
  duration: number;
};

type homeProjectPaginationTypes = {
  has_next: boolean;
  has_prev: boolean;
  next_num: number | null;
  page: number | null;
  pages: number | null;
  prev_num: number | null;
  per_page: number | null;
  total: number | null;
};
