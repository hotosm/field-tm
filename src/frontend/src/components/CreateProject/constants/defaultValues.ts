import { z } from 'zod/v4';
import { createProjectValidationSchema } from '../validation';
import { project_visibility } from '@/types/enums';

export const defaultValues: z.infer<typeof createProjectValidationSchema> = {
  // 00 Project Type Selector
  field_mapping_app: null,

  // 01 Project Overview
  project_name: '',
  description: '',
  uploadAreaSelection: null,
  uploadedAOIFile: [],
  outline: undefined,
  outlineArea: undefined,
  proceedWithLargeOutlineArea: false,
  merge: true,
  osm_category: '',

  // 02 Project Details
  visibility: project_visibility.PUBLIC,
  hashtags: [],
  hasCustomTMS: false,
  custom_tms_url: '',

  // 03 Upload Survey
  xlsFormFile: [],
  needVerificationFields: true,
  mandatoryPhotoUpload: false,
  isFormValidAndUploaded: false,
  advancedConfig: false,

  // 04 Map Data
  dataExtractType: null,
  customDataExtractFile: [],
  dataExtractGeojson: null,
  use_st_within: false,

  // 05 Split Tasks
  task_split_type: null,
  task_split_dimension: 10,
  task_num_buildings: 1,
  splitGeojsonBySquares: null,
  splitGeojsonByAlgorithm: null,
};
