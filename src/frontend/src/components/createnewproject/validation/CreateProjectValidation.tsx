import { isInputEmpty } from '@/utilfunctions/commonUtils';
import { isValidUrl } from '@/utilfunctions/urlChecker';

interface ProjectValues {
  organisation_id: string;
  name: string;
  username: string;
  id: string;
  short_description: string;
  description: string;
  hashtags: string;
  odk_central_url: string;
  odk_central_user: string;
  odk_central_password: string;
  useDefaultODKCredentials: boolean;
  hasCustomTMS: boolean;
  custom_tms_url: string;
}
interface ValidationErrors {
  organisation_id?: string;
  name?: string;
  username?: string;
  id?: string;
  short_description?: string;
  description?: string;
  hashtags?: string;
  odk_central_url?: string;
  odk_central_user?: string;
  odk_central_password?: string;
  custom_tms_url?: string;
}

const regexForSymbol = /_/g;

function CreateProjectValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.organisation_id) {
    errors.organisation_id = 'Organization is Required.';
  }
  if (!values?.useDefaultODKCredentials && isInputEmpty(values?.odk_central_url)) {
    errors.odk_central_url = 'ODK URL is Required.';
  }
  if (!values?.useDefaultODKCredentials && values?.odk_central_url && !isValidUrl(values.odk_central_url)) {
    errors.odk_central_url = 'Invalid URL.';
  }
  if (!values?.useDefaultODKCredentials && isInputEmpty(values?.odk_central_user)) {
    errors.odk_central_user = 'ODK Central User is Required.';
  }
  if (!values?.useDefaultODKCredentials && isInputEmpty(values?.odk_central_password)) {
    errors.odk_central_password = 'ODK Central Password is Required.';
  }
  if (isInputEmpty(values?.name)) {
    errors.name = 'Project Name is Required.';
  }
  if (values?.name && regexForSymbol.test(values.name)) {
    errors.name = 'Project Name should not contain _ .';
  }
  if (isInputEmpty(values?.short_description)) {
    errors.short_description = 'Short Description is Required.';
  }
  if (isInputEmpty(values?.description)) {
    errors.description = 'Description is Required.';
  }
  if (values?.hasCustomTMS && !values?.custom_tms_url) {
    errors.custom_tms_url = 'Custom TMS is Required.';
  }
  if (values?.hasCustomTMS && values?.custom_tms_url && !isValidUrl(values.custom_tms_url)) {
    errors.custom_tms_url = 'Invalid Custom TMS URL.';
  }

  return errors;
}

export default CreateProjectValidation;
