import { z } from 'zod/v4';
import { consentValidationSchema } from '../validation/ConsentDetailsValidation';

export const consentDefaultValues: z.infer<typeof consentValidationSchema> = {
  give_consent: '',
  review_documentation: [],
  participated_in: [],
};
