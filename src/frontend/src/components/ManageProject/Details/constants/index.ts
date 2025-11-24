import { projectVisibilityOptionsType } from '@/store/types/ICreateProject';
import { project_status, project_visibility } from '@/types/enums';
import { projectStatusOptionsType } from '@/store/types/IProject';

export const projectVisibilityOptions: projectVisibilityOptionsType[] = [
  {
    name: 'project_visibility',
    value: project_visibility.PUBLIC,
    label: 'Public',
  },
  {
    name: 'project_visibility',
    value: project_visibility.PRIVATE,
    label: 'Private',
  },
];

export const projectStatusOptions: projectStatusOptionsType[] = [
  {
    name: 'project_status',
    value: project_status.PUBLISHED,
    label: 'Published',
  },
  {
    name: 'project_status',
    value: project_status.COMPLETED,
    label: 'Completed',
  },
];
