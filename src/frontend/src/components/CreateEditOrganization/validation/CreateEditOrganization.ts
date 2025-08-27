import { isValidUrl } from '@/utilfunctions/urlChecker';
import { z } from 'zod/v4';

export const createOrganizationValidationSchema = z
  .object({
    id: z.number().optional(),
    name: z.string().trim().min(1, 'Name is required'),
    url: z
      .url({ protocol: /^https$/, error: 'Invalid URL' })
      .trim()
      .min(1, 'URL is required'),
    description: z.string().trim().min(1, 'Description is required'),
    associated_email: z.email('Invalid email').trim().min(1, 'Email is required'),
    odk_server_type: z.string(),
    odk_central_url: z.string().nullable(),
    odk_central_user: z.string().nullable(),
    odk_central_password: z.string().nullable(),
    community_type: z.string().trim().min(1, 'Community Type is required'),
    logo: z.any(),
    update_odk_credentials: z.boolean(),
  })
  .check((ctx) => {
    const values = ctx.value;

    if (values.odk_server_type === 'OWN' && !values.id) {
      if (!values.odk_central_url?.trim()) {
        ctx.issues.push({
          input: values.odk_central_url,
          path: ['odk_central_url'],
          message: 'ODK URL i s Required',
          code: 'custom',
        });
      } else if (!isValidUrl(values.odk_central_url)) {
        ctx.issues.push({
          input: values.odk_central_url,
          path: ['odk_central_url'],
          message: 'Invalid URL',
          code: 'custom',
        });
      }
      if (!values.odk_central_user?.trim()) {
        ctx.issues.push({
          input: values.odk_central_user,
          path: ['odk_central_user'],
          message: 'ODK Central User is Required',
          code: 'custom',
        });
      }
      if (!values.odk_central_password?.trim()) {
        ctx.issues.push({
          input: values.odk_central_password,
          path: ['odk_central_password'],
          message: 'ODK Central Password is Required',
          code: 'custom',
        });
      }
    }

    if (!values.id && values.odk_server_type?.trim()) {
      ctx.issues.push({
        input: values.odk_server_type,
        path: ['odk_server_type'],
        message: 'ODK Server Type is Required',
        code: 'custom',
      });
    }
  });
