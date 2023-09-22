interface OrganizationValues {
  logo: string;
  name: string;
  description: string;
  url: string;
  type: number;
}
interface ValidationErrors {
  logo?: string;
  name?: string;
  description?: string;
  url?: string;
  type?: string;
}

function isValidUrl(url: string) {
  try {
    new URL(url);
    return true;
  } catch (error) {
    return false;
  }
}

function OrganizationAddValidation(values: OrganizationValues) {
  const errors: ValidationErrors = {};

  // if (!values?.logo) {
  //   errors.logo = 'Logo is Required.';
  // }
  if (!values?.name) {
    errors.name = 'Name is Required.';
  }
  if (!values?.description) {
    errors.description = 'Description is Required.';
  }
  if (!values?.url) {
    errors.url = 'Organization Url is Required.';
  } else if (!isValidUrl(values.url)) {
    errors.url = 'Invalid URL.';
  }

  return errors;
}

export default OrganizationAddValidation;
