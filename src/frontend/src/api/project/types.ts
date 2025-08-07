import { project_status, project_visibility } from '@/types/enums';
import type { Point } from 'geojson';

export type projectSummaryType = {
  id: number;
  name: string;
  organisation_id: number;
  priority: number;
  hashtags: string[];
  location_str: string;
  short_description: string;
  status: project_status;
  visibility: project_visibility;
  organisation_logo: string | null;
  centroid: Point;
  total_tasks: number;
  num_contributors: number;
  total_submissions: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
};
