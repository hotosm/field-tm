export interface HomeProjectCardModel {
  id: number;
  priority: number;
  title: string;
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
  centroid: [number, number];
  description: string;
  hashtags: string | null;
  id: number;
  location_str: string;
  num_contributors: number;
  organisation_id: number;
  organisation_logo: string | null;
  priority: number;
  tasks_bad: number;
  tasks_mapped: number;
  tasks_validated: number;
  title: string;
  total_tasks: number;
};

export type snackbarTypes = {
  open: boolean;
  message: string;
  variant: 'info' | 'success' | 'error' | 'warning';
  duration: number;
};
