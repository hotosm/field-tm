import { task_state as taskStateEnum } from '@/types/enums';

export interface ProjectDetailsModel {
  id: number;
  odkid: number;
  default_locale: string;
  name: string;
  short_description: string;
  description: string;
  instructions: string;
  per_task_instructions: string;
  status: number;
  xform_category: string;
  location_str: string;
  outline: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: null | number[];
  };
  tasks: {
    id: number;
    project_id: number;
    index: number;
    outline: {
      type: string;
      geometry: {
        coordinates: [string, string];
        type: string;
      };
      properties: Record<string, any>;
      id: string;
      bbox: null | number[];
    };
    task_state: taskStateEnum;
    actioned_by_uid: number;
    actioned_by_username: string;
    task_history: {
      event_id: string;
      state: string;
      comment: string;
    }[];
    qr_code_base64: string;
  }[];
}

export interface FormCategoryListModel {
  id: number;
  title: string;
}
export interface OrganisationListModel {
  name: string;
  slug: string;
  description: string;
  type: number;
  id: number;
  logo: string;
  url: string;
}

export type organizationDropdownType = {
  label: string;
  value: number;
  hasODKCredentials: boolean;
};
