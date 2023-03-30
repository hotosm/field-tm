
interface ProjectValues {
  name: string;
  username: string;
  id: string;
  short_description: string;
  description: string;
}
interface ValidationErrors {
  name?: string;
  username?: string;
  id?: string;
  short_description?: string;
  description?: string;
}

function CreateProjectValidation(values: ProjectValues) {
  console.log(values);
  const emailCondition = /\S+@\S+\.\S+/;
  const errors: ValidationErrors = {};

  if (!values?.name) {
    errors.name = 'Project Name is Required.';
  }

  if (!values?.username) {
    errors.username = 'Username is Required.';
  }
  if (!values?.id) {
    errors.id = 'User Id is Required.';
  }
  if (!values?.short_description) {
    errors.short_description = 'Short Description is Required.';
  }
  if (!values?.description) {
    errors.description = 'Description is Required.';
  }

  console.log(errors);
  return errors;
}

export default CreateProjectValidation;
