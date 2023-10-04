interface ProjectValues {
  formCategorySelection: string;
  form_ways: string;
  dataExtractWays: string;
  data_extractFile: object;
  data_extract_options: string;
  dataExtractFeatureType: string;
}
interface ValidationErrors {
  formCategorySelection?: string;
  form_ways?: string;
  dataExtractWays?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  dataExtractFeatureType?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.formCategorySelection) {
    errors.formCategorySelection = 'Form Category is Required.';
  }
  if (!values.dataExtractWays) {
    errors.dataExtractWays = 'Select Data Extract Options.';
  }
  if (values.dataExtractWays && values.dataExtractWays === 'Upload Custom Data Extract' && !values.data_extractFile) {
    errors.data_extractFile = 'Data Extract File is Required.';
  }
  if (values.dataExtractWays && values.dataExtractWays === 'osm_data_extract' && !values.dataExtractFeatureType) {
    errors.dataExtractFeatureType = 'Data Extract Ways is Required.';
  }

  console.log(errors);
  return errors;
}

export default DataExtractValidation;
