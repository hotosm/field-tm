import z from 'zod/v4';
import { inviteValidationSchema } from '../validation/inviteValidation';

export const inviteUserDefaultValue: z.infer<typeof inviteValidationSchema> = {
  inviteVia: 'osm',
  user: [],
  role: null,
};
