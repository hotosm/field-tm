interface ProjectValues {
  form_ways: string;
  dataExtractWays: string;
  data_extractFile: object;
  data_extract_options: string;
  customDataExtractUpload: string;
  hasAdditionalFeature: boolean;
  additionalFeature: File;
}
interface ValidationErrors {
  form_ways?: string;
  dataExtractWays?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  customDataExtractUpload?: string;
  additionalFeature?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.dataExtractWays) {
    errors.dataExtractWays = 'Map Features Selection is Required.';
  }

  if (values.dataExtractWays && values.dataExtractWays === 'custom_data_extract' && !values.customDataExtractUpload) {
    errors.customDataExtractUpload = 'A GeoJSON file is required.';
  }

  if (values.hasAdditionalFeature && !values.additionalFeature) {
    errors.additionalFeature = 'Additional Feature is Required.';
  }

  return errors;
}

export default DataExtractValidation;
