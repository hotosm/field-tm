export interface HomeProjectCardModel {
  id: number;
  name: string;
  priority: number;
  location_str: string;
  description: string;
  total_tasks: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
}

export type homeProjectPaginationTypes = {
  has_next: boolean;
  has_prev: boolean;
  next_num: number | null;
  page: number | null;
  pages: number | null;
  prev_num: number | null;
  per_page: number | null;
  total: number | null;
};

export type projectType = {
  name: string;
  centroid: [number, number];
  short_description: string;
  hashtags: string | null;
  id: number;
  location_str: string;
  num_contributors: number;
  organisation_id: number;
  organisation_logo: string | null;
  priority: number;
  outline: { type: string; coordinates: number[][] };
};

export type snackbarTypes = {
  open: boolean;
  message: string;
  variant: 'info' | 'success' | 'error' | 'warning';
  duration: number;
};
