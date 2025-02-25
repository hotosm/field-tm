interface ProjectValues {
  xlsFormFileUpload: File | null;
}
interface ValidationErrors {
  xlsFormFileUpload?: any;
}

function SelectFormValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.xlsFormFileUpload) {
    errors.xlsFormFileUpload = 'Form needs to be Uploaded.';
  }

  return errors;
}

export default SelectFormValidation;
