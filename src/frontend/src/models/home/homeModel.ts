import { project_status, project_visibility } from '@/types/enums';

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
  total_tasks: number;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_bad: number;
  total_submissions: number;
  visibility: project_visibility;
  status: project_status;
};
