import { isInputEmpty } from '@/utilfunctions/commonUtils';
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
  community_type: string;
  associated_email: string;
  odk_server_type: string;
  update_odk_credentials?: boolean;
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
  community_type?: string;
  associated_email?: string;
  odk_server_type?: string;
  update_odk_credentials?: string;
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function OrganizationDetailsValidation(values: OrganisationValues) {
  const errors: ValidationErrors = {};

  if (isInputEmpty(values?.name)) {
    errors.name = 'Name is Required.';
  }

  if (isInputEmpty(values?.description)) {
    errors.description = 'Description is Required.';
  }

  if (!values?.id) {
    if (isInputEmpty(values?.url)) {
      errors.url = 'Organization Url is Required.';
    } else if (!isValidUrl(values.url)) {
      errors.url = 'Invalid URL.';
    }
    if (!values?.community_type) {
      errors.community_type = 'Community type is Required.';
    }
  }

  if (isInputEmpty(values?.associated_email)) {
    errors.associated_email = 'Email is Required.';
  } else if (!emailPattern.test(values?.associated_email)) {
    errors.associated_email = 'Invalid Email.';
  }

  if (!values?.odk_server_type && !values?.id) {
    errors.odk_server_type = 'ODK Server Type is Required.';
  }

  if (
    (values?.odk_server_type === 'OWN' || values?.update_odk_credentials) &&
    values?.odk_central_url &&
    !isValidUrl(values.odk_central_url)
  ) {
    errors.odk_central_url = 'Invalid URL.';
  }

  if ((values?.odk_server_type === 'OWN' || values?.update_odk_credentials) && isInputEmpty(values.odk_central_url)) {
    errors.odk_central_url = 'ODK Central URL is Required.';
  }

  if ((values?.odk_server_type === 'OWN' || values?.update_odk_credentials) && isInputEmpty(values.odk_central_user)) {
    errors.odk_central_user = 'ODK Central Email is Required.';
  }

  if (
    (values?.odk_server_type === 'OWN' || values?.update_odk_credentials) &&
    isInputEmpty(values.odk_central_password)
  ) {
    errors.odk_central_password = 'ODK Central Password is Required.';
  }

  return errors;
}

export default OrganizationDetailsValidation;
