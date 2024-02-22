import { isValidUrl } from '@/utilfunctions/urlChecker';

interface OrganisationValues {
  id: string;
  logo: string;
  name: string;
  description: string;
  url: string;
  type: number;
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
  osm_profile: string;
  organization_type: string;
  fillODKCredentials: boolean;
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
  osm_profile?: string;
  organization_type?: string;
  fillODKCredentials?: boolean;
}

function OrganizationDetailsValidation(values: OrganisationValues) {
  const errors: ValidationErrors = {};

  if (!values?.name) {
    errors.name = 'Name is Required.';
  }

  if (!values?.description) {
    errors.description = 'Description is Required.';
  }

  if (!values?.id) {
    if (!values?.url) {
      errors.url = 'Organization Url is Required.';
    } else if (!isValidUrl(values.url)) {
      errors.url = 'Invalid URL.';
    }
    if (!values?.organization_type) {
      errors.organization_type = 'Organization type is Required.';
    }
  }

  if (values?.odk_central_url && !isValidUrl(values.odk_central_url)) {
    errors.odk_central_url = 'Invalid URL.';
  }

  if (values?.fillODKCredentials && !values.odk_central_url) {
    errors.odk_central_url = 'ODK central URL is Required.';
  }

  if (values?.fillODKCredentials && !values.odk_central_user) {
    errors.odk_central_user = 'ODK central URL is Required.';
  }

  if (values?.fillODKCredentials && !values.odk_central_password) {
    errors.odk_central_password = 'ODK central URL is Required.';
  }

  return errors;
}

export default OrganizationDetailsValidation;
