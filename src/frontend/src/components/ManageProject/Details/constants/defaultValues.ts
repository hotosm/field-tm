import { z } from 'zod/v4';
import { editProjectSchema } from '../validation';
import { project_status, project_visibility } from '@/types/enums';

export const defaultValues: z.infer<typeof editProjectSchema> = {
  status: project_status.PUBLISHED,
  project_name: '',
  description: '',
  per_task_instructions: '',
  hashtags: [],
  visibility: project_visibility.PUBLIC,
};
