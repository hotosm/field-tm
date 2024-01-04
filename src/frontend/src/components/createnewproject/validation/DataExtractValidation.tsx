interface ProjectValues {
  form_ways: string;
  dataExtractWays: string;
  data_extractFile: object;
  data_extract_options: string;
  dataExtractFeatureType: string;
  customPolygonUpload: string;
  customLineUpload: string;
}
interface ValidationErrors {
  form_ways?: string;
  dataExtractWays?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  dataExtractFeatureType?: string;
  customPolygonUpload?: string;
  customLineUpload?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.dataExtractWays) {
    errors.dataExtractWays = 'Data Extract Ways is Required.';
  }

  if (values.dataExtractWays && values.dataExtractWays === 'osm_data_extract' && !values.dataExtractFeatureType) {
    errors.dataExtractFeatureType = 'OSM Feature Type is Required.';
  }
  if (
    values.dataExtractWays &&
    values.dataExtractWays === 'custom_data_extract' &&
    !values.customPolygonUpload &&
    !values.customLineUpload
  ) {
    errors.customPolygonUpload = 'A GeoJSON file is required.';
  }

  console.log(errors);
  return errors;
}

export default DataExtractValidation;
