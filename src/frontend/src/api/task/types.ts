import { task_event, task_state } from '@/types/enums';

// PAYLOAD TYPES
export type addNewTaskEventPayloadType = {
  event: task_event;
  user_sub: string;
};

// PARAMS TYPES
export type addNewTaskEventParamsType = {
  assignee_sub?: string;
  notify?: boolean;
  project_id: number;
  mapper?: boolean;
  team_id?: string;
};

// RESPONSE TYPES
export type addNewTaskEventResponseType = {
  event_id: string;
  task_id: number;
  event: task_event;
  user_sub: string;
  team_id: string | null;
  username: string;
  comment: string | null;
  created_at: string;
  profile_img: string | null;
  state: task_state;
};
