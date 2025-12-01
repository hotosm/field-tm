import { task_event, task_state } from '@/types/enums';
import type { Polygon, MultiPolygon } from 'geojson';

// PAYLOAD TYPES
export type addNewTaskEventPayloadType = {
  event: task_event;
  user_sub?: string;
  task_id?: number;
  comment?: string;
};

// PARAMS TYPES
export type getTasksParamsType = {
  project_id: string;
};

export type getTaskActivityParamsType = {
  project_id: number;
  days?: number;
};

export type addNewTaskEventParamsType = {
  assignee_sub?: string;
  notify?: boolean;
  project_id: number;
  mapper?: boolean;
  team_id?: string;
};

export type getTaskEventHistoryParamsType = {
  days?: number;
  comments?: boolean;
  project_id: number;
};

// RESPONSE TYPES
export type taskType = {
  id: number;
  outline: Polygon | MultiPolygon;
  project_id: number;
  project_task_index: number;
  feature_count: number;
  task_state: task_state;
  actioned_by_uid: string | null;
  actioned_by_username: string | null;
};

export type taskActivityType = {
  date: string;
  mapped: number;
  validated: number;
};

export type taskEventType = {
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
