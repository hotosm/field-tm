import { z } from 'zod/v4';
import { createOrganizationValidationSchema } from '../validation/CreateEditOrganization';

export const organizationDefaultValues: z.infer<typeof createOrganizationValidationSchema> = {
  name: '',
  url: '',
  associated_email: '',
  description: '',
  odk_server_type: '',
  odk_central_url: '',
  odk_central_user: '',
  odk_central_password: '',
  community_type: '',
  logo: null,
  update_odk_credentials: false,
};
