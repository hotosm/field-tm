interface ProjectValues {
  uploadAreaSelection: string;
  dataExtractWays: string;
  data_extractFile: object;
  data_extract_options: string;
  drawnGeojson: string;
  uploadedAreaFile: string;
}
interface ValidationErrors {
  uploadAreaSelection?: string;
  dataExtractWays?: string;
  data_extractFile?: string;
  data_extract_options?: string;
  drawnGeojson?: string;
  uploadedAreaFile?: string;
}

function UploadAreaValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values.uploadAreaSelection) {
    errors.uploadAreaSelection = 'Select Upload Project Area Options';
  }
  if (values.uploadAreaSelection === 'draw' && !values.drawnGeojson) {
    errors.drawnGeojson = 'Drawing Area is Required';
  }
  if (values.uploadAreaSelection === 'upload_file' && !values.uploadedAreaFile) {
    errors.uploadedAreaFile = 'Uploaded Area File is Required';
  }

  return errors;
}

export default UploadAreaValidation;
