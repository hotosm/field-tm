import { project_status, project_visibility } from '@/types/enums';

export type projectType = {
  name: string;
  centroid: [number, number];
  hashtags: string | null;
  id: number;
  location_str: string;
  num_contributors: number;
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
