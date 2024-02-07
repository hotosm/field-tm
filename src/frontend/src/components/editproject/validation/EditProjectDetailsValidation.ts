interface ProjectValues {
  organisation: string;
  name: string;
  username: string;
  id: string;
  short_description: string;
  description: string;
  // odk_central_url: string;
  // odk_central_user: string;
  // odk_central_password: string;
}
interface ValidationErrors {
  organisation?: string;
  name?: string;
  username?: string;
  id?: string;
  short_description?: string;
  description?: string;
  // odk_central_url?: string;
  // odk_central_user?: string;
  // odk_central_password?: string;
}
const regexForSymbol = /_/g;

function EditProjectValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  // if (!values?.organisation) {
  //   errors.organisation = 'Organization is Required.';
  // }
  if (!values?.name) {
    errors.name = 'Project Name is Required.';
  }
  if (values?.name && regexForSymbol.test(values.name)) {
    errors.name = 'Project Name should not contain _.';
  }
  if (!values?.short_description) {
    errors.short_description = 'Short Description is Required.';
  }
  if (!values?.description) {
    errors.description = 'Description is Required.';
  }

  return errors;
}

export default EditProjectValidation;
