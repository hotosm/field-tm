interface ProjectValues {
  form_ways: string;
  dataExtractWays: string;
  data_extractFile: object;
  data_extract_options: string;
  customPolygonUpload: string;
  customLineUpload: string;
}
interface ValidationErrors {
  form_ways?: string;
  dataExtractWays?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  customPolygonUpload?: string;
  customLineUpload?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.dataExtractWays) {
    errors.dataExtractWays = 'Data Extract Selection is Required.';
  }

  if (
    values.dataExtractWays &&
    values.dataExtractWays === 'custom_data_extract' &&
    !values.customPolygonUpload &&
    !values.customLineUpload
  ) {
    errors.customPolygonUpload = 'A GeoJSON file is required.';
  }

  return errors;
}

export default DataExtractValidation;
