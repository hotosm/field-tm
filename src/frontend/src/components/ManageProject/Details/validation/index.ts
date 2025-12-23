import { z } from 'zod/v4';
import { project_status, project_visibility } from '@/types/enums';

export const editProjectSchema = z.object({
  status: z.enum(project_status, { error: 'Project status must be selected' }),
  name: z.string().trim().min(1, 'Name is required'),
  description: z.string().trim().min(1, 'Description is required'),
  per_task_instructions: z.string(),
  hashtags: z.array(z.string()),
  visibility: z.enum(project_visibility, { error: 'Project Visibility must be selected' }),
});
