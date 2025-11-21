import { z } from 'zod/v4';

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const inviteValidationSchema = z
  .object({
    inviteVia: z.string(),
    user: z.array(z.string()).min(1, 'User is required'),
    role: z.string().min(1, 'Role is required'),
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
  });
