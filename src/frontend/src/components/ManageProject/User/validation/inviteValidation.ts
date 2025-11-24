import { z } from 'zod/v4';
import { project_roles } from '@/types/enums';

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const inviteValidationSchema = z
  .object({
    inviteVia: z.string(),
    user: z.array(z.string()).min(1, 'User is required'),
    role: z.union([z.enum(project_roles, { error: 'Role must be selected' }), z.null()]),
  })
  .check((ctx) => {
    const values = ctx.value;

    if (values.inviteVia === 'gmail' && values.user.some((email) => !emailPattern.test(email))) {
      ctx.issues.push({
        input: values.user,
        path: ['user'],
        message: 'Entered emails must be a Gmail account',
        code: 'custom',
      });
    }

    if (!values.role) {
      ctx.issues.push({
        input: values.role,
        path: ['role'],
        message: 'Role is required',
        code: 'custom',
      });
    }
  });
