import { z } from 'zod/v4';
import { createProjectValidationSchema } from '../validation';
import { project_visibility } from '@/types/enums';

export const defaultValues: z.infer<typeof createProjectValidationSchema> = {
  // 01 Project Overview
  name: '',
  short_description: '',
  description: '',
  organisation_id: null,
  hasODKCredentials: false,
  useDefaultODKCredentials: false,
  odk_central_url: '',
  odk_central_user: '',
  odk_central_password: '',
  project_admins: [],
  uploadAreaSelection: null,
  uploadedAOIFile: undefined,
  outline: undefined,
  outlineArea: undefined,
  organisation_name: '',

  // 02 Project Details
  visibility: project_visibility.PUBLIC,
  hashtags: [],
  hasCustomTMS: false,
  custom_tms_url: '',
  per_task_instructions: '',
  use_odk_collect: false,

  // 03 Upload Survey
  osm_category: '',
  xlsFormFile: null,
  isXlsFormFileValid: false,

  // 04 Map Data
  primary_geom_type: null,
  includeCentroid: false,
  useMixedGeomTypes: false,
  new_geom_type: null,
  dataExtractType: null,
  customDataExtractFile: null,
  dataExtractGeojson: null,

  // 05 Split Tasks
  task_split_type: null,
  task_split_dimension: 10,
  task_num_buildings: 1,
  splitGeojsonBySquares: null,
  splitGeojsonByAlgorithm: null,
};
