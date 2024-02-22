import { isValidUrl } from '@/utilfunctions/urlChecker';

interface OrganisationValues {
  logo: string;
  name: string;
  description: string;
  url: string;
  type: number;
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
}
interface ValidationErrors {
  logo?: string;
  name?: string;
  description?: string;
  url?: string;
  type?: string;
  odk_central_url?: string;
  odk_central_user?: string;
  odk_central_password?: string;
}

function OrganisationAddValidation(values: OrganisationValues) {
  const errors: ValidationErrors = {};

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

  if (values?.odk_central_url && !isValidUrl(values.odk_central_url)) {
    errors.odk_central_url = 'Invalid URL.';
  }

  // if (!values?.logo) {
  //   errors.logo = 'Logo is Required.';
  // }

  return errors;
}

export default OrganisationAddValidation;
