import { project_roles, user_roles } from '@/types/enums';

// PAYLOAD TYPES
export type inviteNewUserPayloadType = {
  project_id: number;
  role: project_roles;
  osm_username?: string;
  email?: string;
};

export type updateExistingUserPayloadType = {
  username?: string;
  role?: user_roles;
  profile_img?: string;
  name?: string;
  city?: string;
  country?: string;
  email_address?: string;
  is_expert?: boolean;
  mapping_level?: string;
  project_roles?: Record<string, project_roles>;
  orgs_managed?: number[];
};

// PARAMS TYPES
export type getUsersParamsType = {
  page: number;
  results_per_page?: number;
  search?: string;
  signin_type?: 'osm' | 'google';
};

export type getUserListParamsType = {
  search: string;
  signin_type?: 'osm' | 'google';
};

export type getProjectUserInvitesParamsType = {
  project_id: number;
};

export type inviteNewUserParamsType = {
  project_id: number;
  mapper?: boolean;
};

export type getUserByIdParamsType = {
  sub: string;
};

export type deleteUserByIdParamsType = {
  sub: string;
};

// RESPONSE TYPES
export type getUserListType = {
  sub: string;
  username: string;
};

export type userType = {
  sub: string;
  username: string;
  role: user_roles;
  profile_img: string | null;
  name: string;
  city: string | null;
  country: string | null;
  email_address: string;
  is_email_verified: boolean;
  is_expert: boolean;
  mapping_level: string;
  tasks_mapped: number;
  tasks_validated: number;
  tasks_invalidated: number;
  projects_mapped: number[] | null;
  api_key: string | null;
  registered_at: string;
  last_login_at: string;
  project_roles: Record<string, project_roles> | null;
  orgs_managed: number[] | null;
};

export type projectUserInvite = {
  token: string;
  project_id: number;
  osm_username: string;
  email: string | null;
  role: project_roles;
  expires_at: string;
  used_at: string;
  created_at: string;
};
