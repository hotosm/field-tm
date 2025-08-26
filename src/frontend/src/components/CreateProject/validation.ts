import { z } from 'zod/v4';
import { isValidUrl } from '@/utilfunctions/urlChecker';
import { data_extract_type, GeoGeomTypesEnum, project_visibility, task_split_type } from '@/types/enums';

const validateODKCreds = (ctx: any, values: Record<string, any>) => {
  if (!values.odk_central_url?.trim()) {
    ctx.issues.push({
      input: values.odk_central_url,
      path: ['odk_central_url'],
      message: 'ODK URL is Required',
      code: 'custom',
    });
  } else if (!isValidUrl(values.odk_central_url)) {
    ctx.issues.push({
      input: values.odk_central_url,
      path: ['odk_central_url'],
      message: 'Invalid URL',
      code: 'custom',
    });
  }
  if (!values.odk_central_user?.trim()) {
    ctx.issues.push({
      input: values.odk_central_user,
      path: ['odk_central_user'],
      message: 'ODK Central User is Required',
      code: 'custom',
    });
  }
  if (!values.odk_central_password?.trim()) {
    ctx.issues.push({
      input: values.odk_central_password,
      path: ['odk_central_password'],
      message: 'ODK Central Password is Required',
      code: 'custom',
    });
  }
};

export const odkCredentialsValidationSchema = z
  .object({
    odk_central_url: z.string(),
    odk_central_user: z.string().optional(),
    odk_central_password: z.string().optional(),
  })
  .check((ctx) => {
    const values = ctx.value;
    validateODKCreds(ctx, values);
  });

export const projectOverviewValidationSchema = z
  .object({
    id: z.number().optional(),
    name: z
      .string()
      .trim()
      .min(1, 'Project Name is Required')
      .regex(/^[^_]+$/, 'Project Name should not contain _ (underscore)'),
    short_description: z.string().trim().min(1, 'Short Description is Required'),
    description: z.string().trim().min(1, 'Description is Required'),
    organisation_id: z
      .number()
      .nullable()
      .refine((val) => val !== null, {
        message: 'Organization is Required',
      }),
    hasODKCredentials: z.boolean(),
    useDefaultODKCredentials: z.boolean(),
    odk_central_url: z.string().optional(),
    odk_central_user: z.string().optional(),
    odk_central_password: z.string().optional(),
    project_admins: z.array(z.string()),
    uploadAreaSelection: z.enum(['draw', 'upload_file']).nullable(),
    uploadedAOIFile: z.any().optional(),
    outline: z.any().refine((val) => !!val, {
      message: 'Project AOI is required',
    }),
    outlineArea: z.string().optional(),
    organisation_name: z.string(),
    merge: z.boolean(),
  })
  .check((ctx) => {
    const values = ctx.value;
    if (values.hasODKCredentials && !values.useDefaultODKCredentials) {
      validateODKCreds(ctx, values);
    }
    if (values.uploadAreaSelection === 'upload_file' && !values.uploadedAOIFile) {
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
      +values.outlineArea?.split(' ')?.[0] > 10000 &&
      values.outlineArea?.split(' ')[1] === 'km²'
    ) {
      ctx.issues.push({
        input: values.outlineArea,
        path: ['outlineArea'],
        message: 'The project area exceeded 10000 Sq.KM. and must be less than 10000 Sq.KM.',
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
    per_task_instructions: z.string(),
    use_odk_collect: z.boolean(),
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
    osm_category: z.string().min(1, 'Form Category is must be selected'),
    xlsFormFile: z.any().optional(),
    isXlsFormFileValid: z.boolean(),
    needVerificationFields: z.boolean(),
  })
  .check((ctx) => {
    const values = ctx.value;
    if (!values.xlsFormFile) {
      ctx.issues.push({
        input: values.xlsFormFile,
        path: ['xlsFormFile'],
        message: 'File is Required',
        code: 'custom',
      });
    }
    if (values.xlsFormFile && !values.isXlsFormFileValid) {
      ctx.issues.push({
        input: values.xlsFormFile,
        path: ['xlsFormFile'],
        message: 'File is Invalid',
        code: 'custom',
      });
    }
  });

export const mapDataValidationSchema = z
  .object({
    primary_geom_type: z
      .enum(GeoGeomTypesEnum)
      .nullable()
      .refine((val) => val !== null, {
        message: 'Primary Geometry Type must be selected',
      }),
    includeCentroid: z.boolean(),
    useMixedGeomTypes: z.boolean(),
    new_geom_type: z.union([z.enum(GeoGeomTypesEnum), z.null()]).optional(),
    dataExtractType: z
      .enum(data_extract_type)
      .nullable()
      .refine((val) => val !== null, {
        message: 'Data Extract Type must be selected',
      }),
    customDataExtractFile: z.any().optional(),
    dataExtractGeojson: z.any().optional(),
  })
  .check((ctx) => {
    const values = ctx.value;
    const featureCount = values.dataExtractGeojson?.features?.length;

    if (values.useMixedGeomTypes && !values.new_geom_type) {
      ctx.issues.push({
        input: values.new_geom_type,
        path: ['new_geom_type'],
        message: 'New Geometry Type must be selected',
        code: 'custom',
      });
    }
    if (values.dataExtractType === data_extract_type.OSM && !values.dataExtractGeojson) {
      ctx.issues.push({
        input: values.dataExtractGeojson,
        path: ['dataExtractGeojson'],
        message: 'Data extract is Required',
        code: 'custom',
      });
    }
    if (values.dataExtractType === data_extract_type.CUSTOM && !values.customDataExtractFile) {
      ctx.issues.push({
        input: values.customDataExtractFile,
        path: ['customDataExtractFile'],
        message: 'File is Required',
        code: 'custom',
      });
    }
    if (
      values.dataExtractGeojson?.id &&
      values.primary_geom_type !== values.dataExtractGeojson?.id &&
      !values.customDataExtractFile
    ) {
      ctx.issues.push({
        input: values.dataExtractGeojson,
        path: ['dataExtractGeojson'],
        message: `Please generate data extract for ${values.primary_geom_type?.toLowerCase()}`,
        code: 'custom',
      });
    }
    if (values.dataExtractType === data_extract_type.OSM && values.customDataExtractFile) {
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

export const createProjectValidationSchema = z.object({
  ...projectOverviewValidationSchema.shape,
  ...projectDetailsValidationSchema.shape,
  ...uploadSurveyValidationSchema.shape,
  ...mapDataValidationSchema.shape,
  ...splitTasksValidationSchema.shape,
});
