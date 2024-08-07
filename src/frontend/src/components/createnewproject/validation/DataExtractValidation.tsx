interface ProjectValues {
  form_ways: string;
  dataExtractWays: string;
  data_extractFile: object;
  data_extract_options: string;
  customDataExtractUpload: string;
}
interface ValidationErrors {
  form_ways?: string;
  dataExtractWays?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  customDataExtractUpload?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.dataExtractWays) {
    errors.dataExtractWays = 'Map Features Selection is Required.';
  }

  if (values.dataExtractWays && values.dataExtractWays === 'custom_data_extract' && !values.customDataExtractUpload) {
    errors.customDataExtractUpload = 'A GeoJSON file is required.';
  }

  return errors;
}

export default DataExtractValidation;
