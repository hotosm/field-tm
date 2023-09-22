interface ProjectValues {
  xform_title: string;
  form_ways: string;
}
interface ValidationErrors {
  xform_title?: string;
  form_ways?: string;
}

function SelectFormValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.xform_title) {
    errors.xform_title = 'Form Category is Required.';
  }
  if (!values?.form_ways) {
    errors.form_ways = 'Form Selection is Required.';
  }

  console.log(errors);
  return errors;
}

export default SelectFormValidation;
