import { projectVisibilityOptionsType } from '@/store/types/ICreateProject';
import { project_visibility } from '@/types/enums';

export interface ICreateProjectSteps {
  step: number;
  label: string;
  name: string;
}

export const createProjectSteps: ICreateProjectSteps[] = [
  {
    step: 1,
    label: '01',
    name: 'Basic Details',
  },
  {
    step: 2,
    label: '02',
    name: 'Project Details',
  },
  {
    step: 3,
    label: '03',
    name: 'Upload Survey',
  },
  {
    step: 4,
    label: '04',
    name: 'Map Data',
  },
  {
    step: 5,
    label: '05',
    name: 'Split Tasks',
  },
];

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

type uploadAreaOptionsType = {
  name: 'upload_area';
  value: 'draw' | 'upload_file';
  label: string;
};

export const uploadAreaOptions: uploadAreaOptionsType[] = [
  {
    name: 'upload_area',
    value: 'draw',
    label: 'Draw',
  },
  {
    name: 'upload_area',
    value: 'upload_file',
    label: 'Upload File',
  },
];

export const primaryGeomOptions = [
  { name: 'primary_geom_type', value: 'POLYGON', label: 'Polygons (e.g. buildings)' },
  { name: 'primary_geom_type', value: 'POINT', label: 'Points (e.g. POIs)' },
  { name: 'primary_geom_type', value: 'POLYLINE', label: 'Lines (e.g. roads, rivers)' },
];

export const newGeomOptions = [
  { name: 'new_geom_type', value: 'POLYGON', label: 'Polygons' },
  { name: 'new_geom_type', value: 'POINT', label: 'Points' },
  { name: 'new_geom_type', value: 'POLYLINE', label: 'Lines' },
];
