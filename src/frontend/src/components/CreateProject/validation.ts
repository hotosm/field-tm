import { z } from 'zod/v4';
import { data_extract_type, field_mapping_app, project_visibility, task_split_type } from '@/types/enums';
import isEmpty from '@/utilfunctions/isEmpty';

export const projectTypeSelectorValidationSchema = z.object({
  field_mapping_app: z.union([z.enum(field_mapping_app), z.null()]).refine((val) => val !== null, {
    message: 'Field Mapping App must be selected',
  }),
});

export const projectOverviewValidationSchema = z
  .object({
    id: z.number().optional(),
    project_name: z
      .string()
      .trim()
      .min(1, 'Project Name is Required')
      .regex(/^[^_]+$/, 'Project Name should not contain _ (underscore)'),
    description: z.string().trim().min(1, 'Description is Required'),
    uploadAreaSelection: z.enum(['draw', 'upload_file']).nullable(),
    uploadedAOIFile: z.any().optional(),
    outline: z.any().refine((val) => !!val, {
      message: 'Project AOI is required',
    }),
    outlineArea: z.string().optional(),
    proceedWithLargeOutlineArea: z.boolean(),
    merge: z.boolean(),
    field_mapping_app: z.union([z.enum(field_mapping_app), z.null()]).refine((val) => val !== null, {
      message: 'Field Mapping App must be selected',
    }),
    osm_category: z.string().min(1, 'Form Category is must be selected'),
  })
  .check((ctx) => {
    const values = ctx.value;
    if (values.uploadAreaSelection === 'upload_file' && isEmpty(values.uploadedAOIFile)) {
      ctx.issues.push({
        input: values.uploadedAOIFile,
        path: ['uploadedAOIFile'],
        message: 'AOI Geojson File is Required',
        code: 'custom',
      });
    }
    if (!values.uploadAreaSelection && !values.id) {
      ctx.issues.push({
        input: values.uploadAreaSelection,
        path: ['uploadAreaSelection'],
        message: 'Upload Project Area Type must be selected',
        code: 'custom',
      });
    }
    if (
      !values.id &&
      values.outlineArea &&
      +values.outlineArea?.split(' ')?.[0] > 1000 &&
      values.outlineArea?.split(' ')[1] === 'km²'
    ) {
      ctx.issues.push({
        input: values.outlineArea,
        path: ['outlineArea'],
        message: 'The project area exceeded 1000 Sq.KM. and must be less than 1000 Sq.KM.',
        code: 'custom',
      });
    }
    if (
      !values.id &&
      values.outlineArea &&
      +values.outlineArea?.split(' ')?.[0] > 200 &&
      values.outlineArea?.split(' ')[1] === 'km²' &&
      !values.proceedWithLargeOutlineArea
    ) {
      ctx.issues.push({
        input: values.proceedWithLargeOutlineArea,
        path: ['proceedWithLargeOutlineArea'],
        message: 'Mapping area exceeds 200km²',
        code: 'custom',
      });
    }
  });

export const projectDetailsValidationSchema = z
  .object({
    visibility: z.enum(project_visibility, { error: 'Project Visibility must be selected' }),
    hashtags: z.array(z.string()),
    hasCustomTMS: z.boolean(),
    custom_tms_url: z.string().optional(),
  })
  .check((ctx) => {
    const values = ctx.value;
    if (values.hasCustomTMS && !values.custom_tms_url) {
      ctx.issues.push({
        input: values.custom_tms_url,
        path: ['custom_tms_url'],
        message: 'Custom TMS URL is Required',
        code: 'custom',
      });
    }
  });

export const uploadSurveyValidationSchema = z
  .object({
    xlsFormFile: z.any().optional(),
    needVerificationFields: z.boolean(),
    mandatoryPhotoUpload: z.boolean(),
    isFormValidAndUploaded: z.boolean(),
    advancedConfig: z.boolean(),
  })
  .check((ctx) => {
    const values = ctx.value;
    if (isEmpty(values.xlsFormFile)) {
      ctx.issues.push({
        input: values.xlsFormFile,
        path: ['xlsFormFile'],
        message: 'File is Required',
        code: 'custom',
      });
    }
  });

export const mapDataValidationSchema = z
  .object({
    dataExtractType: z
      .enum(data_extract_type)
      .nullable()
      .refine((val) => val !== null, {
        message: 'Data Extract Type must be selected',
      }),
    customDataExtractFile: z.any().optional(),
    dataExtractGeojson: z.any().optional(),
    use_st_within: z.boolean(),
  })
  .check((ctx) => {
    const values = ctx.value;
    const featureCount = values.dataExtractGeojson?.features?.length;

    if (values.dataExtractType === data_extract_type.OSM && !values.dataExtractGeojson) {
      ctx.issues.push({
        input: values.dataExtractGeojson,
        path: ['dataExtractGeojson'],
        message: 'Data extract is Required',
        code: 'custom',
      });
    }
    if (values.dataExtractType === data_extract_type.CUSTOM && isEmpty(values.customDataExtractFile)) {
      ctx.issues.push({
        input: values.customDataExtractFile,
        path: ['customDataExtractFile'],
        message: 'File is Required',
        code: 'custom',
      });
    }
    if (values.dataExtractType === data_extract_type.OSM && !isEmpty(values.customDataExtractFile)) {
      ctx.issues.push({
        input: values.customDataExtractFile,
        path: ['dataExtractGeojson'],
        message: 'Please generate OSM data extract',
        code: 'custom',
      });
    }
    if (values.dataExtractGeojson && featureCount > 30000) {
      ctx.issues.push({
        input: values.dataExtractGeojson,
        path: ['dataExtractGeojson'],
        message: `${featureCount} is a lot of features! Please consider breaking this into smaller projects`,
        code: 'custom',
      });
    }
  });

export const splitTasksValidationSchema = z
  .object({
    task_split_type: z
      .enum(task_split_type)
      .nullable()
      .refine((val) => val !== null, {
        message: 'Task Split Type is Required',
      }),
    task_split_dimension: z.number().optional(),
    task_num_buildings: z.number().optional(),
    splitGeojsonBySquares: z.any().optional(),
    splitGeojsonByAlgorithm: z.any().optional(),
    dividedTaskGeojson: z.any().optional(),
  })
  .check((ctx) => {
    const values = ctx.value;

    if (
      values.task_split_type === task_split_type.DIVIDE_ON_SQUARE &&
      values.task_split_dimension !== undefined &&
      values.task_split_dimension < 10
    ) {
      ctx.issues.push({
        minimum: 10,
        message: 'Dimension must be at least 10',
        input: values.task_split_dimension,
        code: 'custom',
        path: ['task_split_dimension'],
      });
    }
    if (
      values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM &&
      values.task_num_buildings !== undefined &&
      values.task_num_buildings < 1
    ) {
      ctx.issues.push({
        minimum: 1,
        message: 'Average buildings per task must be greater than 0',
        input: values.task_num_buildings,
        code: 'custom',
        path: ['task_num_buildings'],
      });
    }
    if (values.task_split_type === task_split_type.DIVIDE_ON_SQUARE && !values.splitGeojsonBySquares) {
      ctx.issues.push({
        message: 'Please generate the task using Divide into squares',
        input: values.splitGeojsonBySquares,
        code: 'custom',
        path: ['splitGeojsonBySquares'],
      });
    }
    if (values.task_split_type === task_split_type.TASK_SPLITTING_ALGORITHM && !values.splitGeojsonByAlgorithm) {
      ctx.issues.push({
        message: 'Please generate the task using Task Splitting Algorithm',
        input: values.splitGeojsonByAlgorithm,
        code: 'custom',
        path: ['splitGeojsonByAlgorithm'],
      });
    }
  });

export const assignProjectManagerValidationSchema = z
  .object({
    has_external_mappingapp_account: z.boolean(),
    external_project_username: z.string().trim().min(1, 'Username/Email is Required'),
    external_project_password: z.string().optional(),
    external_project_password_confirm: z.string().optional(),
  })
  .check((ctx) => {
    const values = ctx.value;

    if (!values.has_external_mappingapp_account) {
      if (!values.external_project_password?.trim()) {
        ctx.issues.push({
          input: values.external_project_password,
          path: ['external_project_password'],
          message: 'Password is Required',
          code: 'custom',
        });
      }
      if (!values.external_project_password_confirm?.trim()) {
        ctx.issues.push({
          input: values.external_project_password_confirm,
          path: ['external_project_password_confirm'],
          message: 'Confirmation Password is Required',
          code: 'custom',
        });
      }

      if (
        values.external_project_password &&
        values.external_project_password_confirm &&
        values.external_project_password !== values.external_project_password_confirm
      ) {
        ctx.issues.push({
          message: 'Passwords do not match',
          input: values.external_project_password_confirm,
          code: 'custom',
          path: ['external_project_password_confirm'],
        });
      }
    }
  });

export const createProjectValidationSchema = z.object({
  ...projectTypeSelectorValidationSchema.shape,
  ...projectOverviewValidationSchema.shape,
  ...projectDetailsValidationSchema.shape,
  ...uploadSurveyValidationSchema.shape,
  ...mapDataValidationSchema.shape,
  ...splitTasksValidationSchema.shape,
  ...assignProjectManagerValidationSchema.shape,
});
