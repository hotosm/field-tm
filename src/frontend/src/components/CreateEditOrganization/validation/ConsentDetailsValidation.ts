import { z } from 'zod/v4';

export const consentValidationSchema = z.object({
  give_consent: z
    .string()
    .min(1, 'Consent is required')
    .refine((val) => val !== 'no', 'To proceed, it is required that you provide consent'),
  review_documentation: z.array(z.string()).min(3, 'Please ensure that all checkboxes are marked'),
  participated_in: z.any(),
});
