interface ProjectValues {
  formCategorySelection: string;
  formWays: string;
  customFormUpload: File | null;
}
interface ValidationErrors {
  formCategorySelection?: string;
  formWays?: string;
  customFormUpload?: string;
}

function SelectFormValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.formCategorySelection) {
    errors.formCategorySelection = 'Form Category is Required.';
  }
  if (!values?.formWays) {
    errors.formWays = 'Form Selection is Required.';
  }
  if (values?.formWays === 'custom_form' && !values?.customFormUpload) {
    errors.customFormUpload = 'Form needs to be Uploaded.';
  }

  console.log(errors);
  return errors;
}

export default SelectFormValidation;
