import { MapGeomTypes } from '@/types/enums';

interface ProjectValues {
  primaryGeomType: MapGeomTypes;
  useMixedGeomTypes: boolean;
  newGeomType: MapGeomTypes;
  dataExtractType: string;
  data_extractFile: object;
  data_extract_options: string;
  customDataExtractUpload: string;
}
interface ValidationErrors {
  primaryGeomType?: string;
  newGeomType?: string;
  dataExtractType?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  customDataExtractUpload?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.primaryGeomType) {
    errors.primaryGeomType = 'A primary geometry type must be selected.';
  }

  if (values?.useMixedGeomTypes && !values?.newGeomType) {
    errors.newGeomType = 'Please select a type for new geometries.';
  }

  if (!values?.dataExtractType) {
    errors.dataExtractType = 'Map Features Selection is Required.';
  }

  if (values.dataExtractType && values.dataExtractType === 'custom_data_extract' && !values.customDataExtractUpload) {
    errors.customDataExtractUpload = 'A GeoJSON file is required.';
  }

  return errors;
}

export default DataExtractValidation;
